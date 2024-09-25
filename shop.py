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


RARITY_DROP_CHANCES = [0, 25, 45, 20, 10, 0] #Mettre 0 en proba d'avoir unique
RARITY_PRICES = [10, 80, 200, 600, 1400]

SHOP_MAX_BULLY = 6
#Le temps pendant lequel le shop reste actif
SHOP_TIMEOUT = 60
#Le temps entre chaque restock
SHOP_RESTOCK_TIMEOUT = 10 * 60
#Le temps pendant lequel le shop est fermé pendant le restockage. Les achats sont possibles mais on ne peut pas afficher un nouveau shop 
#(permet d'éviter que quelqu'un affiche le shop alors qu'il change bientot)
SHOP_CLOSE_WAIT_TIME = 1 #30 #doit être > à SHOP_TIMEOUT (sinon quelqu'un pourrait acheter un truc qu'il veut pas)
#Si c'est à True, alors la commande shop n'affiche pas le shop mais un message qui demande d'attendre.
is_shop_restocking = False

SHOP_SERVER_FILENAME = 'shop_servers.json'

server_shops: dict[int, Shop] = {}

async def init_shop():
    for server_id in load_shop_servers(SHOP_SERVER_FILENAME):
        server_shops[server_id] = Shop(server_id)
    restock_shop_loop.start()

async def restock_shop(server_id: int) -> None:
    await server_shops[server_id].restock_shop()

@tasks.loop(seconds=SHOP_RESTOCK_TIMEOUT)
async def restock_shop_loop():
    print("on restock les shops !")
    #await asyncio.sleep(SHOP_CLOSE_WAIT_TIME)
    for server_id in server_shops:
        await restock_shop(server_id)
    print("Restock done !")

class Shop():
    lock = asyncio.Lock()
    bullies: list[Bully]
    server_id: int
    shop_msg: discord.Message | None
    shop_msg_view: discord.View | None

    def __init__(self, server_id: int):
        self.server_id = server_id

    async def restock_shop(self):
        async with self.lock:
            await self.close(reason = "restocking")
            self.bullies.clear()
            for k in range(SHOP_MAX_BULLY):
                b = new_bully_shop()
                self.bullies.append(b)

    async def close(self, *, reason: str|None = None):
        async with self.lock:
            self.shop_msg_view.stop()
            close_txt = f"```Shop is closed. {("(reason: " + reason+").") if reason else ""} See you again!```"
            await self.shop_msg.edit(content=close_txt, attachments=[], view=None)
            self.shop_msg = None
            self.shop_msg_view = None

    async def print(self, channel: discord.abc.PartialMessageableChannel):
        if self.shop_msg is not None:
            channel.send(f"Shop is already opened, [click here to access it]({self.shop_msg.url})",
                delete_after=15)
        if(is_shop_restocking) :
            await ctx.channel.send(restock_message())
            return
        
        text = self.bullies_in_shop_to_text()
        images = self.bullies_in_shop_to_images()

        list_bully: List[Bully] = bullies_in_shop_server[ctx.guild.id]
        files = None
        view = interact_game.ViewBullyShop(list_choix=list_bully)
        self.shop_msg_view.on_timeout = self.close
        if images:
            files = [discord.File(image) for image in images]
        
        shop_msg = await ctx.channel.send(content=text, files=files, view=view)
        shop_msg_view = view

    async def button_click_callback(self, interaction: discord.Interaction, choice: Bully):
        async with self.lock:
            await interaction.response.defer()
            await self.handle_shop_click(interaction.channel, interaction.user, choice)


    async def handle_shop_click(self, ctx:discord.abc.PartialMessageableChannel, user: discord.abc.User, bully: Bully) -> None:
        lock = PlayerLock(user.id)
        if not lock.check():
            await ctx.send("You are already in an action.")
            return
        with lock:
            async with database.new_session() as session:
                try:
                    print(bully)
                except exc.DetachedInstanceError as e:
                    await ctx.send(f"This bully is no longer available (sorry {user.name})")
                    return
                player = await session.get(Player, user.id)
                
                if player is None:
                    await ctx.send("Please join the game first !")
                    return
                if(money.get_money_user(player) < cout_bully(bully)):
                    await ctx.send(f"You don't have enough {money.MONEY_ICON} {user} for {bully.name} [cost: {cout_bully(bully)}{money.MONEY_ICON}]")
                    return

                if(interact_game.nb_bully_in_team(player) >= interact_game.BULLY_NUMBER_MAX):
                    await ctx.channel.send(f"You can't have more than {interact_game.BULLY_NUMBER_MAX} bullies at the same time")
                    return
                
                money.give_money(player, - cout_bully(bully))
                player.bullies.append(bully)

                if ctx.guild is None:
                    raise Exception("On est pas censé être ici. ctx doit être un server pour handle une shop reaction")

                self.bullies.remove(bully)
                await session.commit()

            list_bully: List[Bully] = bullies_in_shop_server[ctx.guild.id]
            view = interact_game.ViewBullyShop(list_choix=list_bully)
            self.shop_msg_view.on_timeout = self.close
            files = None
            if images:
                files = [discord.File(image) for image in images]
            await shop_msg.edit(content=text, attachments=files, view=view)
            await ctx.channel.send(f"{user.mention} has purchased {bully.name} for {cout_bully(bully)}🩹!")


    def bullies_in_shop_to_text(self) -> str:
        text = "Bullies in the shop :"
        for b in self.bullies:
            text += "\n___________\n"
            text += b.get_print(compact_print = True)
            text += f"\nPrice : {cout_bully(b)} 🩹"
        text = bully.mise_en_forme_str(text)
        return text

    def bullies_in_shop_to_images(self) -> List[Path]:
        images: List[Path] = []
        for b in self.bullies:
            image_path = b.image_file_path
            if image_path is not None:
                images.append(image_path)
        return images

async def print_shop(ctx: Context) -> None:
    if ctx.guild is None:
        ctx.reply("You cannot use this here.")
    
    await server_shops[ctx.guild.id].print_shop(ctx.channel)


# Charger les serveurs sauvegardés depuis le fichier
def load_shop_servers():
    try:
        with open(SHOP_SERVER_FILENAME, 'r') as f:
            shop_servers_id = json.load(f)
    except FileNotFoundError:
        shop_servers_id = []
    return shop_servers_id

def save_shop_server(servers):
    # Save in file
    with open(SHOP_SERVER_FILENAME, 'w') as f:
        json.dump(servers, f, indent=4)

async def add_new_shop(server_id: int, /, *, restock = True):
    newshop = Shop(server_id)
    if restock:
        await newshop.restock_shop()
    server_shops[server_id] = newshop

def new_bully_shop() -> Bully:
    rarity = random.choices(list(bully.Rarity), weights=RARITY_DROP_CHANCES)[0]
    name = interact_game.generate_name()
    b = Bully(name, rarity=rarity)
    return b

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

