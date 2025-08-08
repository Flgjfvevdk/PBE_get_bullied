from pathlib import Path
from bully import Bully
import bully
import interact_game
import money
import donjon
from utils.locks import PlayerLock
import utils.database as database
from player_info import Player
from utils.language_manager import language_manager_instance

import os
import random 
import json
import asyncio

from typing import Optional, Dict
from typing import List

from sqlalchemy.orm import exc

import discord
from discord.ext import tasks
from discord.ext.commands import Context, Bot
from all_texts import getText 
from utils.discord_servers import load_servers

RARITY_DROP_CHANCES = [0, 30, 40, 21, 9, 0] #Mettre 0 en proba d'avoir unique
RARITY_PRICES = [10, 80, 200, 600, 1400]

SHOP_MAX_BULLY = 6
#Le temps pendant lequel le shop reste actif
SHOP_TIMEOUT = 60
SHOP_RESTOCK_TIMEOUT = 10 * 60
#Le temps pendant lequel le shop est fermé pendant le restockage. Les achats sont possibles mais on ne peut pas afficher un nouveau shop 
#(permet d'éviter que quelqu'un affiche le shop alors qu'il change bientot)
SHOP_CLOSE_WAIT_TIME = 1
#Si c'est à True, alors la commande shop n'affiche pas le shop mais un message qui demande d'attendre.
is_shop_restocking = False



# Les bullies disponibles
bullies_in_shop_server : dict[int, List[Bully]] = {}

# On lock le shop lors des modifs pour éviter les conflits
shop_lock = asyncio.Lock()

async def init_shop():
    await restock_shop()
    restock_shop_loop.start()

async def restock_shop() -> None:
    bullies_in_shop_server.clear()
    shop_servers_id = load_shop_servers()
    for server_id in shop_servers_id:
        bullies_in_shop_server[server_id] = []
        for k in range(SHOP_MAX_BULLY):
            b = new_bully_shop()
            bullies_in_shop_server[server_id].append(b)
    

@tasks.loop(seconds=SHOP_RESTOCK_TIMEOUT)
async def restock_shop_loop():
    print("on restock le shop !")
    global is_shop_restocking
    is_shop_restocking = True
    await asyncio.sleep(SHOP_CLOSE_WAIT_TIME)
    await restock_shop()
    print("Restock done !")
    is_shop_restocking = False

async def print_shop(ctx: Context, bot: Bot) -> None:
    guild_id = ctx.guild.id if ctx.guild is not None else None
    lang = language_manager_instance.get_server_language(guild_id)
    
    if ctx.guild is None: #$$
        await ctx.send(getText("shop_dm_error", lang=lang))
        return
    
    if ctx.guild.id not in bullies_in_shop_server : #$$
        await ctx.send(getText("shop_not_open", lang=lang))
        return

    if(is_shop_restocking) :
        await ctx.channel.send(restock_message(lang=lang))
        return
    
    text = bullies_in_shop_to_text(ctx.guild.id, lang=lang)
    images = bullies_in_shop_to_images(ctx.guild.id)

    event = asyncio.Event()
    var:Dict[str, Bully | discord.abc.User| None] = {"choix" : None, "user" : None}
    list_bully: List[Bully] = bullies_in_shop_server[ctx.guild.id]
    if images:
        files = [discord.File(image) for image in images]
        shop_msg = await ctx.channel.send(content=text, files=files, view=interact_game.ViewBullyShop(event=event, list_choix=list_bully, variable_pointer = var))
    else:
        shop_msg = await ctx.channel.send(text)
    
    try:
        while True:
            if(is_shop_restocking):
                await shop_msg.edit(content=restock_message(lang=lang), attachments=[], view=None)
                return
                
            await asyncio.wait_for(event.wait(), timeout=SHOP_TIMEOUT)
            event.clear()
            async with shop_lock:
                await handle_shop_click(ctx=ctx, variable_pointer=var, shop_msg=shop_msg, event=event)

    except Exception as e:
        if not isinstance(e, asyncio.TimeoutError):
            print(e)
        await shop_msg.edit(content="```" + getText("shop_closed_message", lang=lang) + "```", attachments=[], view=None)
        return

async def handle_shop_click(ctx:Context, variable_pointer:Dict[str, Bully | discord.abc.User | None], shop_msg: discord.Message, event:asyncio.Event) -> None:
    guild_id = ctx.guild.id if ctx.guild is not None else None
    lang = language_manager_instance.get_server_language(guild_id)
    
    if(not isinstance(variable_pointer["choix"], Bully) or not isinstance(variable_pointer["user"], discord.abc.User)):
        return
    choix_bully: Bully = variable_pointer["choix"]
    user: discord.abc.User = variable_pointer["user"]

    lock = PlayerLock(user.id)
    if not lock.check():
        await ctx.send(getText("already_in_action", lang=lang))
        return
    with lock:
        async with database.new_session() as session:
            try:
                print(choix_bully)
            except exc.DetachedInstanceError as e:
                await ctx.send(getText("shop_bully_not_available", lang=lang).format(user=user.name))
                return
            player = await session.get(Player, user.id)
            
            if player is None:
                await ctx.send(getText("join", lang=lang))
                return
            if(money.get_money_user(player) < cout_bully(choix_bully)):
                await ctx.send(getText("shop_not_enough_money", lang=lang).format(user=user.name, money_emoji=money.MONEY_EMOJI, bully=choix_bully.name, cost=cout_bully(choix_bully)))
                return

            if(interact_game.nb_bully_in_team(player) >= interact_game.BULLY_NUMBER_MAX):
                await ctx.send(getText("max_bullies_reached", lang=lang).format(user = user.name, max_bullies=interact_game.BULLY_NUMBER_MAX))
                return
            
            money.give_money(player, - cout_bully(choix_bully))
            player.bullies.append(choix_bully)

            if ctx.guild is None: #$$
                raise Exception("On est pas censé être ici. ctx doit être un server pour handle une shop reaction")
            bullies_in_shop_server[ctx.guild.id].remove(choix_bully)
            
            variable_pointer["choix"] = None
            variable_pointer["user"] = None

            text = bullies_in_shop_to_text(ctx.guild.id, lang=lang)
            images = bullies_in_shop_to_images(ctx.guild.id)
            files = [discord.File(image) for image in images]
            await shop_msg.edit(content=text, attachments=files, view=interact_game.ViewBullyShop(event=event, list_choix=bullies_in_shop_server[ctx.guild.id], variable_pointer = variable_pointer))
            await ctx.send(getText("shop_purchase_success", lang=lang).format(user=user.mention, bully=choix_bully.name, cost=cout_bully(choix_bully), money_emoji=money.MONEY_EMOJI))

            await session.commit()

# Charger les serveurs sauvegardés depuis le fichier
def load_shop_servers() -> List[int]:
    return load_servers()
    

def new_bully_shop() -> Bully:
    rarity = random.choices(list(bully.Rarity), weights=RARITY_DROP_CHANCES)[0]
    name = interact_game.generate_name()
    b = Bully(name, rarity=rarity)
    return b

def bullies_in_shop_to_text(server_id, lang: Optional[str] = None) -> str:
    text = getText("bully_in_shop", lang=lang)
    for k in range(len(bullies_in_shop_server[server_id])) :
        b = bullies_in_shop_server[server_id][k]
        text += "\n___________\n"
        text += b.get_print(compact_print = True)
        text += "\n" + getText("price", lang=lang).format(cost=cout_bully(b), money_emoji=money.MONEY_EMOJI)
    text = bully.mise_en_forme_str(text)
    return text

def bullies_in_shop_to_images(server_id) -> List[Path]:
    images: List[Path] = []
    for k in range(len(bullies_in_shop_server[server_id])) :
        b = bullies_in_shop_server[server_id][k]
        image_path = b.image_file_path
        if image_path is not None:
            images.append(image_path)
    
    return images

def cout_bully(b: Bully) -> int:
    r = b.rarity
    return RARITY_PRICES[r.value]

async def restock_shop_automatic() -> None:
    global is_shop_restocking
    print("on commence")
    while(True):    
        await asyncio.sleep(SHOP_RESTOCK_TIMEOUT)
        print("on restock le shop !")
        is_shop_restocking = True
        await asyncio.sleep(SHOP_CLOSE_WAIT_TIME)
        await restock_shop()
        is_shop_restocking = False


def restock_message(lang: Optional[str] = None) -> str:
    return getText("shop_restocking", lang=lang).format(seconds=SHOP_CLOSE_WAIT_TIME)

async def setup_shop_for_server(server_id: int) -> None:
    """Setup shop for a specific server"""
    if server_id not in bullies_in_shop_server:
        bullies_in_shop_server[server_id] = []
        for k in range(SHOP_MAX_BULLY):
            b = new_bully_shop()
            bullies_in_shop_server[server_id].append(b)
        for k in range(SHOP_MAX_BULLY):
            b = new_bully_shop()
            bullies_in_shop_server[server_id].append(b)

