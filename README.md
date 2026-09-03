# 🤖 Autonomous Multi-Agent AI Orchestration System

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2.60+-2b5b84.svg)](https://langchain-ai.github.io/langgraph/)
[![Celery](https://img.shields.io/badge/Celery-5.4+-37814A.svg?logo=celery&logoColor=white)](https://docs.celeryq.dev/)
[![Redis](https://img.shields.io/badge/Redis-7+-DC382D.svg?logo=redis&logoColor=white)](https://redis.io)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-4169E1.svg?logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg?logo=react&logoColor=black)](https://react.dev)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg?logo=docker&logoColor=white)](https://www.docker.com)

A stateful, autonomous multi-agent AI system built to solve complex, multi-step problems through coordinated multi-agent workflows. Orchestrated via **LangGraph**, backed by **Celery** and **Redis** for distributed asynchronous tool dispatch, persisted to **PostgreSQL** for full auditability, and streamed in real-time to a modern **React** frontend via **WebSockets**.

---

## 🏛️ System Architecture

```
                                  ┌───────────────────────────┐
                                  │   React 18 UI (:3000)     │
                                  └──────┬────────────▲───────┘
                                         │            │
                           1. POST /tasks│            │ 2. WS /api/ws/:id
                                         ▼            │ (Live Streaming)
                                  ┌───────────────────┴───────┐
                                  │   FastAPI Server (:8000)  │
                                  └──────┬────────────▲───────┘
                                         │            │
                     3. Store Initial Run│            │ 6. Real-time Events
                                         ▼            │
                              ┌─────────────────────┐ │
                              │ PostgreSQL DB (:5432)│ │
                              └─────────────────────┘ │
                                                      │
                                                      │
                       4. Trigger Graph Execution     │
                                 │                    │
                                 ▼                    │
             ┌────────────────────────────────────────┴─────────┐
             │            LangGraph State Machine               │
             │                                                  │
             │   ┌───────────────┐     Plan Steps               │
             │   │    Planner    │─────────────────────────┐    │
             │   └───────────────┘                         ▼    │
             │                                   ┌────────────┐ │
             │                      ┌───────────►│ Researcher │ │
             │   5. Synthesize      │ Loop Steps └─────┬──────┘ │
             │      Deliverable     │                  │        │
             │           ┌──────────┴───┐              │        │
             │           │  Synthesizer │              │ 7. Dispatch
             │           └──────────────┘              │    Tool
             │                                         ▼        │
             └─────────────────────────────────────────┼────────┘
                                                       │
                                  ┌────────────────────┴───┐
                                  │ Redis Message Broker   │
                                  └────────────┬───────────┘
                                               │
                                  8. Consume   │ 9. Return Result
                                               ▼
                                  ┌────────────────────────┐
                                  │ Celery Worker Queue    │
                                  └────────────┬───────────┘
                                               │
                                               ▼
                                  ┌────────────────────────┐
                                  │ External Tools:        │
                                  │ • WebSearchTool        │
                                  │ • WeatherSearchTool    │
                                  │ • CalculatorTool       │
                                  └────────────────────────┘
```

---

## 🚀 Key Features

1. **Stateful Multi-Agent Workflow**:
   - **Strategic Planner**: Analyzes goals and formulates structured, tool-assisted action steps.
   - **Specialized Researcher**: Executes operations, interfaces with external APIs, and isolates failures.
   - **Executive Synthesizer**: Consolidates gathered evidence into a comprehensive Markdown response.
2. **Distributed Asynchronous Tool Execution**:
   - Long-running or network I/O tools are offloaded to **Celery** workers over **Redis**, keeping the FastAPI server responsive.
3. **Strict Schema Validation & Resilient Tools**:
   - Every tool enforces strict **Pydantic schemas**.
   - Built-in error trapping converts API faults into recovery feedback rather than crashing the system.
4. **Relational State Persistence & Auditability**:
   - **PostgreSQL** stores all runs (`task_runs`) and granular state transitions (`agent_events`).
   - Queryable timeline of every thought, parameter, and tool output.
5. **Real-Time WebSocket Streaming**:
   - Bidirectional WebSocket (`/api/ws/{task_id}`) streaming event traces live to the UI.
   - Integrated heartbeat mechanism to prevent connection drops.
6. **Multi-Provider LLM Integration**:
   - High-speed **Groq** acceleration (`llama-3.3-70b-versatile`).
   - Native **OpenAI** support (`gpt-4o-mini`).
   - Built-in intelligent fallback model ensuring zero-crash evaluation even without API keys.

---

## 📂 Repository Structure

```
.
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes.py          # REST endpoints (/api/tasks)
│   │   │   └── websocket.py       # WebSocket streaming manager
│   │   ├── core/
│   │   │   └── config.py          # Pydantic Settings configuration
│   │   ├── db/
│   │   │   ├── models.py          # SQLAlchemy TaskRun and AgentEvent models
│   │   │   ├── repository.py      # Async database query layer
│   │   │   └── session.py         # Async engine and init_db
│   │   ├── tools/
│   │   │   ├── schemas.py         # Pydantic tool input models
│   │   │   └── implementations.py # Web search, weather, and safe calculator
│   │   ├── worker/
│   │   │   ├── celery_app.py      # Celery broker configuration
│   │   │   └── tasks.py           # Celery tool task definitions
│   │   ├── agents/
│   │   │   ├── state.py           # LangGraph AgentState TypedDict
│   │   │   ├── prompts.py         # Specialized agent system prompts
│   │   │   ├── llm.py             # Groq / OpenAI / Mock factory
│   │   │   ├── nodes.py           # Planner, Researcher, Synthesizer nodes
│   │   │   └── graph.py           # LangGraph StateGraph compilation
│   │   └── main.py                # FastAPI app entry point
│   ├── Dockerfile                 # Backend container definition
│   └── requirements.txt           # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Navbar.tsx
│   │   │   ├── TaskForm.tsx
│   │   │   ├── StateGraphVisualizer.tsx
│   │   │   ├── TaskTimeline.tsx
│   │   │   ├── EventCard.tsx
│   │   │   ├── FinalResultView.tsx
│   │   │   └── TaskHistoryModal.tsx
│   │   ├── hooks/
│   │   │   └── useAgentWebSocket.ts
│   │   ├── services/
│   │   │   └── api.ts
│   │   ├── types/
│   │   │   └── index.ts
│   │   ├── App.tsx
│   │   ├── index.css
│   │   └── main.tsx
│   ├── Dockerfile                 # Frontend container definition
│   ├── package.json
│   └── vite.config.ts
├── docker-compose.yml             # 5-service orchestration
├── .env.example                   # Environment configuration template
├── EVALUATION.md                  # Comprehensive architectural report
└── README.md
```

---

## ⚡ Quick Start

### 1. Clone and Configure Environment

```bash
git clone <repo-url>
cd Multi-Agent-AI-Orchestration-System-with-LangChain-FastAPI-and-React

# Copy environment file
cp .env.example .env
```

### 2. Configure Your LLM API Key (Groq or OpenAI)

Edit `.env` to include your Groq API key:

```bash
GROQ_API_KEY=gsk_your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```

*(If no key is supplied, the system automatically uses its built-in intelligent fallback model, allowing full end-to-end testing and evaluation).*

### 3. Spin Up All Services via Docker Compose

```bash
docker compose up --build
```

The system will start all 5 services with automated health checks:
- **UI (React)**: [http://localhost:3000](http://localhost:3000)
- **API (FastAPI)**: [http://localhost:8000](http://localhost:8000)
- **API Docs (Swagger)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **PostgreSQL**: `localhost:5432`
- **Redis**: `localhost:6379`
- **Celery Worker**: Background task executor

---

## 🛠️ Custom Tools Reference

| Tool Name | Input Schema | Execution Target | Error Handling |
| :--- | :--- | :--- | :--- |
| `web_search` | `query: str`, `max_results: int` | Celery Worker (Redis) | Handles rate limits and network drops; returns informative summary or guidance. |
| `weather_search` | `location: str`, `units: str` | Celery Worker (Redis) | Geocodes location and fetches live weather + 3-day forecast from Open-Meteo. |
| `calculator` | `expression: str`, `description: str` | Celery Worker (Redis) | Safe AST-parsed evaluation supporting arithmetic, CAGR, and statistical calculations without code injection risks. |

---

## 📡 API Endpoints

- `POST /api/tasks` — Accepts `{"prompt": "string"}` and returns `{"task_id": "uuid"}` while scheduling the multi-agent graph in the background.
- `GET /api/tasks` — Lists historical task runs from PostgreSQL.
- `GET /api/tasks/{task_id}` — Gets status and final result of a task.
- `GET /api/tasks/{task_id}/events` — Retrieves all audit events for a task.
- `WS /api/ws/{task_id}` — Real-time bidirectional WebSocket streaming agent thoughts, tool dispatches, and final results.
- `GET /api/health` — Service health and LLM provider status.

---

## 🧪 Testing & Verification

### 1. Test via cURL

```bash
# Initiate a multi-agent task
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is the weather in Tokyo and based on that, what should I pack?"}'

# Output:
# {"task_id":"<uuid>","status":"PENDING","prompt":"...","message":"Task accepted."}
```

### 2. Inspect Database Audit Trail

```bash
docker compose exec db psql -U postgres -d multiagent_db -c "SELECT id, status, prompt FROM task_runs;"
docker compose exec db psql -U postgres -d multiagent_db -c "SELECT agent_name, event_type, timestamp FROM agent_events ORDER BY timestamp DESC LIMIT 10;"
```

### 3. Check Celery Worker Logs

```bash
docker compose logs worker -f
```

---

## ❓ FAQ & Troubleshooting

- **WebSocket connection drops during long runs?**
  FastAPI includes a built-in 15-second heartbeat loop over the WebSocket channel to keep intermediary proxies and Docker networks alive.
- **How to view Celery tasks?**
  Run `docker compose logs worker -f` to observe tool execution logs as tasks are received from Redis.
- **Can I run this without external API keys?**
  Yes! The system automatically detects missing API keys and activates its intelligent fallback reasoning engine so that all graph edges, Celery tasks, database persistence, and WebSocket feeds function smoothly.