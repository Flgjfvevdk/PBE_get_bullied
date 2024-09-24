from utils.helpers import getenv
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass
from sqlalchemy.ext.declarative import AbstractConcreteBase
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession, async_scoped_session
import sqlalchemy.types as types
from pathlib import Path

ENGINE = create_async_engine(getenv("DB_URL"))

new_session = async_sessionmaker(bind=ENGINE, class_=AsyncSession)

class Base(MappedAsDataclass, DeclarativeBase):
    pass


class DBPath(types.TypeDecorator):
    """
    Implementation of a representation of Path objects in the DB
    """
    impl = types.String

    cache_ok = True

    def process_bind_param(self, value, dialect):
        if isinstance(value, Path):
            return str(value)
        return value #On ne fait rien si on ne sait pas traiter

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return Path(value)

async def init_models():
    async with ENGINE.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)