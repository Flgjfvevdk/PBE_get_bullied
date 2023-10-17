import utils
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession


ENGINE = create_async_engine(utils.getenv("DB_URL"))

new_session = async_sessionmaker(bind=ENGINE, class_=AsyncSession)

class Base(DeclarativeBase, MappedAsDataclass):
    pass