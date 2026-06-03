from sqlmodel import create_engine, SQLModel
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import sessionmaker
from contextlib import asynccontextmanager

from src.config import Config

engine = AsyncEngine(
    create_engine(
    url=Config.DATABASE_URL,
    echo=True
))

async def init_db():
    async with engine.begin() as conn:
        from src.auth.models import User
        await conn.run_sync(SQLModel.metadata.create_all)

Session = sessionmaker(
    bind = engine,
    class_ = AsyncSession,
    expire_on_commit=False
)

@asynccontextmanager
async def get_session_ctx():
    async with Session() as session:
        yield session

async def get_session() -> AsyncSession:
    async with Session() as session:
        yield session