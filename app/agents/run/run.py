from sqlalchemy import select, update

from app.agents.run.model import Job
from app.api.db.session import AsyncSessionLocal
from app.voiceops.analyzer import analyze_raw_text


async def _run_agent(run_id: int) -> dict:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Job).where(Job.run_id == run_id)
        )
        job = result.scalar_one_or_none()

        if job is None:
            return {
                "run_id": run_id,
                "status": "failed",
                "error": f"Job {run_id} not found",
            }

        try:
            await db.execute(
                update(Job)
                .where(Job.run_id == run_id)
                .values(status="running", error=None)
            )
            await db.commit()

            rca_report = analyze_raw_text(job.input_text, run_id=job.run_id)
            agent_result = rca_report.model_dump_json(indent=2)

            await db.execute(
                update(Job)
                .where(Job.run_id == run_id)
                .values(
                    status="completed",
                    result=agent_result,
                    error=None,
                )
            )
            await db.commit()

            return {
                "run_id": job.run_id,
                "user_id": job.user_id,
                "status": "completed",
                "result": agent_result,
                "error": None,
            }

        except Exception as exc:
            await db.execute(
                update(Job)
                .where(Job.run_id == run_id)
                .values(
                    status="failed",
                    error=str(exc),
                )
            )
            await db.commit()

            return {
                "run_id": job.run_id,
                "user_id": job.user_id,
                "status": "failed",
                "result": None,
                "error": str(exc),
            }
