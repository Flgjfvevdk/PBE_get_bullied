from database import Base
from bully import Bully
from typing import Optional, List, Dict, TypeVar, Generic, Type
import player_info
from database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship, composite
from sqlalchemy import ForeignKey, String
import player_info
import color_str


class Consommable(Base):
    __tablename__ = "consommable"

    # Relation inverse vers Player
    player = relationship('Player', back_populates='consommables')
    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    player_id: Mapped[int] = mapped_column(ForeignKey("player.id"),init=False) 
    player: Mapped["player_info.Player"] = relationship(back_populates="consommables", init=False, lazy="selectin")

    name: Mapped[str] = mapped_column(String(50))

    def __init__(self, name:str = "Consommable"):
        self.name = name

    def apply(self, b:Bully):
        pass

    def get_print(self) -> str:
        return f"A consommable"

class CreatorConsoAliment():

    def __init__(self,value:float):
        self.initiate_var("", "", value, "")
        raise Exception("This class is not supposed to exist")
    
    def initiate_var(self, stat_buff:str, stat_debuff:str, value:float, name:str):
        self.stat_buff = stat_buff
        self.stat_debuff = stat_debuff
        self.value = value
        self.name = name

    def construct(self)->Consommable:
        c = Consommable(self.name)
        c.apply = self.apply
        c.get_print = self.get_print
        return c

    def apply(self, b:Bully):
        # Calculate actual debuff ensuring it doesn't drop below 1
        current_debuffed_stat = getattr(b.stats, self.stat_debuff)
        actual_buff = min(self.value, current_debuffed_stat - 1)

        if actual_buff > 0:
            # Apply the debuff
            setattr(b.stats, self.stat_debuff, current_debuffed_stat - actual_buff)
            
            # Apply the buff with the actual debuff value as its maximum
            current_buff_value = getattr(b.stats, self.stat_buff)
            setattr(b.stats, self.stat_buff, current_buff_value + actual_buff)
            
    def get_print(self) -> str:
        return f"{self.name} : on use, debuff {color_str.red(self.stat_debuff)} up to {self.value} (min 1) and buff {color_str.blue(self.stat_buff)} by the same amount."

class Gigot(CreatorConsoAliment):
    def __init__(self, value):
        self.initiate_var(stat_buff='strength', stat_debuff='agility', value=value, name=f'Gigot[{value}]')
class Banane(CreatorConsoAliment):
    def __init__(self, value):
        self.initiate_var(stat_buff='strength', stat_debuff='lethality', value=value, name=f'Banane[{value}]')
class Creme(CreatorConsoAliment):
    def __init__(self, value):
        self.initiate_var(stat_buff='strength', stat_debuff='viciousness', value=value, name=f'Creme[{value}]')
class Piment(CreatorConsoAliment):
    def __init__(self, value):
        self.initiate_var(stat_buff='agility', stat_debuff='strength', value=value, name=f'Piment[{value}]')
class Chocolat(CreatorConsoAliment):
    def __init__(self, value):
        self.initiate_var(stat_buff='agility', stat_debuff='lethality', value=value, name=f'Chocolat[{value}]')
class Meringue(CreatorConsoAliment):
    def __init__(self, value):
        self.initiate_var(stat_buff='agility', stat_debuff='viciousness', value=value, name=f'Meringue[{value}]')
class Bonbon(CreatorConsoAliment):
    def __init__(self, value):
        self.initiate_var(stat_buff='lethality', stat_debuff='strength', value=value, name=f'Bonbon[{value}]')
class Merguez(CreatorConsoAliment):
    def __init__(self, value):
        self.initiate_var(stat_buff='lethality', stat_debuff='agility', value=value, name=f'Merguez[{value}]')
class Citron(CreatorConsoAliment):
    def __init__(self, value):
        self.initiate_var(stat_buff='lethality', stat_debuff='viciousness', value=value, name=f'Citron[{value}]')
class Bierre(CreatorConsoAliment):
    def __init__(self, value):
        self.initiate_var(stat_buff='viciousness', stat_debuff='strength', value=value, name=f'Bierre[{value}]')
class Beurre(CreatorConsoAliment):
    def __init__(self, value):
        self.initiate_var(stat_buff='viciousness', stat_debuff='agility', value=value, name=f'Beurre[{value}]')
class Yaourt(CreatorConsoAliment):
    def __init__(self, value):
        self.initiate_var(stat_buff='viciousness', stat_debuff='lethality', value=value, name=f'Yaourt[{value}]')

aliments:list[Type[CreatorConsoAliment]] = [Gigot, Banane, Creme, Piment, Chocolat, Meringue, Bonbon, Merguez, Citron, Bierre, Beurre, Yaourt]
