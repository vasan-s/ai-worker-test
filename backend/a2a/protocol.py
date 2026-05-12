"""A2A message types and HTTP client."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

import httpx
from pydantic import BaseModel, Field


class AgentSkill(BaseModel):
    id: str
    name: str
    description: str
    input_schema: dict[str, Any]


class AgentCard(BaseModel):
    """Public description of an agent — served at /.well-known/agent.json."""

    name: str
    description: str
    version: str = "1.0.0"
    url: str
    skills: list[AgentSkill]


class Task(BaseModel):
    """A request from one agent to another."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    skill_id: str
    inputs: dict[str, Any]
    requester: str = "orchestrator"


class TaskResult(BaseModel):
    """Response from a peer agent."""

    id: str
    status: str  # "completed" | "failed"
    output: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None


class A2AClient:
    """Discover an A2A agent and send Tasks to it."""

    def __init__(self, base_url: str, timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._card: AgentCard | None = None

    async def discover(self) -> AgentCard:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            r = await client.get(f"{self.base_url}/.well-known/agent.json")
            r.raise_for_status()
            self._card = AgentCard(**r.json())
            return self._card

    async def send_task(self, skill_id: str, inputs: dict[str, Any]) -> TaskResult:
        task = Task(skill_id=skill_id, inputs=inputs)
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            r = await client.post(f"{self.base_url}/a2a/task", json=task.model_dump())
            r.raise_for_status()
            return TaskResult(**r.json())
