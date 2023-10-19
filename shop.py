from pathlib import Path
from bully import Bully
import bully
import interact_game
import money
import donjon
import utils
import database
from player_info import Player

from discord.ext import tasks

import os
import random 
import pickle
import asyncio

from typing import Optional
from typing import List

import discord
from discord.ext.commands import Context, Bot

RARITY_DROP_CHANCES = [0, 50, 35, 14, 1]
RARITY_PRICES = [30, 80, 200, 600, 1000]

SHOP_MAX_BULLY = 5
#Le temps pendant lequel le shop reste actif
SHOP_TIMEOUT = 30 
#Le temps entre chaque restock
SHOP_RESTOCK_TIMEOUT = 10 * 60
#Le temps pendant lequel le shop est fermé pendant le restockage. Les achats sont possibles mais on ne peut pas afficher un nouveau shop 
#(permet d'éviter que quelqu'un affiche le shop alors qu'il change bientot)
SHOP_CLOSE_WAIT_TIME = 30 #doit être > à SHOP_TIMEOUT (sinon quelqu'un pourrait acheter un truc qu'il veut pas)
#Si c'est à True, alors la commande shop n'affiche pas le shop mais un message qui demande d'attendre.
is_shop_restocking = False

# Les bullies disponibles
bullies_in_shop: dict[int,Bully] = {}

# On lock le shop lors des modifs pour éviter les conflits
shop_lock = asyncio.Lock()

async def restock_shop() -> None:
    bullies_in_shop.clear()
    for k in range(SHOP_MAX_BULLY):
        b = new_bully_shop()
        bullies_in_shop[k] = b

async def init_shop():
    await restock_shop()
    restock_shop_loop.start()

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
    if(is_shop_restocking) :
        await ctx.channel.send(restock_message())
        return
    
    text = bullies_in_shop_to_text()
    images = bullies_in_shop_to_images()
    if images:
        files = [discord.File(image) for image in images]
        shop_msg = await ctx.channel.send(content=text, files=files)
    else:
        shop_msg = await ctx.channel.send(text)
    
    # Add reaction emotes
    for i in bullies_in_shop:
        await shop_msg.add_reaction(str(i) + "️⃣")

    def check(reaction: discord.Reaction, user: discord.abc.User):
        return (str(reaction.emoji) in [str(i) + "️⃣" for i in range(SHOP_MAX_BULLY)] 
                and reaction.message.id == shop_msg.id
                and user.id != bot.user.id) #type: ignore (on sait que le bot est co TT)

    try:
        while True:
            if(is_shop_restocking):
                await shop_msg.edit(content=restock_message())
                return
        
            reaction, user = await bot.wait_for('reaction_add', timeout=SHOP_TIMEOUT, check=check)
            async with shop_lock:
                await handle_shop_reaction(ctx, reaction, user, shop_msg)

    except Exception as e:
        if not isinstance(e, asyncio.TimeoutError):
            print(e)
        await shop_msg.edit(content="```Shop is closed. See you again!```", attachments=[])
        return

async def handle_shop_reaction(ctx: Context, reaction: discord.Reaction, user: discord.abc.User, shop_msg: discord.Message):
    if user.id in utils.players_in_interaction:
        await ctx.send("You are already in an action.")
    utils.players_in_interaction.add(user.id)

    # Get the index of the selected item
    item_index = int(str(reaction.emoji)[0])
    if not (0 <= item_index <= len(bullies_in_shop)):
        await ctx.send("Invalid selection.")
        return
    
    elif item_index not in bullies_in_shop:
        await ctx.send("This bully has already been purchased.")
        return

    #get the selected bully 
    b = bullies_in_shop[item_index]
    
    # Process the purchase 
    async with database.new_session() as session:
        player = await session.get(Player, user.id)
        if player is None:
            await ctx.send("Please join the game first !")
            return
        if(money.get_money_user(player) < cout_bully(b)):
            await ctx.send(f"You don't have enough {money.MONEY_ICON} {user} for {b.name} [cost: {cout_bully(b)}{money.MONEY_ICON}]")
            return
    
        if(interact_game.nb_bully_in_team(player) >= interact_game.BULLY_NUMBER_MAX):
            await ctx.channel.send(f"You can't have more than {interact_game.BULLY_NUMBER_MAX} bullies at the same time")
            return
        
        money.give_money(player, - cout_bully(b))
        player.bullies.append(b)
        del bullies_in_shop[item_index]
        await session.commit()

        text = bullies_in_shop_to_text()
        await shop_msg.edit(content=text)
        await ctx.send(f"{user.mention} has purchased {b.name} for {cout_bully(b)}🩹!")

    utils.players_in_interaction.discard(ctx.author.id)

def new_bully_shop() -> Bully:
    rarity = random.choices(list(bully.Rarity), weights=RARITY_DROP_CHANCES)[0]
    name = interact_game.generate_name()
    b = Bully(name[0] + " " + name[1], rarity=rarity)
    return b

def bullies_in_shop_to_text() -> str:
    text = "Bullies in the shop : "
    for k in bullies_in_shop :
        b = bullies_in_shop[k]
        text += "\n___________\n"
        text += b.get_print(compact_print = True)
        text += f"\nPrice : {cout_bully(b)} 🩹"
    text = bully.mise_en_forme_str(text)
    return text

def bullies_in_shop_to_images() -> List[Path]:
    images: List[Path] = []
    for k in bullies_in_shop :
        b = bullies_in_shop[k]
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

