from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase


DATABASE_URL = "postgresql+asyncpg://postgres:1234@localhost/test.db"
SECRET_KEY = "zuzula_tutula_pupula"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with SessionLocal() as session:
        yield session 