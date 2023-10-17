from pathlib import Path
from bully import Bully
import bully
import interact_game
import money
import donjon

import os
import random 
import pickle
import asyncio

from typing import Optional
from typing import List

import discord
from discord.ext.commands import Context

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

async def restock_shop() -> None:
    empty_bullies_shop()
    for k in range(SHOP_MAX_BULLY):
        try:
            b = new_bully_shop(k)
            file_path = Path(f"shop/{k}.pkl")
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "wb") as file:
                pickle.dump(b, file)
        except Exception as e:
            print(e)
            return
        
        file.close()

async def print_shop(ctx: Context, bot) -> None:
    if(is_shop_restocking) :
        await ctx.channel.send(restock_message())
        return
    Bullies_in_shop = load_bullies_shop()
    text = bullies_in_shop_to_text(Bullies_in_shop)
    images = bullies_in_shop_to_images(Bullies_in_shop)
    if images:
        files = [discord.File(image) for image in images]
        shop_msg = await ctx.channel.send(content=text, files=files)
    else:
        shop_msg = await ctx.channel.send(text)
    #shop_msg = await ctx.channel.send(text)

    # Add reaction emotes
    for i in range(len(Bullies_in_shop)):
        if(Bullies_in_shop[i] != None):
            await shop_msg.add_reaction(str(i) + "️⃣")

    purchased_bullies = []

    def check(reaction, user):
        return (str(reaction.emoji) in [str(i) + "️⃣" for i in range(SHOP_MAX_BULLY)] 
                and reaction.message.id == shop_msg.id
                and user.id != bot.user.id)

    try:
        while True :
            if(is_shop_restocking):
                await shop_msg.edit(content=restock_message())
                return
            
            reaction, user = await bot.wait_for('reaction_add', timeout=SHOP_TIMEOUT, check=check)

            # Get the index of the selected item
            item_index = int(str(reaction.emoji)[0])
            if item_index >= len(Bullies_in_shop):
                await ctx.send("Invalid selection.")
                continue
            
            if item_index in purchased_bullies:
                await ctx.send("This bully has already been purchased.")
                continue

            #get the selected bully 
            b = Bullies_in_shop[item_index]

            if b == None:
                await ctx.send("This bully is not available.")
                continue

            # Process the purchase 
            if(money.get_money_user(user.id) >= cout_bully(b)):
                if(ctx.author.id in donjon.ID_joueur_en_donjon):
                    await ctx.channel.send("You can't, you are in a dungeon")
                elif(interact_game.nb_bully_in_team(user_id=user.id) >= interact_game.BULLY_NUMBER_MAX):
                    await ctx.channel.send(f"You can't have more than {interact_game.BULLY_NUMBER_MAX} bullies at the same time")
                else :
                    #La transaction s'effectue. A FAIRE : Créer une fonction buy_bully qui fait ça en bas comme ça c'est plus clair
                    money.give_money(user.id, - cout_bully(b))

                    image_name = os.path.basename(b.get_image_path()).replace(f"{b.associated_number}_", "")

                    b.kill()#On retire l'ancien fichier qui était dans le shop (pour le retirer de la boutique)
                    Bullies_in_shop[item_index] = None
                    await interact_game.add_bully_to_player(ctx, user.id ,b)
                    b.set_image_with_name(image_name)
                    purchased_bullies.append(item_index)
                    text = bullies_in_shop_to_text(Bullies_in_shop)
                    await shop_msg.edit(content=text)
                    await ctx.send(f"{user.mention} has purchased {b.name} for {cout_bully(b)}🩹!")
            else :
                await ctx.send(f"You don't have enough {money.MONEY_ICON} {user} for {b.name} [cost: {cout_bully(b)}{money.MONEY_ICON}]")

    except Exception as e:
        #print(e)
        await shop_msg.edit(content="```Shop is closed. See you again!```")
        #print("time out")

def new_bully_shop(nb) -> Bully:
    rarity = random.choices(list(bully.Rarity), weights=RARITY_DROP_CHANCES)[0]
    name = interact_game.generate_name()
    b = Bully(name[0] + " " + name[1], f"shop/{nb}.pkl", rarity=rarity)
    return b

def load_bullies_shop() -> List[Optional[Bully]]:
    bullies_in_shop:List[Optional[Bully]] = []
    folder_path = Path("shop/")
    for k in range(SHOP_MAX_BULLY):
        file_path = folder_path / f"{k}.pkl"
        if file_path.exists() and file_path.is_file():
            with file_path.open("rb") as file:
                obj = pickle.load(file)
                bullies_in_shop.append(obj)
        else :
            bullies_in_shop.append(None)
    """
    for filename in sorted(os.listdir(folder_path)):
        if filename.endswith(".pkl"):
            file_path = os.path.join(folder_path, filename)
            with open(file_path, "rb") as file:
                obj = pickle.load(file)
                bullies_in_shop.append(obj)
    """
    return bullies_in_shop

def empty_bullies_shop() -> None:
    Bullies_in_shop = load_bullies_shop()
    for k in range(len(Bullies_in_shop)):
        b = Bullies_in_shop[k]
        if(b != None):
            b.kill()

def bullies_in_shop_to_text(Bullies_in_shop) -> str:
    text = "Bullies in the shop : "
    for k in range(len(Bullies_in_shop)) :
        b = Bullies_in_shop[k]
        if(b != None):
            text += "\n___________\n"
            text += b.get_print(compact_print = True)
            text += f"\nPrice : {cout_bully(b)} 🩹"
    text = bully.mise_en_forme_str(text)
    return text

def bullies_in_shop_to_images(Bullies_in_shop:List[Optional[Bully]]) -> List[str]:
    images: List[str] = []
    for k in range(len(Bullies_in_shop)) :
        b = Bullies_in_shop[k]
        if(b != None):
            image_path = b.get_image_path()
            if image_path is not None:
                images.append(image_path)
    
    return images

def cout_bully(b) -> int:
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
        is_shop_restocking = False
        await restock_shop()


def restock_message() -> str:
    return (f"```The shop is restocking. Please wait <{SHOP_CLOSE_WAIT_TIME} seconds```")

