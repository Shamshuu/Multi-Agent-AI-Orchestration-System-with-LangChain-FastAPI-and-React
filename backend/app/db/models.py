import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def utc_now():
    return datetime.now(timezone.utc)


class TaskRun(Base):
    __tablename__ = "task_runs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    prompt = Column(Text, nullable=False)
    status = Column(String(32), default="PENDING", nullable=False)  # PENDING, RUNNING, COMPLETED, FAILED
    final_result = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    events = relationship("AgentEvent", back_populates="task_run", cascade="all, delete-orphan", order_by="AgentEvent.timestamp")

    def to_dict(self):
        return {
            "id": self.id,
            "prompt": self.prompt,
            "status": self.status,
            "final_result": self.final_result,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class AgentEvent(Base):
    __tablename__ = "agent_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_run_id = Column(String(36), ForeignKey("task_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_name = Column(String(64), nullable=False)  # Planner, Researcher, Synthesizer, Tool, System
    event_type = Column(String(64), nullable=False)  # AGENT_THOUGHT, TOOL_INVOCATION, TOOL_RESULT, STATE_TRANSITION, ERROR, COMPLETE
    payload = Column(JSON, nullable=False, default=dict)
    timestamp = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    task_run = relationship("TaskRun", back_populates="events")

    def to_dict(self):
        return {
            "id": self.id,
            "task_run_id": self.task_run_id,
            "agent_name": self.agent_name,
            "event_type": self.event_type,
            "payload": self.payload,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
