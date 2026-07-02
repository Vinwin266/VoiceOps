from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.api.auth.models import Base
from app.voiceops.events.model import VoiceOpsEvent
from app.voiceops.fingerprints.matcher import FingerprintMatch


class VoiceOpsEventRow(Base):
    __tablename__ = "voice_ops_events"

    event_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    run_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("agent_runs.run_id"),
        nullable=False,
        index=True,
    )
    phase: Mapped[str | None] = mapped_column(Text, nullable=True)
    module: Mapped[str | None] = mapped_column(Text, nullable=True)
    pipeline_node: Mapped[str | None] = mapped_column(Text, nullable=True)
    level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    error_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    fingerprint: Mapped[str | None] = mapped_column(Text, nullable=True)
    call_sid: Mapped[str | None] = mapped_column(Text, nullable=True)
    room_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    agent_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    turn_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    provider: Mapped[str | None] = mapped_column(Text, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    taxonomy_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    message_redacted: Mapped[str] = mapped_column(Text, nullable=False)


async def persist_events(
    events: list[VoiceOpsEvent],
    matches: list[FingerprintMatch],
    run_id: int,
    db: AsyncSession,
) -> None:
    fingerprints_by_event_id = _best_fingerprints_by_event_id(matches)

    for event in events:
        row = VoiceOpsEventRow(
            event_id=event.event_id,
            run_id=run_id,
            phase=event.phase,
            module=event.module,
            pipeline_node=event.pipeline_node,
            level=event.level,
            error_type=event.error_type,
            fingerprint=fingerprints_by_event_id.get(event.event_id, event.fingerprint),
            call_sid=event.call_sid,
            room_id=event.room_id,
            agent_id=event.agent_id,
            turn_id=event.turn_id,
            provider=event.provider,
            latency_ms=event.latency_ms,
            taxonomy_confidence=event.taxonomy_confidence,
            message_redacted=event.message_redacted,
        )
        db.add(row)
    await db.commit()


def _best_fingerprints_by_event_id(
    matches: list[FingerprintMatch],
) -> dict[str, str]:
    best_matches: dict[str, FingerprintMatch] = {}

    for match in matches:
        existing = best_matches.get(match.event_id)
        if existing is None or match.confidence > existing.confidence:
            best_matches[match.event_id] = match

    return {
        event_id: match.fingerprint
        for event_id, match in best_matches.items()
    }
