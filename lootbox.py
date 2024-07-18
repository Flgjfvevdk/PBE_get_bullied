from discord.ext.commands import Context, Bot
from discord.abc import User
from discord import Thread
import discord
import utils
import database

from bully import Bully, Rarity #ne pas confondre avec bully (le fichier)
import bully #ne pas confondre avec Bully (la class)

from player_info import Player
import interact_game
import money
import random
import math
import asyncio
from dataclasses import dataclass, field, KW_ONLY

from typing import Dict

CHOICE_TIMEOUT = 20
RARITY_DROP_CHANCES = [0, 35, 50, 10, 5, 0] #Mettre 0 en proba d'avoir unique
PRIX_BASE = 80


def get_cout(level) ->int:
    cout = int(math.sqrt(level) * PRIX_BASE)
    return cout

def loot_bully(level) -> Bully:
    name = interact_game.generate_name()
    rarity = random.choices(list(bully.Rarity), weights=RARITY_DROP_CHANCES)[0]
    b = Bully(name=name, rarity=rarity)
    lvl_bully = int((level+1)/2)
    for k in range(1, lvl_bully):
        b.level_up_one()

    return b
    
    
async def shop_lootbox(ctx: Context, user: discord.abc.User):
    text = f"Select a lootbox to open. You'll get a bully with a level 2 times smaller than the box level."
    event = asyncio.Event()
    var:Dict[str, int | None] = {"choix" : None}
    level_choix = [1, 5, 10, 20, 30, 40, 50]
    list_choix_name:list[str] = []
    for l in (level_choix):
        list_choix_name.append(f"Level {l} ({get_cout(l)}{money.MONEY_ICON})")
    view = interact_game.ViewChoice(user=user, event=event, list_choix=level_choix, list_choix_name= list_choix_name, variable_pointer = var)
    shop_lb_msg = await ctx.channel.send(content=text, view=view)

    #On attend une réponse (et on retourne une erreur si nécessaire avec le timeout)
    try:
        await asyncio.wait_for(event.wait(), timeout=CHOICE_TIMEOUT)
        box_lvl = var["choix"]
        if(box_lvl):
            await open_lootbox(ctx, user, box_lvl)
    except Exception as e: 
        print(e)
    finally:
        await shop_lb_msg.delete()

async def open_lootbox(ctx: Context, user: discord.abc.User, level:int):
    if user.id in utils.players_in_interaction:
        await ctx.send("You are already in an action.")
        return
    
    async with database.new_session() as session:
        player = await session.get(Player, user.id)

        if player is None:
            await ctx.send("Please join the game first !")
            return
        
        max_dungeon_lvl:int = player.max_dungeon
        if level > max_dungeon_lvl and level > 1:
            await ctx.send(f"{user.name}, you must beat dungeon level {level} to buy this lootbox")
            return

        cout = get_cout(level=level)
        if(money.get_money_user(player) < cout):
            await ctx.send(f"{user.name}, you don't have enough {money.MONEY_ICON} for this box [cost: {cout}{money.MONEY_ICON}]")
            return

        if(interact_game.nb_bully_in_team(player) >= interact_game.BULLY_NUMBER_MAX):
            await ctx.channel.send(f"{user.name}, you can't have more than {interact_game.BULLY_NUMBER_MAX} bullies at the same time")
            return
        
        money.give_money(player, - cout)
        b:Bully = loot_bully(level)
        player.bullies.append(b)
        
        text_lootbox = bully.mise_en_forme_str(f"{user.name} has purchased a lootbox and got ... {b.name} a {b.rarity.name}!")
        await ctx.channel.send(text_lootbox)
        await session.commit()
    
    b = loot_bully(level=level)
    await interact_game.add_bully_to_player(ctx = ctx, player=player, b=b)