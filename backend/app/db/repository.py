import uuid
from typing import List, Optional, Any, Dict
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import TaskRun, AgentEvent, utc_now


async def create_task_run(session: AsyncSession, prompt: str, task_id: Optional[str] = None) -> TaskRun:
    """Create a new TaskRun record with initial PENDING status."""
    task_run = TaskRun(
        id=task_id or str(uuid.uuid4()),
        prompt=prompt,
        status="PENDING",
        created_at=utc_now(),
        updated_at=utc_now(),
    )
    session.add(task_run)
    await session.commit()
    await session.refresh(task_run)
    return task_run


async def update_task_run(
    session: AsyncSession,
    task_id: str,
    status: Optional[str] = None,
    final_result: Optional[str] = None,
) -> Optional[TaskRun]:
    """Update task run status and/or final result."""
    stmt = select(TaskRun).where(TaskRun.id == task_id)
    result = await session.execute(stmt)
    task_run = result.scalar_one_or_none()
    if not task_run:
        return None

    if status is not None:
        task_run.status = status
    if final_result is not None:
        task_run.final_result = final_result
    task_run.updated_at = utc_now()

    await session.commit()
    await session.refresh(task_run)
    return task_run


async def create_agent_event(
    session: AsyncSession,
    task_run_id: str,
    agent_name: str,
    event_type: str,
    payload: Dict[str, Any],
) -> AgentEvent:
    """Record an agent event for auditable tracking."""
    event = AgentEvent(
        id=str(uuid.uuid4()),
        task_run_id=task_run_id,
        agent_name=agent_name,
        event_type=event_type,
        payload=payload,
        timestamp=utc_now(),
    )
    session.add(event)
    await session.commit()
    await session.refresh(event)
    return event


async def get_task_run(session: AsyncSession, task_id: str) -> Optional[TaskRun]:
    """Retrieve a single TaskRun by ID."""
    stmt = select(TaskRun).where(TaskRun.id == task_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_all_task_runs(session: AsyncSession, limit: int = 50) -> List[TaskRun]:
    """List recent TaskRuns ordered by creation time descending."""
    stmt = select(TaskRun).order_by(desc(TaskRun.created_at)).limit(limit)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_agent_events(session: AsyncSession, task_id: str) -> List[AgentEvent]:
    """Retrieve all chronological events associated with a TaskRun."""
    stmt = (
        select(AgentEvent)
        .where(AgentEvent.task_run_id == task_id)
        .order_by(AgentEvent.timestamp.asc())
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())
