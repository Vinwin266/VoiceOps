from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.run.model import AgentCreateRunResponse, Job


async def create_run(
    user_id: int,
    input_text: str,
    db: AsyncSession,
) -> AgentCreateRunResponse:
    job = Job(
        user_id=user_id,
        input_text=input_text,
        status="pending",
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return _to_run_response(job)


async def get_run_for_user(
    run_id: int,
    user_id: int,
    db: AsyncSession,
) -> AgentCreateRunResponse | None:
    result = await db.execute(
        select(Job).where(
            Job.run_id == run_id,
            Job.user_id == user_id,
        )
    )
    job = result.scalar_one_or_none()
    if job is None:
        return None
    return _to_run_response(job)


def _to_run_response(job: Job) -> AgentCreateRunResponse:
    return AgentCreateRunResponse(
        run_id=job.run_id,
        user_id=job.user_id,
        input_text=job.input_text,
        status=job.status,
        result=job.result,
        error=job.error,
    )


async def list_runs(user_id: int, db: AsyncSession) -> list[AgentCreateRunResponse]:
    result = await db.execute(
        select(Job)
        .where(Job.user_id == user_id)
        .order_by(Job.run_id.desc())
    )
    return [_to_run_response(job) for job in result.scalars().all()]
