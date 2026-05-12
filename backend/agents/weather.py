"""Weather specialist agent. Exposes A2A endpoints to look up forecasts."""

from fastapi import APIRouter, HTTPException

from backend.a2a import AgentCard, AgentSkill, Task, TaskResult
from backend.knowledge_base import get_forecast

router = APIRouter()

_AGENT_CARD = AgentCard(
    name="WeatherAgent",
    description="Provides weather forecasts for destinations in the knowledge base.",
    url="http://localhost:8000/agents/weather",
    skills=[
        AgentSkill(
            id="get_forecast",
            name="Get Weather Forecast",
            description="Return high/low temperature and conditions for a city on a date.",
            input_schema={
                "type": "object",
                "properties": {
                    "city": {"type": "string"},
                    "travel_date": {"type": "string", "format": "date"},
                },
                "required": ["city", "travel_date"],
            },
        )
    ],
)


@router.get("/.well-known/agent.json")
async def weather_agent_card() -> dict:
    return _AGENT_CARD.model_dump()


@router.post("/a2a/task")
async def weather_handle_task(task: Task) -> TaskResult:
    if task.skill_id != "get_forecast":
        raise HTTPException(400, f"Unknown skill: {task.skill_id}")
    city = task.inputs.get("city")
    travel_date = task.inputs.get("travel_date")
    if not city or not travel_date:
        return TaskResult(id=task.id, status="failed", error="city and travel_date required")
    forecast = get_forecast(city, travel_date)
    if forecast is None:
        return TaskResult(
            id=task.id,
            status="failed",
            error=f"No forecast available for {city} on {travel_date}",
        )
    return TaskResult(id=task.id, status="completed", output=forecast)
