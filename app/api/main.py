from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from .auth.routes import router as auth_router
from app.agents.run.routes import router as agents_router

app = FastAPI()

app.include_router(auth_router)
app.include_router(agents_router)

@app.get("/health")
async def health():
    return {"status": "ok"}
