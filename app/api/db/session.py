import os
##async engine
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine, async_sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

engine = create_async_engine(DATABASE_URL,echo=True,pool_pre_ping=True)

AsyncSessionLocal = async_sessionmaker(bind = engine, class_=AsyncSession,expire_on_commit=False)

async def get_db():
    async with AsyncSessionLocal() as db:
        yield db

async def close_db(db: AsyncSession):
    await db.close()

