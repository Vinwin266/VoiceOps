from sqlalchemy import select, update

from app.agents.run.model import Job
from app.api.db.session import AsyncSessionLocal
from app.voiceops.events.db import persist_events
from app.voiceops.graph.graph import run_rca_graph
from app.voiceops.graph.state import RCAState


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

            graph_input: RCAState = {"run_id": job.run_id}
            if job.input_format == "jsonl":
                graph_input["jsonl_input"] = job.input_text
            else:
                graph_input["raw_input"] = job.input_text
            result = run_rca_graph(graph_input)
            rca_report = result.get("report", None)
            if rca_report is None:
                errors = result.get("errors") or []
                raise ValueError(
                    errors[0] if errors else "RCA graph returned no report"
                )

            events = result.get("events") or []
            if events:
                await persist_events(events=events, run_id=job.run_id, db=db)

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
