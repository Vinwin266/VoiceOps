from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.run.model import AgentCreateRunResponse, AgentRunRequest
from app.agents.run.service import create_run
from app.api.auth.models import User
from app.api.auth.service import get_current_active_user
from app.api.db.session import get_db

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("/run", response_model=AgentCreateRunResponse)
async def run_agent(
    agent_run: AgentRunRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    return await create_run(
        user_id=current_user.user_id,
        input_text=agent_run.input_text,
        db=db,
    )
