import utils
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession, async_scoped_session
import sqlalchemy.types as types
from pathlib import Path

ENGINE = create_async_engine(utils.getenv("DB_URL"))

new_session = async_sessionmaker(bind=ENGINE, class_=AsyncSession)

class Base(DeclarativeBase, MappedAsDataclass):
    pass

class DBPath(types.TypeDecorator):
    impl = types.String

    cache_ok = True

    def process_bind_param(self, value, dialect):
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return Path(value)

async def init_models():
    async with ENGINE.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)