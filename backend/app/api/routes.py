import asyncio
import json
import uuid
import logging
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db, AsyncSessionLocal
from app.db import repository
from app.api.websocket import manager
from app.agents.graph import execute_agent_workflow
from app.core.config import settings

logger = logging.getLogger("api_routes")
router = APIRouter()


class TaskCreateRequest(BaseModel):
    prompt: str = Field(..., min_length=3, description="The complex user instruction or problem to solve.")


class TaskResponse(BaseModel):
    task_id: str
    status: str
    prompt: str
    created_at: Optional[str] = None
    final_result: Optional[str] = None


@router.post("/tasks", response_model=dict, status_code=202)
async def create_task(
    request: TaskCreateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Primary REST endpoint to initiate tasks.
    Creates a TaskRun record in PostgreSQL, dispatches the agent workflow asynchronously,
    and immediately returns the unique task_id.
    """
    task_id = str(uuid.uuid4())
    task_run = await repository.create_task_run(db, prompt=request.prompt, task_id=task_id)

    # Event callback to forward LangGraph events directly to connected WebSockets
    async def stream_event_callback(agent_name: str, event_type: str, payload: dict):
        event_message = {
            "task_id": task_id,
            "agent": agent_name,
            "event_type": event_type,
            "payload": payload,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await manager.broadcast_to_task(task_id, event_message)

    # Run agent workflow in the background
    background_tasks.add_task(
        execute_agent_workflow,
        task_id=task_id,
        prompt=request.prompt,
        event_callback=stream_event_callback,
    )

    return {
        "task_id": task_id,
        "status": task_run.status,
        "prompt": task_run.prompt,
        "message": "Task accepted. Connect to WebSocket /api/ws/{task_id} for live trace.",
    }


@router.get("/tasks", response_model=List[dict])
async def list_tasks(db: AsyncSession = Depends(get_db)):
    """Retrieve recent task runs for audit and history."""
    tasks = await repository.get_all_task_runs(db, limit=30)
    return [t.to_dict() for t in tasks]


@router.get("/tasks/{task_id}", response_model=dict)
async def get_task(task_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve details and status for a specific task."""
    task = await repository.get_task_run(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")
    return task.to_dict()


@router.get("/tasks/{task_id}/events", response_model=List[dict])
async def get_task_events(task_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve all historical agent events for audit trail."""
    events = await repository.get_agent_events(db, task_id)
    return [e.to_dict() for e in events]


@router.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "llm_provider": settings.LLM_PROVIDER,
        "has_groq_key": bool(settings.GROQ_API_KEY),
        "has_openai_key": bool(settings.OPENAI_API_KEY),
    }


@router.websocket("/ws/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    """
    WebSocket endpoint for real-time task monitoring.
    Accepts connections, replays existing audit events from Postgres,
    and streams live events as agents execute.
    """
    await manager.connect(websocket, task_id)

    # Replay existing recorded events from database if client connects after run started
    try:
        async with AsyncSessionLocal() as session:
            existing_events = await repository.get_agent_events(session, task_id)
            task_info = await repository.get_task_run(session, task_id)

        # Send initial status
        if task_info:
            await websocket.send_text(
                json.dumps({
                    "task_id": task_id,
                    "event_type": "INITIAL_STATE",
                    "agent": "System",
                    "payload": {
                        "status": task_info.status,
                        "prompt": task_info.prompt,
                        "final_result": task_info.final_result,
                    },
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
            )

        for event in existing_events:
            await websocket.send_text(
                json.dumps({
                    "task_id": task_id,
                    "agent": event.agent_name,
                    "event_type": event.event_type,
                    "payload": event.payload,
                    "timestamp": event.timestamp.isoformat() if event.timestamp else None,
                })
            )

        # Keep-alive ping loop to prevent proxy and Docker network timeouts
        while True:
            try:
                # Wait for any client message or 15s timeout to send ping
                data = await asyncio.wait_for(websocket.receive_text(), timeout=15.0)
                # Handle client ping
                if data == "ping":
                    await websocket.send_text(json.dumps({"type": "pong", "timestamp": datetime.now(timezone.utc).isoformat()}))
            except asyncio.TimeoutError:
                # Send heartbeat frame to keep WebSocket open during long tool executions
                await websocket.send_text(json.dumps({"type": "heartbeat", "timestamp": datetime.now(timezone.utc).isoformat()}))

    except WebSocketDisconnect:
        await manager.disconnect(websocket, task_id)
    except Exception as exc:
        logger.warning(f"WebSocket connection error for task {task_id}: {str(exc)}")
        await manager.disconnect(websocket, task_id)
