from database import Base

from typing import List
from sqlalchemy.orm import Mapped, relationship, MappedAsDataclass, mapped_column
from datetime import datetime
import bully
import item

class Player(Base):
    __tablename__ = "player"

    id: Mapped[int] = mapped_column(init=False, primary_key=True)

    money: Mapped[int]
    keys: Mapped[int] = mapped_column(default = 8)
    max_dungeon: Mapped[int] = mapped_column(default = 0)
    last_payday: Mapped[datetime] = mapped_column(default=datetime.utcfromtimestamp(0.0))

    bullies: Mapped[List[bully.Bully]] = relationship(back_populates="player", cascade="all, delete-orphan", default_factory=list, lazy="selectin")
    items: Mapped[List[item.Item]] = relationship(back_populates="player", cascade="all, delete-orphan", default_factory=list, lazy="selectin")