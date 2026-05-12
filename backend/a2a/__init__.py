"""Lightweight Agent-to-Agent (A2A) protocol implementation.

Inspired by the public A2A spec: every agent exposes a discovery endpoint
(``/.well-known/agent.json``) returning an AgentCard, and a ``/a2a/task``
endpoint that accepts a structured Task and returns a structured Result.
"""

from .protocol import AgentCard, A2AClient, Task, TaskResult, AgentSkill

__all__ = ["AgentCard", "AgentSkill", "A2AClient", "Task", "TaskResult"]
