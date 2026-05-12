# TravelMate — Multi-Agent Travel Booking System

A small but complete demonstration of three modern agent patterns working together:

- **OpenAI tool-calling** in an orchestrator that drives the conversation
- **MCP (Model Context Protocol)** server providing the hardcoded travel knowledge base as callable tools
- **A2A (Agent-to-Agent)** protocol with specialist agents (Weather + Booking) discovered via `/.well-known/agent.json` cards and invoked over HTTP

Plus a React + Vite single-screen chat frontend.

## Architecture

```
┌────────────────────┐        ┌────────────────────────────────────────┐
│  React Frontend    │  /api  │  FastAPI app                           │
│  (Vite, port 5173) │ ─────▶ │   ┌──────────────────────────────────┐ │
└────────────────────┘        │   │ Orchestrator Agent (OpenAI brain)│ │
                              │   └──────────────────────────────────┘ │
                              │       │ MCP (stdio)         │ A2A      │
                              │       ▼                     ▼          │
                              │  ┌──────────────┐  ┌────────────────┐  │
                              │  │ MCP server   │  │ WeatherAgent   │  │
                              │  │ (knowledge   │  │ /agents/weather│  │
                              │  │  base tools) │  └────────────────┘  │
                              │  └──────────────┘  ┌────────────────┐  │
                              │                    │ BookingAgent   │  │
                              │                    │ /agents/booking│  │
                              │                    └────────────────┘  │
                              └────────────────────────────────────────┘
```

The orchestrator is the only component that talks to the LLM. It calls:
- the **MCP server** (stdio subprocess) for destination lookups, and
- the **specialist agents** over A2A for weather and booking.

Each specialist agent serves an A2A AgentCard at `/.well-known/agent.json` and accepts JSON Tasks at `/a2a/task`.

## Layout

```
backend/
  app.py                FastAPI: mounts agents + /api/chat
  knowledge_base.py     Hardcoded places + weather profiles
  mcp_server.py         MCP server (stdio, FastMCP)
  a2a/protocol.py       AgentCard, Task, TaskResult, A2AClient
  agents/
    orchestrator.py     OpenAI loop, MCP client, A2A clients
    weather.py          A2A agent: get_forecast
    booking.py          A2A agent: create_booking, get_booking
frontend/
  src/App.jsx           Single-screen chat + bookings sidebar
start.sh                One-command boot
```

## Setup

1. **Set your OpenAI key**

   ```bash
   cp backend/.env.example backend/.env
   # edit backend/.env and set OPENAI_API_KEY
   ```

2. **Run everything**

   ```bash
   ./start.sh
   ```

   This will:
   - create a Python venv and install `backend/requirements.txt`
   - install frontend node modules
   - start the FastAPI backend on `http://localhost:8000`
   - start the Vite dev server on `http://localhost:5173`

   Open <http://localhost:5173>.

## Manual run (if you prefer)

```bash
# backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt
PYTHONPATH=. uvicorn backend.app:app --reload --port 8000

# frontend (in another terminal)
cd frontend && npm install && npm run dev
```

## Try it

The knowledge base ships with Tokyo, Paris, Bali, New York, Dubai, and Reykjavik.

Example prompts:
- *"What destinations do you have?"* — exercises MCP `list_destinations`
- *"Tell me about Paris and check the weather on 2026-09-22"* — MCP + A2A WeatherAgent
- *"Book 4 nights in Bali starting 2026-07-10 for 2 travelers, name Priya Shah"* — the orchestrator will summarize and ask you to confirm; reply *"yes"* to trigger A2A BookingAgent

The Agent activity dropdown under each assistant message shows which tools (MCP / A2A) fired.

## Endpoints

- `POST /api/chat` — main chat endpoint used by the frontend
- `GET /api/bookings` — list in-memory bookings
- `GET /agents/weather/.well-known/agent.json` — A2A discovery for WeatherAgent
- `POST /agents/weather/a2a/task` — A2A task endpoint
- `GET /agents/booking/.well-known/agent.json` — A2A discovery for BookingAgent
- `POST /agents/booking/a2a/task` — A2A task endpoint
