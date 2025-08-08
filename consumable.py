from typing import Optional
from utils.database import Base
from bully import Bully, Stats, Rarity, BULLY_MAX_LEVEL, mise_en_forme_str
from discord.ext.commands import Context, Bot
import discord, asyncio
import interact_game
import player_info
from dataclasses import KW_ONLY, replace, dataclass
from utils.color_str import CText
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy.ext.asyncio.session import async_object_session
import enum
import buffs
from fighting_bully import BuffFight
from utils.embed import create_embed
from all_texts import getText
from utils.language_manager import language_manager_instance

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

    def apply(self, b:Bully, lang:Optional[str] = None):
        raise Exception("Must be implemented")
    
    def get_effect(self, lang:Optional[str] = None) -> str:
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

    def apply(self, b:Bully, lang:Optional[str] = None):
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
            
    
    def get_effect(self, lang:Optional[str] = None) -> str:
        aliment = self.aliment.value
        return getText("consumable_aliment_effect", lang=lang).format(nerf=aliment.stat_nerf, buff=aliment.stat_buff, value=int(self.value))
        
class ConsumableElixirBuff(Consumable):
    __mapper_args__ = {
        "polymorphic_identity": "elixirbuff",
        "polymorphic_load": "selectin"
    }
    __tablename__ = "elixirbuff"

    id: Mapped[int] = mapped_column(ForeignKey("consumable.id"), init=False, primary_key=True)
    buff_tag: Mapped[str]

    def apply(self, b:Bully, lang:Optional[str] = None):
        b.buff_fight_tag = self.buff_tag

    def get_effect(self, lang:Optional[str] = None) -> str:
        try : 
            BuffClass:type[BuffFight] = getattr(buffs, self.buff_tag)
            return f"{BuffClass.description}"
        except Exception:
            return f"ERROR ELIXIR"

class ConsumableWaterLvl(Consumable):
    __mapper_args__ = {
        "polymorphic_identity": "waterlvl",
        "polymorphic_load": "selectin"
    }
    __tablename__ = "waterLVL"

    id: Mapped[int] = mapped_column(ForeignKey("consumable.id"), init=False, primary_key=True)
    val: Mapped[int]
    rarity : Mapped[Rarity]

    def apply(self, b:Bully, lang:Optional[str] = None):
        if self.rarity != b.rarity:
            raise ConsumableUseException(getText("consumable_water_rarity_error", lang=lang).format(water_rarity=self.rarity.name, bully_rarity=b.rarity.name))
        if b.lvl < b.max_level_reached and b.lvl < BULLY_MAX_LEVEL:
            b.lvl += self.val
            b.lvl = min(b.lvl, b.max_level_reached, BULLY_MAX_LEVEL)

    def get_effect(self, lang:Optional[str] = None) -> str:
        return getText("consumable_water_effect", lang=lang).format(name=self.name, rarity=self.rarity.name, value=self.val)
        

#____________________________________________________________________________________________________________________
class ConsumableUseException(Exception):
    def __init__(self, text=""):
        self.text = text
        super().__init__(text)
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

    guild_id = ctx.guild.id if ctx.guild is not None else None
    lang = language_manager_instance.get_server_language(guild_id)

    if len(player.consumables) >= CONSO_NUMBER_MAX:
        await channel_cible.send(getText("consumable_too_many_select", lang=lang))
        await remove_consumable(ctx=ctx, user=ctx.author, player=player)
    
        if len(player.consumables) >= CONSO_NUMBER_MAX:
            await channel_cible.send(getText("consumable_too_many_destroyed", lang=lang))

    if len(player.consumables) < CONSO_NUMBER_MAX:
        await channel_cible.send(getText("consumable_added", lang=lang).format(name=c.name))
        player.consumables.append(c)

async def use_consumable(ctx: Context, user: discord.abc.User, player: 'player_info.Player', session:AsyncSession, bot: Bot, channel_cible=None) :
    if(channel_cible==None):
        channel_cible = ctx.channel

    guild_id = ctx.guild.id if ctx.guild is not None else None
    lang = language_manager_instance.get_server_language(guild_id)

    try :
        bully_selected = await interact_game.select_bully(ctx=ctx, user=user, player=player)
    except asyncio.exceptions.TimeoutError as e:
        await ctx.send(getText("timeout_choose_faster", lang=lang).format(user=user.name))
        return
    except interact_game.CancelChoiceException as e:
        return
    
    consumable_selected = await select_consumable(ctx=ctx, user=user, player=player, bully_selected=bully_selected, channel_cible=channel_cible)
    if consumable_selected is None:
        await channel_cible.send(getText("consumable_no_selection", lang=lang))
    else : 
        try :
            consumable_selected.apply(bully_selected, lang=lang)
        except ConsumableUseException as e:
            await channel_cible.send(content=e.text)
            return
        await channel_cible.send(content=getText("consumable_applied", lang=lang).format(name=consumable_selected.name))
        player.consumables.remove(consumable_selected)
        await session.delete(consumable_selected)          

async def select_consumable(ctx: Context, user: discord.abc.User, player: 'player_info.Player', bully_selected:Bully|None = None, channel_cible=None, timeout = CHOICE_TIMEOUT) -> Consumable|None:
    if(channel_cible==None):
        channel_cible = ctx.channel
    
    selected_consumable: Consumable|None = None

    #On affiche les items accessibles
    embed = embed_consumables(player, user, select=True, guild=ctx.guild)
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

    await message_consumable_choix.delete()
    return selected_consumable

async def remove_consumable(ctx: Context, user: discord.abc.User, player: 'player_info.Player', channel_cible=None, timeout:float = CHOICE_TIMEOUT) -> None : 
    if(channel_cible == None):
        channel_cible = ctx.channel

    consumable_selected = await select_consumable(ctx=ctx, user=user, player=player, channel_cible=channel_cible)
    if consumable_selected is not None:
        player.consumables.remove(consumable_selected)
        await ctx.send(getText("consumable_removed", ctx=ctx).format(name=consumable_selected.name))
        

async def force_add_conso(player: 'player_info.Player', c:Consumable) -> None:
    player.consumables.append(c)



def embed_consumables(player: 'player_info.Player', user: discord.abc.User, *, select=False, guild:Optional[discord.Guild]=None) -> discord.Embed:
    guild_id=guild.id if guild else None
    lang = language_manager_instance.get_server_language(guild_id)
    title = getText("consumable_choose_title", lang=lang) if select else getText("consumable_user_title", lang=lang).format(user=user.display_name)
    description_lines = []

    if not player.consumables:
        description_lines.append(getText("consumable_none", lang=lang))
        footnote = getText("consumable_do_ruin", lang=lang) if not select else None
    else:
        for i, c in enumerate(player.consumables):
            description_lines.append(f"**{i+1}. {c.name}**{c.get_effect(lang=lang)}")

        footnote = None if select else getText("consumable_use_command", lang=lang)

    thumbnail = user.avatar.url if not select and user.avatar is not None else None 
    columns = 2 if len(description_lines) > 5 else 1  # Two-column format if many consumables

    return create_embed(title, description_lines, footnote=footnote, thumbnail=thumbnail, columns=columns)

