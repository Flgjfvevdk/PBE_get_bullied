import os
from bully import Bully
import bully
from player_info import Player
import interact_game
from utils.language_manager import language_manager_instance

from pathlib import Path

import discord
from discord.ext.commands import Context, Bot
from typing import Optional, List, Dict, TypeVar, Generic
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
import asyncio
from utils.locks import PlayerLock
from all_texts import getText

MAX_BULLY_RESERVE = 10
TIMEOUT_RESERVE_MODIF = 60


async def add_bully_reserve(ctx: Context, player: Player, b: Bully, channel_cible=None) -> None:
    #Par défaut, le channel d'envoie est le channel du contexte
    if(channel_cible==None):
        channel_cible = ctx.channel
        
    if len(player.get_reserve()) >= MAX_BULLY_RESERVE:
        await channel_cible.send(getText("reserve_max_bullies", ctx=ctx).format(max_reserve=MAX_BULLY_RESERVE))
        return
    b.in_reserve = True
    player.bullies.append(b)

    await channel_cible.send(getText("new_bully_reserve", ctx=ctx).format(bully=b.name))

async def switch_reserve(ctx: Context, player: Player, b: Bully, go_reserve:bool, channel_cible=None) -> None :
    #Par défaut, le channel d'envoie est le channel du contexte
    if(channel_cible==None):
        channel_cible = ctx.channel
    
    guild_id = ctx.guild.id if ctx.guild is not None else None
    lang = language_manager_instance.get_server_language(guild_id)
    
    nb_empty_space = MAX_BULLY_RESERVE - len(player.get_reserve()) if go_reserve else interact_game.BULLY_NUMBER_MAX - len(player.get_equipe())
    
    if nb_empty_space > 0:
        #On fait le switch
        b.in_reserve = go_reserve
        await channel_cible.send(getText("bully_moved", lang=lang).format(bully=b.name, target=(getText("reserve", lang=lang) if go_reserve else getText("active_team", lang=lang))))

    else :
        await channel_cible.send(getText("team_full", lang=lang).format(target=(getText("reserve", lang=lang) if go_reserve else getText("active_team", lang=lang))))


async def print_reserve(ctx: Context, user: discord.abc.User, player: Player, bot: Bot, session:AsyncSession, compact_print=False, print_images=False, channel_cible=None) -> None:
    #Par défaut, le channel d'envoie est le channel du contexte
    if(channel_cible==None):
        channel_cible = ctx.channel

    guild_id = ctx.guild.id if ctx.guild is not None else None
    lang = language_manager_instance.get_server_language(guild_id)

    text = getText("reserve_bullies_info", lang=lang).format(user=user.name)
    split_txt = []

    for b in player.get_reserve():
        text += "\n___________\n"
        text += b.get_print(compact_print=compact_print)
        split_txt.append(bully.mise_en_forme_str(b.get_print(compact_print=compact_print)))
        
    text = bully.mise_en_forme_str(text)

    #On init les variables
    event = asyncio.Event()
    var:Dict[str, int | None] = {"choix" : None}
    view = interact_game.ViewChoice(user=user, event=event, list_choix=[0,1,2], 
                    list_choix_name=[getText("label_send_reserve", lang=lang), getText("label_send_team", lang=lang), getText("label_switch_team_reserve", lang=lang)], variable_pointer=var)

    from utils.embed import create_embed
    message_reserve = await channel_cible.send(embed=create_embed("Your bullies in reserve", split_txt, columns=1, str_between_element=""), view=view)

    try:
        #On attend une réponse (et on retourne une erreur si nécessaire avec le timeout)
        await asyncio.wait_for(event.wait(), timeout=TIMEOUT_RESERVE_MODIF)

        int_selected = var["choix"]
        if(int_selected is None) : 
            raise interact_game.CancelChoiceException("Cancel")
        user = ctx.author
        lock = PlayerLock(user.id)
        if not lock.check():
            await ctx.reply(getText("already_in_action", lang=lang))
            return
        with lock:
            try:
                if int_selected == 0:
                    bully_selected = await interact_game.select_bully(ctx=ctx, user=user, player=player)
                    await switch_reserve(ctx, player, bully_selected, go_reserve=True)
                elif int_selected == 1 :
                    bully_selected = await interact_game.select_bully(ctx=ctx, user=user, player=player, from_team=False)
                    await switch_reserve(ctx, player, bully_selected, go_reserve=False)
                else : 
                    bully_team = await interact_game.select_bully(ctx=ctx, user=user, player=player, from_team=True)
                    bully_reserve = await interact_game.select_bully(ctx=ctx, user=user, player=player, from_team=False)
                    bully_team.in_reserve = True
                    bully_reserve.in_reserve = False
                    await channel_cible.send(getText("reserve_switch_bullies", lang=lang).format(bully1=bully_team.name, bully2=bully_reserve.name))
                await message_reserve.delete()
                await session.commit()
            except IndexError as e:
                await channel_cible.send(getText("empty_team_or_reserve", lang=lang))
            except Exception as e:
                await message_reserve.edit(view=None)
        
    except Exception as e:
        await message_reserve.edit(view=None)
    
    return

