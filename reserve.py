
import os
from bully import Bully
import bully
from player_info import Player
import interact_game

from pathlib import Path

import discord
from discord.ext.commands import Context, Bot
from typing import Optional, List, Dict, TypeVar, Generic
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
import asyncio
import utils

MAX_BULLY_RESERVE = 3
TIMEOUT_RESERVE_MODIF = 60


async def add_bully_reserve(ctx: Context, player: Player, b: Bully, channel_cible=None) -> None:
    #Par défaut, le channel d'envoie est le channel du contexte
    if(channel_cible==None):
        channel_cible = ctx.channel
        
    if len(player.get_reserve()) >= 3:
        await channel_cible.send(f"You cannot have more than {3} bullies!")
        return
    b.in_reserve = True
    player.bullies.append(b)

    await channel_cible.send("You have a new bully in reserve : " + b.name)   

async def switch_reserve(ctx: Context, player: Player, b: Bully, go_reserve:bool, channel_cible=None) -> None :
    #Par défaut, le channel d'envoie est le channel du contexte
    if(channel_cible==None):
        channel_cible = ctx.channel
    
    nb_empty_space = MAX_BULLY_RESERVE - len(player.get_reserve()) if go_reserve else interact_game.BULLY_NUMBER_MAX - len(player.get_equipe())
    
    if nb_empty_space > 0:
        #On fait le switch
        b.in_reserve = go_reserve
        await channel_cible.send(f"{b.name} have been moved in your {'reserve' if go_reserve else 'active team'}")  

    else :
        await channel_cible.send(f"Your {'reserve' if go_reserve else 'active team'} is already full") 


async def print_reserve(ctx: Context, user: discord.abc.User, player: Player, bot: Bot, session:AsyncSession, compact_print=False, print_images=False, channel_cible=None) -> None:
    #Par défaut, le channel d'envoie est le channel du contexte
    if(channel_cible==None):
        channel_cible = ctx.channel

    text = f"{user}, your bullies in reserve:"
    images: list[Path] = []

    for b in player.get_reserve():
        text += "\n___________\n"
        text += b.get_print(compact_print=compact_print)
        if print_images:
            image_path = b.image_file_path
            image_path_str = str(image_path).replace("\\", "/")
            if image_path is not None and os.path.isfile(image_path_str):
                images.append(Path(image_path_str))
            else : 
                images.append(bully.BULLY_DEFAULT_PATH_IMAGE)
        
    text = bully.mise_en_forme_str(text)

    #On init les variables
    event = asyncio.Event()
    var:Dict[str, int | None] = {"choix" : None}
    view = interact_game.ViewChoice(user=user, event=event, list_choix=[0,1,2], list_choix_name=["Send bully to reserve", "Send bully to team", "Switch team and reserve"], variable_pointer=var)

    if print_images and images:
        files = [discord.File(image) for image in images]
        message_reserve = await channel_cible.send(content=text, files=files, view=view)
    else:
        message_reserve = await channel_cible.send(text, view=view)

    try:
        #On attend une réponse (et on retourne une erreur si nécessaire avec le timeout)
        await asyncio.wait_for(event.wait(), timeout=TIMEOUT_RESERVE_MODIF)

        #On sélectionne le bully et on crée un FightingBully
        int_selected = var["choix"]
        if(int_selected is None) : 
            raise interact_game.CancelChoiceException("Cancel")
        if user.id in utils.players_in_interaction:
            await ctx.reply(f"You are already in an interaction.")
            return
        
        utils.players_in_interaction.add(user.id)
        try :
            if int_selected == 0:
                bully_selected, _ = await interact_game.player_choose_bully(ctx=ctx, user=user, player=player, bot = bot)
                await switch_reserve(ctx, player, bully_selected, go_reserve=True)
            elif int_selected == 1 :
                bully_selected, _ = await interact_game.player_choose_bully(ctx=ctx, user=user, player=player, bot = bot, from_team=False)
                await switch_reserve(ctx, player, bully_selected, go_reserve=False)
            else : 
                bully_team, _ = await interact_game.player_choose_bully(ctx=ctx, user=user, player=player, bot = bot, from_team=True)
                bully_reserve, _ = await interact_game.player_choose_bully(ctx=ctx, user=user, player=player, bot = bot, from_team=False)
                bully_team.in_reserve = True
                bully_reserve.in_reserve = False
                await channel_cible.send(f"{bully_team.name} and {bully_reserve.name} switched")  
            await session.commit()
        except Exception as e:
            await message_reserve.edit(view=None)
        finally:
            utils.players_in_interaction.discard(user.id)
        
    except Exception as e:
        await message_reserve.edit(view=None)
    
    return