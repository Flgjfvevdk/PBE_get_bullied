from database import Base
from dataclasses import KW_ONLY, replace, dataclass
from bully import Bully, Stats
from discord.ext.commands import Context, Bot
import discord
from typing import Optional, List, Dict, TypeVar, Generic, Type
import interact_game
import player_info
import asyncio
import player_info
from dataclasses import KW_ONLY, replace, dataclass
import abc
import color_str
from sqlalchemy import ForeignKey, Column, Integer, String, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship, composite, declarative_base
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy.ext.asyncio.session import async_object_session

CHOICE_TIMEOUT = 60
CONSO_NUMBER_MAX = 10


class Consommable(Base):
    __tablename__ = 'consommable'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    name: Mapped[str] = mapped_column(String(50))
    type: Mapped[str] = mapped_column(String)

    player_id: Mapped[int] = mapped_column(ForeignKey("player.id"),init=False) 
    player: Mapped["player_info.Player"] = relationship(back_populates="consommables", init=False, lazy="selectin")
    
    __mapper_args__ = {
        'polymorphic_identity': 'consommable',
        'polymorphic_on': type
    }

    def apply(self, b: Bully):
        raise NotImplementedError("Subclasses should implement this!")
    
    def get_print(self) -> str:
        raise NotImplementedError("Subclasses should implement get_print!")
    

class Aliment(Consommable):
    __tablename__ = 'aliment'
    id: Mapped[int] = mapped_column(ForeignKey('consommable.id'), init=False, primary_key=True)
    stat_buff: Mapped[str] = mapped_column(String(50))
    stat_debuff: Mapped[str] = mapped_column(String(50))
    value: Mapped[float] = mapped_column(Float)

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
        super().__init__(name=f'Gigot[{value}]', stat_buff='strength', stat_debuff='agility', value=value, type='gigot') 

class Banane(Aliment):
    __mapper_args__ = {
        'polymorphic_identity': 'banane'
    }

    def __init__(self, value: float):
        # super().__init__(name=f'Banane[{value}]', stat_buff='strength', stat_debuff='lethality', value=value)
        super().__init__(name=f'Banane[{value}]', stat_buff='strength', stat_debuff='lethality', value=value, type='banane')

class Creme(Aliment):
    __mapper_args__ = {
        'polymorphic_identity': 'creme'
    }

    def __init__(self, value: float):
        super().__init__(name=f'Creme[{value}]', stat_buff='strength', stat_debuff='viciousness', value=value, type='creme')

class Piment(Aliment):
    __mapper_args__ = {
        'polymorphic_identity': 'piment'
    }

    def __init__(self, value: float):
        super().__init__(name=f'Piment[{value}]', stat_buff='agility', stat_debuff='strength', value=value, type='piment')

class Chocolat(Aliment):
    __mapper_args__ = {
        'polymorphic_identity': 'chocolat'
    }

    def __init__(self, value: float):
        super().__init__(name=f'Chocolat[{value}]', stat_buff='agility', stat_debuff='lethality', value=value, type='chocolat')

class Meringue(Aliment):
    __mapper_args__ = {
        'polymorphic_identity': 'meringue'
    }

    def __init__(self, value: float):
        super().__init__(name=f'Meringue[{value}]', stat_buff='agility', stat_debuff='viciousness', value=value, type='meringue')

class Bonbon(Aliment):
    __mapper_args__ = {
        'polymorphic_identity': 'bonbon'
    }

    def __init__(self, value: float):
        super().__init__(name=f'Bonbon[{value}]', stat_buff='lethality', stat_debuff='strength', value=value, type='bonbon')

class Merguez(Aliment):
    __mapper_args__ = {
        'polymorphic_identity': 'merguez'
    }

    def __init__(self, value: float):
        super().__init__(name=f'Merguez[{value}]', stat_buff='lethality', stat_debuff='agility', value=value, type='merguez')

class Citron(Aliment):
    __mapper_args__ = {
        'polymorphic_identity': 'citron'
    }

    def __init__(self, value: float):
        super().__init__(name=f'Citron[{value}]', stat_buff='lethality', stat_debuff='viciousness', value=value, type='citron')

class Bierre(Aliment):
    __mapper_args__ = {
        'polymorphic_identity': 'bierre'
    }

    def __init__(self, value: float):
        super().__init__(name=f'Bierre[{value}]', stat_buff='viciousness', stat_debuff='strength', value=value, type='bierre')

class Beurre(Aliment):
    __mapper_args__ = {
        'polymorphic_identity': 'beurre'
    }

    def __init__(self, value: float):
        super().__init__(name=f'Beurre[{value}]', stat_buff='viciousness', stat_debuff='agility', value=value, type='beurre')

class Yaourt(Aliment):
    __mapper_args__ = {
        'polymorphic_identity': 'yaourt'
    }

    def __init__(self, value: float):
        super().__init__(name=f'Yaourt[{value}]', stat_buff='viciousness', stat_debuff='lethality', value=value, type='yaourt')



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

#_______________________________________________________________________
#_______________________________________________________________________
#_______________________________________________________________________
#_______________________________________________________________________
#_______________________________________________________________________
#_______________________________________________________________________

async def add_conso_to_player(ctx: Context, player: 'player_info.Player', c:Consommable, channel_cible=None):
    #Par défaut, le channel d'envoie est le channel du contexte
    if(channel_cible==None):
        channel_cible = ctx.channel

    if len(player.consommables) >= CONSO_NUMBER_MAX :
        await channel_cible.send("You have to many consommables. Destroy one to receive the new one.")
        await remove_consommable(ctx=ctx, user=ctx.author, player=player)
    
        if len(player.consommables) >= CONSO_NUMBER_MAX :
            await channel_cible.send("You have too many consommables, the new one is destroyed")

    if len(player.consommables) < CONSO_NUMBER_MAX :
        await channel_cible.send("You receive a new consommable : " + c.name)
        player.consommables.append(c)

async def use_consommable(ctx: Context, user: discord.abc.User, player: 'player_info.Player', session:AsyncSession, bot: Bot, channel_cible=None) :
    if(channel_cible==None):
        channel_cible = ctx.channel

    try :
        bully_selected, _ = await interact_game.player_choose_bully(ctx=ctx, user=user, player=player, bot = bot)
    except asyncio.exceptions.TimeoutError as e:
        await ctx.send(f"Timeout, choose faster next time {user.name}")
        return
    except interact_game.CancelChoiceException as e:
        return
    
    consommable_selected = await select_consommable(ctx=ctx, user=user, player=player, bully_selected=bully_selected, channel_cible=channel_cible)
    if consommable_selected is None:
        await channel_cible.send(content="You didn't selected any consommable")
    else : 
        consommable_selected.apply(bully_selected)
        await channel_cible.send(content="Consommable have been successfully applied")
        player.consommables.remove(consommable_selected)
        await session.delete(consommable_selected)          

async def select_consommable(ctx: Context, user: discord.abc.User, player: 'player_info.Player', bully_selected:Bully|None = None, channel_cible=None, timeout = CHOICE_TIMEOUT) -> Consommable|None:
    if(channel_cible==None):
        channel_cible = ctx.channel
    
    selected_consommable: Consommable|None = None

    if(player.consommables == []):
        await ctx.channel.send(content=f"[{user.mention}] - You don't have any consommables")
        return None

    #On affiche les items accessibles
    # text = str_items(player, compact_print=True)
    text = "```ansi\n Select a consommable to use " + (f"on {bully_selected.name}" if bully_selected is not None else "")
    for c in player.consommables:
        text+= "\n- " + c.get_print()
    text+="```"
        
    #On init les variables
    event = asyncio.Event()
    var:Dict[str, Consommable | None] = {"choix" : None}
    list_choix_name:list[str] = [c.name for c in player.consommables]

    view = interact_game.ViewChoice(user=user, event=event, list_choix=player.consommables, list_choix_name=list_choix_name, variable_pointer=var)
    message_consommable_choix = await channel_cible.send(content=text, view=view)

    #On attend une réponse (et on retourne une erreur si nécessaire avec le timeout)
    try:
        await asyncio.wait_for(event.wait(), timeout=CHOICE_TIMEOUT)
        selected_consommable = var["choix"]
    except Exception as e: 
        print(e)

    return selected_consommable

async def remove_consommable(ctx: Context, user: discord.abc.User, player: 'player_info.Player', channel_cible=None, timeout = CHOICE_TIMEOUT) -> None : 
    if(channel_cible == None):
        channel_cible = ctx.channel

    consommable_selected = await select_consommable(ctx=ctx, user=user, player=player, channel_cible=channel_cible)
    if consommable_selected is not None:
        player.consommables.remove(consommable_selected)
        session = async_object_session(consommable_selected)
        if session is not None:
            await session.delete(consommable_selected)

# async def print_consommables(ctx: Context, player: 'player_info.Player', channel_cible=None):
#     #Par défaut, le channel d'envoie est le channel du contexte
#     if(channel_cible==None):
#         channel_cible = ctx.channel

#     if len(player.consommables) <= 0:
#         text = "```You don't have any consommables. Do ruin to have one```"
#         return text
#     text="```ansi\n Your consommables :"
#     for c in player.consommables:
#         print(c.get_print())
#         print(f"on a {c}")
#         text+= "\n- " + c.get_print()
#     text+="\n\n(!!use_consommable to use one)```"
#     await channel_cible.send(text)


def str_consommables(player:'player_info.Player'):
    if len(player.consommables) <= 0:
        text = "```You don't have any consommables. Do ruin to have one```"
        return text
    text="```ansi\n Your consommables :"
    for c in player.consommables:
        print(c.get_print())
        print(f"on a {c}")
        text+= "\n- " + c.get_print()
    text+="\n\n(!!use_consommable to use one)```"
    return text
