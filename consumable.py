from utils.database import Base
from bully import Bully, Stats
from discord.ext.commands import Context, Bot
import discord
import interact_game
import player_info
import asyncio
from dataclasses import KW_ONLY, replace, dataclass
from utils.color_str import CText
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy.ext.asyncio.session import async_object_session
import enum
import buffs
from fighting_bully import BuffFight

CHOICE_TIMEOUT = 60
CONSO_NUMBER_MAX = 10

class Consumable(Base):
    __mapper_args__ = {
        "polymorphic_on": "type",
        "polymorphic_identity": "consumable"
    }
    __tablename__ = "consumable"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)

    player_id: Mapped[int] = mapped_column(ForeignKey("player.id"), init=False)
    player: Mapped["player_info.Player"] = relationship(back_populates="consumables", init=False, lazy="selectin")

    name: Mapped[str] = mapped_column(String(50))
    type: Mapped[str] = mapped_column(init=False)

    def apply(self, b:Bully):
        raise Exception("Must be implemented")

    def get_print(self) -> CText:
        raise Exception("Must be implemented")


@dataclass(eq=True, frozen=True)
class AlimentType():
    stat_buff: str
    stat_nerf: str


class AlimentEnum(enum.Enum):  
    Gigot = AlimentType("strength", "agility")
    Banane = AlimentType("strength", "lethality")
    Creme = AlimentType("strength", "viciousness")
    Piment = AlimentType("agility", "strength")
    Chocolat = AlimentType("agility", "lethality")
    Meringue = AlimentType("agility", "viciousness")
    Bonbon = AlimentType("lethality", "strength")
    Merguez = AlimentType("lethality", "agility")
    Citron = AlimentType("lethality", "viciousness")
    Bierre = AlimentType("viciousness", "strength")
    Beurre = AlimentType("viciousness", "agility")
    Yaourt = AlimentType("viciousness", "lethality")

    def new_conso(self, value: int) -> "ConsumableAliment":
        return ConsumableAliment(self.name, self, value)

class ConsumableAliment(Consumable):
    __mapper_args__ = {
        "polymorphic_identity": "aliment",
        "polymorphic_load": "selectin"
    }
    __tablename__ = "aliment"

    id: Mapped[int] = mapped_column(ForeignKey("consumable.id"), init=False, primary_key=True)
    aliment: Mapped[AlimentEnum]
    value: Mapped[float]

    def apply(self, b:Bully):
        aliment = self.aliment.value

        # Calculate actual debuff ensuring it doesn't drop below 1
        current_debuffed_stat = getattr(b.stats, aliment.stat_nerf)
        actual_buff = min(self.value, current_debuffed_stat - 1)

        if actual_buff > 0:
            # Apply the debuff
            setattr(b.stats, aliment.stat_nerf, current_debuffed_stat - actual_buff)
            
            # Apply the buff with the actual debuff value as its maximum
            current_buff_value = getattr(b.stats, aliment.stat_buff)
            setattr(b.stats, aliment.stat_buff, current_buff_value + actual_buff)
            
    def get_print(self) -> CText:
        return (
            CText(f"{self.name} : on use, debuff ")
            .red(self.aliment.value.stat_nerf)
            .txt(f" up to {self.value} (min 1) and buff ")
            .blue(self.aliment.value.stat_buff)
            .txt(" by the same amount.")
        )
    
class ConsumableElixirBuff(Consumable):
    __mapper_args__ = {
        "polymorphic_identity": "elixirbuff",
        "polymorphic_load": "selectin"
    }
    __tablename__ = "elixirbuff"

    id: Mapped[int] = mapped_column(ForeignKey("consumable.id"), init=False, primary_key=True)
    buff_tag: Mapped[str]

    def apply(self, b:Bully):
        b.buff_fight_tag = self.buff_tag

    def get_print(self) -> CText:
        BuffClass:type[BuffFight] = getattr(buffs, self.buff_tag)
        return (
            CText().txt(f"Elixir of {self.name}. On use, give a fighting buff : {BuffClass.description}")
        )

#_______________________________________________________________________
#_______________________________________________________________________
#_______________________________________________________________________
#_______________________________________________________________________
#_______________________________________________________________________
#_______________________________________________________________________

async def add_conso_to_player(ctx: Context, player: 'player_info.Player', c:Consumable, channel_cible=None):
    #Par défaut, le channel d'envoie est le channel du contexte
    if(channel_cible==None):
        channel_cible = ctx.channel

    if len(player.consumables) >= CONSO_NUMBER_MAX :
        await channel_cible.send("You have to many consumables. Please select one consumable you own to replace with the new one.")
        await remove_consumable(ctx=ctx, user=ctx.author, player=player)
    
        if len(player.consumables) >= CONSO_NUMBER_MAX :
            await channel_cible.send("You have too many consumables, the new one is destroyed.")

    if len(player.consumables) < CONSO_NUMBER_MAX :
        await channel_cible.send("You receive a new consumable : " + c.name + "!")
        player.consumables.append(c)

async def use_consumable(ctx: Context, user: discord.abc.User, player: 'player_info.Player', session:AsyncSession, bot: Bot, channel_cible=None) :
    if(channel_cible==None):
        channel_cible = ctx.channel

    try :
        bully_selected, _ = await interact_game.player_choose_bully(ctx=ctx, user=user, player=player)
    except asyncio.exceptions.TimeoutError as e:
        await ctx.send(f"Timeout, choose faster next time {user.name}")
        return
    except interact_game.CancelChoiceException as e:
        return
    
    consumable_selected = await select_consumable(ctx=ctx, user=user, player=player, bully_selected=bully_selected, channel_cible=channel_cible)
    if consumable_selected is None:
        await channel_cible.send(content="You didn't select any consumable.")
    else : 
        consumable_selected.apply(bully_selected)
        await channel_cible.send(content=f"Consumable ({consumable_selected.name}) has been successfully applied!")
        player.consumables.remove(consumable_selected)
        await session.delete(consumable_selected)          

async def select_consumable(ctx: Context, user: discord.abc.User, player: 'player_info.Player', bully_selected:Bully|None = None, channel_cible=None, timeout = CHOICE_TIMEOUT) -> Consumable|None:
    if(channel_cible==None):
        channel_cible = ctx.channel
    
    selected_consumable: Consumable|None = None

    #On affiche les items accessibles
    embed = embed_consumables(player, user, select=True)
    if(player.consumables == []):
        await channel_cible.send(embed=embed)
        return None

    #On init les variables
    event = asyncio.Event()
    var: dict[str, Consumable | None] = {"choix" : None}
    list_choix_name: list[str] = [f"{i+1}. {c.name}" for i,c in enumerate(player.consumables)]
    view = interact_game.ViewChoice(user=user, event=event, list_choix=player.consumables, list_choix_name=list_choix_name, variable_pointer=var)

    message_consumable_choix = await channel_cible.send(embed=embed, view=view)

    #On attend une réponse (et on retourne une erreur si nécessaire avec le timeout)
    try:
        await asyncio.wait_for(event.wait(), timeout=CHOICE_TIMEOUT)
        selected_consumable = var["choix"]
    except Exception as e: 
        print(e)

    return selected_consumable

async def remove_consumable(ctx: Context, user: discord.abc.User, player: 'player_info.Player', channel_cible=None, timeout = CHOICE_TIMEOUT) -> None : 
    if(channel_cible == None):
        channel_cible = ctx.channel

    consumable_selected = await select_consumable(ctx=ctx, user=user, player=player, channel_cible=channel_cible)
    if consumable_selected is not None:
        player.consumables.remove(consumable_selected)
        session = async_object_session(consumable_selected)
        if session is not None:
            await session.delete(consumable_selected)



def str_consumables(player: 'player_info.Player') -> CText:
    if len(player.consumables) <= 0:
        text = CText("You don't have any consumables. Do ruin to have one")
        return text
    text = CText("Your consumables :")
    text = CText()
    for c in player.consumables:
        text.txt("\n")
        text += c.get_print()
    text.txt("\n\n(Use !!use_consumable to use one)")
    return text

def embed_consumables(player: 'player_info.Player', user: discord.abc.User, *, select=False) -> discord.Embed:
    embed=discord.Embed(title=f"{user.display_name}'s consumables", color=0x77767b)
    if select: embed.title = "Choose a consumable"
    if not select: embed.set_footer(text="Enter !!use_consumable to use one.")
    if len(player.consumables) == 0:
        embed.description = "You have no consumables :("
        if not select: embed.set_footer(text="But you may get some from ruins!")
    for i,c in enumerate(player.consumables):
        embed.add_field(name=f"{i+1}. {c.name}", value=c.get_print(), inline=not select)
    if user.avatar is not None and not select: embed.set_thumbnail(url=user.avatar.url)
    return embed