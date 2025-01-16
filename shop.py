from pathlib import Path
from bully import Bully
import bully
import interact_game
import money
import donjon
from utils.locks import PlayerLock
import utils.database as database
from player_info import Player

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

SHOP_SERVER_FILENAME = 'discord_servers.json'


# Les bullies disponibles
bullies_in_shop_server : dict[int, List[Bully]] = {}

# On lock le shop lors des modifs pour éviter les conflits
shop_lock = asyncio.Lock()

async def init_shop():
    await restock_shop()
    restock_shop_loop.start()

async def restock_shop() -> None:
    # bullies_in_shop.clear()
    # for k in range(SHOP_MAX_BULLY):
    #     b = new_bully_shop()
    #     bullies_in_shop.append(b)
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
    if ctx.guild is None: #$$
        await ctx.send('This command can only be used in a server, not in a DM.')
        return
    
    if ctx.guild.id not in bullies_in_shop_server : #$$
        await ctx.send('The shop is not open in this server. Ask an admin to open it.')
        return

    if(is_shop_restocking) :
        await ctx.channel.send(restock_message())
        return
    
    text = bullies_in_shop_to_text(ctx.guild.id)
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
                await shop_msg.edit(content=restock_message(), attachments=[], view=None)
                return
                
            await asyncio.wait_for(event.wait(), timeout=SHOP_TIMEOUT)
            event.clear()
            async with shop_lock:
                await handle_shop_click(ctx=ctx, variable_pointer=var, shop_msg=shop_msg, event=event)

    except Exception as e:
        if not isinstance(e, asyncio.TimeoutError):
            print(e)
        await shop_msg.edit(content="```Shop is closed. See you again!```", attachments=[], view=None)
        return

async def handle_shop_click(ctx:Context, variable_pointer:Dict[str, Bully | discord.abc.User | None], shop_msg: discord.Message, event:asyncio.Event) -> None:
    if(not isinstance(variable_pointer["choix"], Bully) or not isinstance(variable_pointer["user"], discord.abc.User)):
        return
    choix_bully: Bully = variable_pointer["choix"]
    user: discord.abc.User = variable_pointer["user"]


    lock = PlayerLock(user.id)
    if not lock.check():
        await ctx.send("You are already in an action.")
        return
    with lock:
        async with database.new_session() as session:
            try:
                print(choix_bully)
            except exc.DetachedInstanceError as e:
                await ctx.send(f"This bully is no longer available (sorry {user.name})")
                return
            player = await session.get(Player, user.id)
            
            if player is None:
                await ctx.send("Please join the game first !")
                return
            if(money.get_money_user(player) < cout_bully(choix_bully)):
                await ctx.send(f"You don't have enough {money.MONEY_ICON} {user} for {choix_bully.name} [cost: {cout_bully(choix_bully)}{money.MONEY_ICON}]")
                return

            if(interact_game.nb_bully_in_team(player) >= interact_game.BULLY_NUMBER_MAX):
                await ctx.channel.send(f"You can't have more than {interact_game.BULLY_NUMBER_MAX} bullies at the same time")
                return
            
            money.give_money(player, - cout_bully(choix_bully))
            player.bullies.append(choix_bully)

            if ctx.guild is None: #$$
                raise Exception("On est pas censé être ici. ctx doit être un server pour handle une shop reaction")
            bullies_in_shop_server[ctx.guild.id].remove(choix_bully)
            
            variable_pointer["choix"] = None
            variable_pointer["user"] = None

            text = bullies_in_shop_to_text(ctx.guild.id)
            images = bullies_in_shop_to_images(ctx.guild.id)
            files = [discord.File(image) for image in images]
            await shop_msg.edit(content=text, attachments=files, view=interact_game.ViewBullyShop(event=event, list_choix=bullies_in_shop_server[ctx.guild.id], variable_pointer = variable_pointer))
            await ctx.channel.send(f"{user.mention} has purchased {choix_bully.name} for {cout_bully(choix_bully)}🩹!")

            await session.commit()

# Charger les serveurs sauvegardés depuis le fichier
def load_shop_servers():
    try:
        with open(SHOP_SERVER_FILENAME, 'r') as f:
            shop_servers_id = json.load(f)
    except FileNotFoundError:
        shop_servers_id = []
    return shop_servers_id

def save_shop_server(servers):
    with open(SHOP_SERVER_FILENAME, 'w') as f:
        json.dump(servers, f, indent=4)

def new_bully_shop() -> Bully:
    rarity = random.choices(list(bully.Rarity), weights=RARITY_DROP_CHANCES)[0]
    name = interact_game.generate_name()
    b = Bully(name, rarity=rarity)
    return b

def bullies_in_shop_to_text(server_id) -> str:
    text = "Bullies in the shop : "
    for k in range(len(bullies_in_shop_server[server_id])) :
        b = bullies_in_shop_server[server_id][k]
        text += "\n___________\n"
        text += b.get_print(compact_print = True)
        text += f"\nPrice : {cout_bully(b)} 🩹"
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


def restock_message() -> str:
    return (f"```The shop is restocking. Please wait <{SHOP_CLOSE_WAIT_TIME} seconds```")

