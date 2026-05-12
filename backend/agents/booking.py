"""Booking specialist agent. Exposes A2A endpoints to create bookings."""

from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from backend.a2a import AgentCard, AgentSkill, Task, TaskResult
from backend.knowledge_base import get_place

router = APIRouter()

# In-memory booking store
_BOOKINGS: dict[str, dict] = {}


_AGENT_CARD = AgentCard(
    name="BookingAgent",
    description="Creates and looks up travel bookings in the in-memory reservation system.",
    url="http://localhost:8000/agents/booking",
    skills=[
        AgentSkill(
            id="create_booking",
            name="Create Travel Booking",
            description="Reserve a trip for a traveler. Returns a booking confirmation.",
            input_schema={
                "type": "object",
                "properties": {
                    "city": {"type": "string"},
                    "travel_date": {"type": "string", "format": "date"},
                    "traveler_name": {"type": "string"},
                    "num_travelers": {"type": "integer", "minimum": 1},
                    "nights": {"type": "integer", "minimum": 1},
                },
                "required": ["city", "travel_date", "traveler_name", "num_travelers", "nights"],
            },
        ),
        AgentSkill(
            id="get_booking",
            name="Get Booking",
            description="Look up a booking by confirmation code.",
            input_schema={
                "type": "object",
                "properties": {"confirmation_code": {"type": "string"}},
                "required": ["confirmation_code"],
            },
        ),
    ],
)


@router.get("/.well-known/agent.json")
async def booking_agent_card() -> dict:
    return _AGENT_CARD.model_dump()


@router.post("/a2a/task")
async def booking_handle_task(task: Task) -> TaskResult:
    if task.skill_id == "create_booking":
        return _create_booking(task)
    if task.skill_id == "get_booking":
        return _get_booking(task)
    raise HTTPException(400, f"Unknown skill: {task.skill_id}")


def _create_booking(task: Task) -> TaskResult:
    required = ("city", "travel_date", "traveler_name", "num_travelers", "nights")
    missing = [k for k in required if task.inputs.get(k) in (None, "")]
    if missing:
        return TaskResult(id=task.id, status="failed", error=f"Missing fields: {missing}")

    place = get_place(task.inputs["city"])
    if place is None:
        return TaskResult(id=task.id, status="failed", error=f"Unknown destination: {task.inputs['city']}")

    nights = int(task.inputs["nights"])
    num = int(task.inputs["num_travelers"])
    price = place["avg_hotel_price_usd"] * nights * num
    code = f"TRV-{uuid4().hex[:8].upper()}"
    record = {
        "confirmation_code": code,
        "city": place["city"],
        "country": place["country"],
        "travel_date": task.inputs["travel_date"],
        "nights": nights,
        "traveler_name": task.inputs["traveler_name"],
        "num_travelers": num,
        "total_price_usd": price,
        "currency_at_destination": place["currency"],
        "booked_at_utc": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "status": "CONFIRMED",
    }
    _BOOKINGS[code] = record
    return TaskResult(id=task.id, status="completed", output=record)


def _get_booking(task: Task) -> TaskResult:
    code = task.inputs.get("confirmation_code")
    if not code:
        return TaskResult(id=task.id, status="failed", error="confirmation_code required")
    record = _BOOKINGS.get(code)
    if record is None:
        return TaskResult(id=task.id, status="failed", error=f"No booking with code {code}")
    return TaskResult(id=task.id, status="completed", output=record)


def all_bookings() -> list[dict]:
    return list(_BOOKINGS.values())
