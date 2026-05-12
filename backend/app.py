"""FastAPI app wiring up orchestrator, specialist agents, and frontend API."""

import logging
import os
from contextlib import asynccontextmanager
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from pydantic import BaseModel

from backend.agents import booking as booking_agent
from backend.agents import weather as weather_agent
from backend.agents.orchestrator import TravelOrchestrator

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s | %(message)s")
log = logging.getLogger("travel-agent")


orchestrator = TravelOrchestrator()


@asynccontextmanager
async def lifespan(app: FastAPI):
    base = os.getenv("BACKEND_BASE_URL", "http://localhost:8000")
    log.info("Configuring orchestrator, base_url=%s", base)
    orchestrator.configure(base)
    params = StdioServerParameters(
        command="python", args=["-m", "backend.mcp_server"], env=os.environ.copy()
    )
    # Own both contexts inside the same task so the anyio cancel-scope
    # exits in the task that entered it.
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            orchestrator.attach_mcp(session)
            log.info("MCP session connected — orchestrator ready.")
            try:
                yield
            finally:
                orchestrator.detach_mcp()
                log.info("Shutting down MCP session.")


app = FastAPI(title="Travel Booking Multi-Agent System", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Mount specialist agents under their own URL prefixes — each prefix is an
# independently-discoverable A2A endpoint.
app.include_router(weather_agent.router, prefix="/agents/weather", tags=["weather-agent"])
app.include_router(booking_agent.router, prefix="/agents/booking", tags=["booking-agent"])


class ChatRequest(BaseModel):
    message: str
    history: list[dict[str, Any]] = []


class ChatResponse(BaseModel):
    reply: str
    history: list[dict[str, Any]]
    tool_trace: list[dict[str, Any]]


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    history = list(req.history) + [{"role": "user", "content": req.message}]
    try:
        result = await orchestrator.chat(history)
    except Exception as exc:  # noqa: BLE001 — surface to UI
        log.exception("Orchestrator chat failed")
        raise HTTPException(500, f"Orchestrator failed: {exc}") from exc
    return ChatResponse(**result)


@app.get("/api/bookings")
async def list_bookings() -> dict[str, Any]:
    return {"bookings": booking_agent.all_bookings()}


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
