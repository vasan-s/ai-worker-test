"""Travel orchestrator agent.

Uses the OpenAI Chat Completions API with tool calling. Tools are routed to:
  * MCP server (stdio subprocess) for place catalog lookups
  * Weather agent via A2A
  * Booking agent via A2A

This is the only component that talks to the LLM. The specialist agents are
pure executors reached over A2A.
"""

from __future__ import annotations

import json
import os
from typing import Any

from mcp import ClientSession
from openai import AsyncOpenAI

from backend.a2a import A2AClient

SYSTEM_PROMPT = """You are TravelMate, a friendly AI travel concierge.

You help users plan and book trips. You have three categories of tools:

1. Knowledge base (via MCP): list_destinations, get_place_details — for
   destination info, attractions, currency, best seasons.
2. Weather (via A2A WeatherAgent): get_weather — forecast for a city/date.
3. Booking (via A2A BookingAgent): create_booking — to reserve a trip.

Rules:
- When the user expresses interest in a destination, look it up to share concrete
  facts (top attractions, season, avg hotel price). Do not invent details.
- Before calling create_booking, ALWAYS show the user a summary
  (city, date, traveler name, number of travelers, nights, estimated cost) and
  ask them to confirm with "yes" / "confirm". Never book without explicit confirmation.
- If the user has not given you a travel date, ask for one before checking weather.
- Use ISO dates (YYYY-MM-DD).
- Keep responses concise and warm. Use short paragraphs and the occasional bullet.
"""


TOOLS_SCHEMA: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "list_destinations",
            "description": "List all destinations available in the knowledge base.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_place_details",
            "description": "Get info (attractions, season, currency) for a destination.",
            "parameters": {
                "type": "object",
                "properties": {"city": {"type": "string"}},
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the weather forecast for a city on a specific ISO date (YYYY-MM-DD).",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string"},
                    "travel_date": {"type": "string", "description": "ISO date YYYY-MM-DD"},
                },
                "required": ["city", "travel_date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_booking",
            "description": (
                "Create a confirmed travel booking. ONLY call this after the user has "
                "explicitly confirmed the trip details in their last message."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string"},
                    "travel_date": {"type": "string"},
                    "traveler_name": {"type": "string"},
                    "num_travelers": {"type": "integer", "minimum": 1},
                    "nights": {"type": "integer", "minimum": 1},
                },
                "required": ["city", "travel_date", "traveler_name", "num_travelers", "nights"],
            },
        },
    },
]


class TravelOrchestrator:
    """Holds the MCP session, A2A clients, and OpenAI client for the lifetime of the app."""

    def __init__(self) -> None:
        self._mcp: ClientSession | None = None
        self._openai: AsyncOpenAI | None = None
        self._weather: A2AClient | None = None
        self._booking: A2AClient | None = None
        self._model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def configure(self, base_url: str) -> None:
        """Configure non-async dependencies. Called from lifespan."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY environment variable is required.")
        self._openai = AsyncOpenAI(api_key=api_key)
        # A2A clients are lazy — discovery happens on first chat request.
        self._weather = A2AClient(f"{base_url}/agents/weather")
        self._booking = A2AClient(f"{base_url}/agents/booking")

    def attach_mcp(self, session: ClientSession) -> None:
        self._mcp = session

    def detach_mcp(self) -> None:
        self._mcp = None

    async def _call_tool(self, name: str, args: dict[str, Any]) -> dict[str, Any]:
        if name in ("list_destinations", "get_place_details"):
            assert self._mcp is not None
            mcp_args = args if name != "list_destinations" else {}
            result = await self._mcp.call_tool(name, mcp_args)
            return _mcp_to_dict(result)
        if name == "get_weather":
            assert self._weather is not None
            res = await self._weather.send_task("get_forecast", args)
            return res.model_dump()
        if name == "create_booking":
            assert self._booking is not None
            res = await self._booking.send_task("create_booking", args)
            return res.model_dump()
        return {"error": f"Unknown tool {name}"}

    async def chat(self, history: list[dict[str, Any]]) -> dict[str, Any]:
        """Run the OpenAI tool-calling loop. Returns updated history + final reply."""
        assert self._openai is not None
        messages: list[dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}] + history
        tool_trace: list[dict[str, Any]] = []

        for _ in range(8):  # safety cap on tool-calling iterations
            completion = await self._openai.chat.completions.create(
                model=self._model,
                messages=messages,
                tools=TOOLS_SCHEMA,
                tool_choice="auto",
                temperature=0.4,
            )
            msg = completion.choices[0].message
            messages.append(_msg_to_dict(msg))

            if not msg.tool_calls:
                return {
                    "reply": msg.content or "",
                    "history": messages[1:],  # drop system prompt
                    "tool_trace": tool_trace,
                }

            for tc in msg.tool_calls:
                args = _safe_json(tc.function.arguments)
                result = await self._call_tool(tc.function.name, args)
                tool_trace.append({"tool": tc.function.name, "args": args, "result": result})
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "name": tc.function.name,
                        "content": json.dumps(result),
                    }
                )

        return {
            "reply": "I'm having trouble finishing that request — too many tool steps.",
            "history": messages[1:],
            "tool_trace": tool_trace,
        }


def _safe_json(s: str | None) -> dict[str, Any]:
    if not s:
        return {}
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        return {}


def _msg_to_dict(msg: Any) -> dict[str, Any]:
    out: dict[str, Any] = {"role": "assistant", "content": msg.content}
    if msg.tool_calls:
        out["tool_calls"] = [
            {
                "id": tc.id,
                "type": "function",
                "function": {"name": tc.function.name, "arguments": tc.function.arguments},
            }
            for tc in msg.tool_calls
        ]
    return out


def _mcp_to_dict(result: Any) -> dict[str, Any]:
    """Unwrap an MCP CallToolResult into a plain dict for the LLM."""
    if getattr(result, "isError", False):
        return {"error": "MCP tool returned an error", "content": _content_payload(result)}
    return {"data": _content_payload(result)}


def _content_payload(result: Any) -> Any:
    # Prefer structuredContent if the server provided it.
    structured = getattr(result, "structuredContent", None)
    if structured is not None:
        return structured

    content = getattr(result, "content", None) or []
    parsed: list[Any] = []
    for chunk in content:
        text = getattr(chunk, "text", None)
        if text is None:
            continue
        try:
            parsed.append(json.loads(text))
        except (json.JSONDecodeError, TypeError):
            parsed.append(text)
    if not parsed:
        return None
    if len(parsed) == 1:
        return parsed[0]
    return parsed
