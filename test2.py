from database import Base
from dataclasses import KW_ONLY, replace, dataclass
from bully import Bully, Stats
from discord.ext.commands import Context, Bot
import discord
from typing import Optional, List, Dict, TypeVar, Generic, Type
import interact_game
import player_info
import asyncio
from database import Base
import player_info
from dataclasses import KW_ONLY, replace, dataclass
import abc
import color_str
from sqlalchemy import ForeignKey, Column, Integer, String, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship, composite, declarative_base
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy.ext.asyncio.session import async_object_session


Base = declarative_base()

class Consommable(Base):
    __tablename__ = 'consommable'
    # id = Column(Integer, primary_key=True)
    # name = Column(String)
    # type = Column(String)  # Pour le polymorphismeid = Column(Integer, primary_key=True)
    id: Mapped[int] = mapped_column(primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("player.id"), nullable=True) 
    player: Mapped["player_info.Player"] = relationship(back_populates="consommables", lazy="selectin")

    name: Mapped[str] = mapped_column(String(50))
    type: Mapped[str] = mapped_column(String)
    

    __mapper_args__ = {
        'polymorphic_identity': 'consommable',
        'polymorphic_on': type
    }


    def apply(self, b: Bully):
        raise NotImplementedError("Subclasses should implement this!")
    
    def get_print(self) -> str:
        raise NotImplementedError("Subclasses should implement get_print!")
    

class Aliment(Consommable):
    __tablename__ = 'aliments'
    # id = Column(Integer, ForeignKey('consommables.id'), primary_key=True)
    # stat_buff = Column(String)
    # stat_debuff = Column(String)
    # value = Column(Float)
    # id : Mapped[int] = mapped_column(primary_key=True)
    id: Mapped[int] = mapped_column(ForeignKey('consommable.id'), primary_key=True)

    # player: Mapped["player_info.Player"] = relationship(back_populates="consommables", init=False, lazy="selectin")
    # player_id: Mapped[int] = mapped_column(ForeignKey("player.id"),init=False) 

    stat_buff: Mapped[str] = mapped_column(String(50))
    stat_debuff: Mapped[str] = mapped_column(String(50))
    value: Mapped[float] = mapped_column(Float)

    consommable = relationship("Consommable", back_populates="aliment", uselist=False)

    __mapper_args__ = {
        'polymorphic_identity': 'aliment',
        'inherit_condition': id == Consommable.id,
    }

    def apply(self, b: Bully):
        current_debuffed_stat = getattr(b.stats, self.stat_debuff)
        actual_buff = min(self.value, current_debuffed_stat - 1)
        if actual_buff > 0:
            setattr(b.stats, self.stat_debuff, current_debuffed_stat - actual_buff)
            current_buff_value = getattr(b.stats, self.stat_buff)
            setattr(b.stats, self.stat_buff, current_buff_value + actual_buff)

    def get_print(self) -> str:
        return f"{self.name} : on use, debuff {color_str.red(self.stat_debuff)} up to {self.value} (min 1) and buff {color_str.blue(self.stat_buff)} by the same amount."

class Gigot(Aliment):
    __mapper_args__ = {
        'polymorphic_identity': 'gigot'
    }

    def __init__(self, value: float):
        super().__init__(name=f'Gigot[{value}]', stat_buff='strength', stat_debuff='agility', value=value)

class Banane(Aliment):
    __mapper_args__ = {
        'polymorphic_identity': 'banane'
    }

    def __init__(self, value: float):
        super().__init__(name=f'Banane[{value}]', stat_buff='strength', stat_debuff='lethality', value=value)

class Creme(Aliment):
    __mapper_args__ = {
        'polymorphic_identity': 'creme'
    }

    def __init__(self, value: float):
        super().__init__(name=f'Creme[{value}]', stat_buff='strength', stat_debuff='viciousness', value=value)

class Piment(Aliment):
    __mapper_args__ = {
        'polymorphic_identity': 'piment'
    }

    def __init__(self, value: float):
        super().__init__(name=f'Piment[{value}]', stat_buff='agility', stat_debuff='strength', value=value)

class Chocolat(Aliment):
    __mapper_args__ = {
        'polymorphic_identity': 'chocolat'
    }

    def __init__(self, value: float):
        super().__init__(name=f'Chocolat[{value}]', stat_buff='agility', stat_debuff='lethality', value=value)

class Meringue(Aliment):
    __mapper_args__ = {
        'polymorphic_identity': 'meringue'
    }

    def __init__(self, value: float):
        super().__init__(name=f'Meringue[{value}]', stat_buff='agility', stat_debuff='viciousness', value=value)

class Bonbon(Aliment):
    __mapper_args__ = {
        'polymorphic_identity': 'bonbon'
    }

    def __init__(self, value: float):
        super().__init__(name=f'Bonbon[{value}]', stat_buff='lethality', stat_debuff='strength', value=value)

class Merguez(Aliment):
    __mapper_args__ = {
        'polymorphic_identity': 'merguez'
    }

    def __init__(self, value: float):
        super().__init__(name=f'Merguez[{value}]', stat_buff='lethality', stat_debuff='agility', value=value)

class Citron(Aliment):
    __mapper_args__ = {
        'polymorphic_identity': 'citron'
    }

    def __init__(self, value: float):
        super().__init__(name=f'Citron[{value}]', stat_buff='lethality', stat_debuff='viciousness', value=value)

class Bierre(Aliment):
    __mapper_args__ = {
        'polymorphic_identity': 'bierre'
    }

    def __init__(self, value: float):
        super().__init__(name=f'Bierre[{value}]', stat_buff='viciousness', stat_debuff='strength', value=value)

class Beurre(Aliment):
    __mapper_args__ = {
        'polymorphic_identity': 'beurre'
    }

    def __init__(self, value: float):
        super().__init__(name=f'Beurre[{value}]', stat_buff='viciousness', stat_debuff='agility', value=value)

class Yaourt(Aliment):
    __mapper_args__ = {
        'polymorphic_identity': 'yaourt'
    }

    def __init__(self, value: float):
        super().__init__(name=f'Yaourt[{value}]', stat_buff='viciousness', stat_debuff='lethality', value=value)



# class OtherConso(Consommable):
#     __tablename__ = 'other_conso'
#     id = Column(Integer, ForeignKey('consommables.id'), primary_key=True)

#     __mapper_args__ = {
#         'polymorphic_identity': 'other_conso',
#         'inherit_condition': id == Consommable.id,
#     }

#     def apply(self, b: Bully):
#         print(f"{self.name} has a unique effect on {b.name}")

aliments: list[Type[Aliment]] = [
    Gigot, Banane, Creme, Piment, Chocolat, Meringue, Bonbon, Merguez, Citron, Bierre, Beurre, Yaourt
]