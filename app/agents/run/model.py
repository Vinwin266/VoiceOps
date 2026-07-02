from datetime import UTC, datetime
from typing import Optional

from pydantic import BaseModel
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.api.auth.models import Base


class AgentRunRequest(BaseModel):
    input_text: str
    input_format: str = "raw_text"  # "raw_text" | "jsonl"


class AgentCreateRunResponse(BaseModel):
    run_id: int
    user_id: int
    input_text: str
    input_format: str
    status: str
    result: Optional[str] = None
    error: Optional[str] = None


class Job(Base):
    __tablename__ = "agent_runs"

    run_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.user_id"),
        index=True,
        nullable=False,
    )
    input_text: Mapped[str] = mapped_column(Text, nullable=False)
    input_format: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="raw_text",
        server_default="raw_text",
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
        server_default="pending",
    )
    result: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )
