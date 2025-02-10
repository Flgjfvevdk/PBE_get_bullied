from utils.database import Base
from typing import List
from sqlalchemy.orm import Mapped, relationship, MappedAsDataclass, mapped_column
from sqlalchemy import Table, Column, Integer, ForeignKey
from datetime import datetime
import bully
import consumable


class Player(Base):
    __tablename__ = "player"

    id: Mapped[int] = mapped_column(init=False, primary_key=True)

    money: Mapped[int]
    keys: Mapped[int] = mapped_column(default = 8)
    last_payday: Mapped[datetime] = mapped_column(default=datetime.utcfromtimestamp(0.0))
    max_dungeon: Mapped[int] = mapped_column(default = 0)
    max_ruin: Mapped[int] = mapped_column(default = 0)
    nb_referrals: Mapped[int] = mapped_column(default = 0)

    bullies: Mapped[List[bully.Bully]] = relationship(back_populates="player", cascade="all, delete-orphan", default_factory=list, lazy="selectin")
    consumables: Mapped[List[consumable.Consumable]] = relationship(back_populates="player", cascade="all, delete-orphan", default_factory=list, lazy="selectin")
    
    def get_equipe(self) -> List[bully.Bully]:
        return [b for b in self.bullies if not b.in_reserve]
    
    def get_reserve(self) -> List[bully.Bully]:
        return [b for b in self.bullies if b.in_reserve]