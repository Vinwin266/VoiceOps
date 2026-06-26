from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.run.model import AgentCreateRunResponse, AgentRunRequest
from app.agents.run.run import _run_agent
from app.agents.run.service import create_run, get_run_for_user, list_runs
from app.api.auth.models import User
from app.api.auth.service import get_current_active_user
from app.api.db.session import get_db

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("/run", response_model=AgentCreateRunResponse)
async def run_agent(
    agent_run: AgentRunRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    run = await create_run(
        user_id=current_user.user_id,
        input_text=agent_run.input_text,
        db=db,
    )
    background_tasks.add_task(_run_agent, run.run_id)
    return run


@router.get("/run/{run_id}", response_model=AgentCreateRunResponse)
async def get_run(
    run_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    agent_run = await get_run_for_user(
        run_id=run_id,
        user_id=current_user.user_id,
        db=db,
    )
    if agent_run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return agent_run


@router.get("/runs", response_model=list[AgentCreateRunResponse])
async def get_runs(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    return await list_runs(user_id=current_user.user_id, db=db)
