import os
import random
import pickle
import money
from bully import Bully
import bully
from item import Item
import item
from player_info import Player

from pathlib import Path
from typing import Optional, List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

import fight_manager # ##$$$
from fighting_bully import FightingBully
import utils

import discord
from discord.ext.commands import Context, Bot

BULLY_NUMBER_MAX = 5
CHOICE_TIMEOUT = 20

async def join_game(ctx: Context, session: AsyncSession, channel_cible: Optional[discord.abc.Messageable]=None) -> None:
    # Par défaut, le channel d'envoie est le channel du contexte
    if(channel_cible==None):
        channel_cible = ctx.channel
    
    player = Player(money.MONEY_JOIN_VALUE)
    player.id = ctx.author.id
    try:
        session.add(player)
        await session.commit()
    except IntegrityError:
        await ctx.reply("You have already joined the game!\n"
                  "(if you think this is an error, please contact an administrator)")
        return

    await ctx.reply("Welcome to the adventure !")
    return 

async def add_random_bully_to_player(ctx: Context, player: Player, name_brute: list[str], channel_cible=None) -> None:

    name_bully = f"{name_brute[0]} {name_brute[1]}"
    new_bully = Bully(name_bully)

    await add_bully_to_player(ctx, player, new_bully, channel_cible)

async def add_bully_to_player(ctx: Context, player: Player, b: Bully, channel_cible=None) -> None:
    #Par défaut, le channel d'envoie est le channel du contexte
    if(channel_cible==None):
        channel_cible = ctx.channel

    if len(player.bullies) >= BULLY_NUMBER_MAX:
        await channel_cible.send(f"You cannot have more than {BULLY_NUMBER_MAX} bullies!")
        return
    
    player.bullies.append(b)

    await channel_cible.send("You have a new bully : " + b.name)   

async def add_item_to_player(ctx: Context, player: Player, i: Item, channel_cible=None) -> None:
    #Par défaut, le channel d'envoie est le channel du contexte
    if(channel_cible==None):
        channel_cible = ctx.channel

    player.items.append(i)

    await channel_cible.send("You have a new item : " + i.name)

async def print_bullies(ctx: Context, player: Player, compact_print=False, print_images=False, channel_cible=None) -> None:
    #Par défaut, le channel d'envoie est le channel du contexte
    if(channel_cible==None):
        channel_cible = ctx.channel

    
    text = "Your bullies:"
    images: list[Path] = []

    for b in player.bullies:
        text += "\n___________\n"
        text += b.get_print(compact_print=compact_print)
        if print_images:
            image_path = b.image_file_path
            if image_path is not None:
                images.append(image_path)

    try:
        text = bully.mise_en_forme_str(text)
    except Exception as e:
        print(e)

    if print_images:
        if images:
            files = [discord.File(image) for image in images]
            await channel_cible.send(content=text, files=files)
        else:
            await channel_cible.send(text)
    else:
        await channel_cible.send(text)
    return

async def print_items(ctx: Context, player: Player, compact_print=False, channel_cible=None) -> None:
    #Par défaut, le channel d'envoie est le channel du contexte
    if(channel_cible==None):
        channel_cible = ctx.channel

    text = "Your items:"

    for i in player.items:
        text += "\n___________\n"
        text += i.print(compact_print=compact_print)

    text = item.mise_en_forme_str(text)
    await channel_cible.send(text)
    return

async def player_choose_bully(ctx: Context, user: discord.abc.User, player: Player, bot: Bot, channel_cible=None, timeout = CHOICE_TIMEOUT) -> tuple[FightingBully, int]:
    '''Il faut try catch cette méthode car elle peut raise une exception en cas de timeout !!!
    '''
    if(channel_cible == None):
        channel_cible = ctx.channel

    #Demande au joueur de choisir son combattant
    message_choose_fighter = await channel_cible.send(f"{user} choose your fighter : ") 
    await print_bullies(ctx, player, compact_print = True, channel_cible= channel_cible)
    for k in range(len(player.bullies)):
        await message_choose_fighter.add_reaction(fight_manager.from_number_to_emote(k))

    #On attend le choix du joueur
    try : 
        reaction, _ = await bot.wait_for("reaction_add", check=fight_manager.check_reaction_number(user, message_choose_fighter), timeout=timeout)
        bully_number = fight_manager.from_emote_to_number(reaction.emoji)
    except Exception as e:
        raise TimeoutError("Timeout choose bully delay")
    
    #On a récup le bully associé au choix du joueur
    try:
        bully_selected = player.bullies[bully_number]
    except Exception as e:
        raise IndexError("Player don't have this bully")
    
    await channel_cible.send(f"{user} sends {bully_selected.name} to fight") 
    
    fighting_bully = FightingBully.create_fighting_bully(bully_selected)
    
    return fighting_bully, bully_number

async def player_choose_item(ctx: Context, user: discord.abc.User, player: Player, bot: Bot, channel_cible=None, timeout = CHOICE_TIMEOUT) -> Optional[Item]:
    if(channel_cible==None):
        channel_cible = ctx.channel

    item:Optional[Item] = None

    text_ask_item = f"{user.mention}, do you want to equip an item?"
    message = await channel_cible.send(text_ask_item)
    await message.add_reaction("✅")
    await message.add_reaction("❌")
    try:
        reaction, _ = await bot.wait_for("reaction_add", check=fight_manager.check_reaction_yes_no(user, message), timeout=timeout)
        if str(reaction.emoji) == "✅":
            await message.edit(content=f"{user.mention}, Choose an item to equip")
            item = await select_item_to_equip(ctx, user, player, bot)
        elif str(reaction.emoji) == "❌":
            await message.edit(content=f"[{user.mention}] - No item equipped")
    except Exception as e:
        await message.edit(content=f"[{user.mention}] - No item equipped")

    return item

async def select_item_to_equip(ctx: Context, user: discord.abc.User, player: Player, bot: Bot) -> Optional[Item]:
    selected_item: Optional[Item] = None

    if(player.items == []):
        await ctx.channel.send(content=f"[{user.mention}] - You don't have any item")
        return None

    #On affiche les items accessibles
    text = "Items:\n"
    for idx,item in enumerate(player.items) :
        text+=f"[{idx}] - {item.name}"
        if(idx % 2 == 0):
            text+="\t\t\t\t\t"
        else : 
            text+="\n"
        
    message_item_choix = await ctx.channel.send(text)

    #On ajoute une réaction par item
    for idx in range(len(player.items)) :
        await message_item_choix.add_reaction(fight_manager.from_number_to_emote(idx))

    #On check si le joueur clique sur une réaction
    reaction, _ = await bot.wait_for("reaction_add", check=fight_manager.check_reaction_number(user, message_item_choix), timeout=CHOICE_TIMEOUT)
    num_item_equipped = fight_manager.from_emote_to_number(reaction.emoji)
    selected_item = player.items[num_item_equipped]
    print(f"{user.name} a choisit l'item : {selected_item.name}")

    return selected_item


def generate_name() -> List[str]:
    file_prenom = open("prenom_bully.txt", 'r', encoding='utf-8')
    file_nom = open("nom_bully.txt", 'r', encoding='utf-8')
    lignes = [ligne.strip() for ligne in file_prenom.readlines()]
    r = random.randint(0, len(lignes) - 1)
    prenom = lignes[r]

    lignes = [ligne.strip() for ligne in file_nom.readlines()]
    r = random.randint(0, len(lignes) - 1)
    nom = lignes[r]

    file_prenom.close()
    file_nom.close()
    return [prenom, nom]

#A SUPPRIMER
async def add_bully_custom(ctx: Context, player: Player, name_brute, stats, rarity, channel_cible=None):
    
    #Par défaut, le channel d'envoie est le channel du contexte
    if(channel_cible==None):
        channel_cible = ctx.channel
    
    

    if(len(player.bullies) >= 5) :
        await channel_cible.send(f"You can't have more than 5 bullies at the same time")
        return

    name_bully = name_brute[0] + " " + name_brute[1]
    new_bully = Bully(name_bully, stats=stats, rarity=rarity)

    player.bullies.append(new_bully)

    await channel_cible.send("You have a new bully : " + name_bully)

async def increase_all_lvl(ctx: Context, player: Player, channel_cible=None) -> None:

    #Par défaut, le channel d'envoie est le channel du contexte
    if(channel_cible==None):
        channel_cible = ctx.channel

    print("yep")
    for b in player.bullies:
        b.level_up_one()

    
    await channel_cible.send("done")

def nb_bully_in_team(player: Player) -> int:
    return len(player.bullies)


    