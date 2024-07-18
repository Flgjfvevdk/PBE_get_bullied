import random
import os
import money
from bully import Bully
import bully
from item import Item
import item
from player_info import Player
import generate_name_tab

from pathlib import Path
from typing import Optional, List, Dict, TypeVar, Generic
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from fighting_bully import FightingBully

import asyncio

import discord
from discord.ext.commands import Context, Bot

BULLY_NUMBER_MAX = 5
ITEM_NUMBER_MAX = 6
CHOICE_TIMEOUT = 20


class CancelChoiceException(Exception):
    def __init__(self, text = "Choice canceled"):
        super().__init__(text)

class ButtonChoice(discord.ui.Button):
    def __init__(self, user:discord.abc.User, event:asyncio.Event, variable_pointer:Dict, valeur_assigne, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user:discord.abc.User = user
        self.event:asyncio.Event = event
        self.variable_pointer:Dict = variable_pointer
        self.valeur_assigne = valeur_assigne

    async def callback(self, interaction):
        if(interaction.user == self.user):
            self.variable_pointer["choix"] = self.valeur_assigne
            self.event.set()
            await interaction.response.defer() #Le bot ne renvoie pas de réponse automatique, mais pour faire comprendre à discord que l'interaction n'a pas fail, on fait ça

class ButtonShopChoice(discord.ui.Button):
    def __init__(self, event:asyncio.Event, variable_pointer:Dict[str, Bully | discord.abc.User | None ], valeur_assigne:Bully, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.event:asyncio.Event = event
        self.variable_pointer:Dict[str, Bully | discord.abc.User| None ] = variable_pointer
        self.valeur_assigne:Bully = valeur_assigne

    async def callback(self, interaction):
        self.variable_pointer["choix"] = self.valeur_assigne
        self.variable_pointer["user"] = interaction.user
        self.event.set()
        await interaction.response.defer() #Le bot ne renvoie pas de réponse automatique, mais pour faire comprendre à discord que l'interaction n'a pas fail, on fait ça

class ButtonClickBool(discord.ui.Button):
    def __init__(self, user:discord.abc.User, event:asyncio.Event, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user:discord.abc.User = user
        self.event:asyncio.Event = event

    async def callback(self, interaction):
        if(interaction.user == self.user):
            self.event.set()
            await interaction.response.defer() #Le bot ne renvoie pas de réponse automatique, mais pour faire comprendre à discord que l'interaction n'a pas fail, on fait ça

class ViewBullyShop(discord.ui.View):
    def __init__(self, event:asyncio.Event, list_choix:List[Bully], variable_pointer:Dict[str, Bully | discord.abc.User| None]):
        super().__init__()
        self.list_choix:List[Bully] = list_choix
        for index, choix in enumerate(list_choix):
            label = choix.name
            self.add_item(ButtonShopChoice(style=discord.ButtonStyle.secondary, label=label, custom_id=f"button_{index}", 
                                   event=event, variable_pointer= variable_pointer, valeur_assigne=choix))

class ViewBullyChoice(discord.ui.View):
    def __init__(self, user:discord.abc.User, event:asyncio.Event, list_choix:List[Bully], variable_pointer:Dict[str, Bully | None]):
        super().__init__()
        self.list_choix:List[Bully] = list_choix

        for index, choix in enumerate(list_choix):
            label = choix.name
            self.add_item(ButtonChoice(style=discord.ButtonStyle.secondary, label=label, custom_id=f"button_{index}", 
                                   user = user, event=event, variable_pointer= variable_pointer, valeur_assigne=choix))
        
        self.add_item(ButtonClickBool(style=discord.ButtonStyle.secondary,  label = "Cancel", user = user, event=event, emoji = "❌"))
            
class ViewItemChoice(discord.ui.View): 
    def __init__(self, user:discord.abc.User, event:asyncio.Event, list_choix:List[Item], variable_pointer:Dict[str, Item | None]):
        super().__init__()
        self.list_choix:List[Item] = list_choix

        for index, choix in enumerate(list_choix):
            label = choix.name
            self.add_item(ButtonChoice(style=discord.ButtonStyle.secondary, label=label, custom_id=f"button_{index}", 
                                   user = user, event=event, variable_pointer= variable_pointer, valeur_assigne=choix))
            
        self.add_item(ButtonClickBool(style=discord.ButtonStyle.secondary,  label = "Cancel", user = user, event=event, emoji = "❌"))

T = TypeVar('T')
class ViewChoice(discord.ui.View, Generic[T]): 
    def __init__(self, user:discord.abc.User, event:asyncio.Event, list_choix:List[T], list_choix_name:List[str], variable_pointer:Dict[str, T | None]):
        super().__init__()
        self.list_choix:List[T] = list_choix

        for index, choix in enumerate(list_choix):
            label = list_choix_name[index]
            self.add_item(ButtonChoice(style=discord.ButtonStyle.secondary, label=label, custom_id=f"button_{index}", 
                                   user = user, event=event, variable_pointer= variable_pointer, valeur_assigne=choix))
            # self.add_item(ButtonShopChoice(style=discord.ButtonStyle.secondary, label=label, custom_id=f"button_{index}", 
            #                        event=event, variable_pointer= variable_pointer, valeur_assigne=choix))
            
        self.add_item(ButtonClickBool(style=discord.ButtonStyle.secondary,  label = "Cancel", user = user, event=event, emoji = "❌"))

class ViewYesNo(discord.ui.View):
    def __init__(self, user:discord.abc.User, event:asyncio.Event, variable_pointer:Dict[str, bool]):
        super().__init__()

        self.add_item(ButtonChoice(style=discord.ButtonStyle.secondary, label="Accept", emoji="✅",
                                   user = user, event=event, variable_pointer= variable_pointer, valeur_assigne=True))
        self.add_item(ButtonChoice(style=discord.ButtonStyle.secondary, label="Decline", emoji="❌",
                                   user = user, event=event, variable_pointer= variable_pointer, valeur_assigne=False))

class ViewClickBool(discord.ui.View):
    def __init__(self, user:discord.abc.User, event:asyncio.Event, label:str, emoji:str|None = None):
        super().__init__()
        # emoji = "" if emoji is None else emoji
        self.add_item(ButtonClickBool(style=discord.ButtonStyle.secondary, label=label, emoji=emoji,
                                   user = user, event=event))

## _________________________________________________________________________

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

    await ctx.reply("Welcome to the adventure ! (!!tuto)")
    return 

async def add_random_bully_to_player(ctx: Context, player: Player, name_brute: str, channel_cible=None) -> None:
    name_bully:str = name_brute
    new_bully = Bully(name_bully)

    await add_bully_to_player(ctx, player, new_bully, channel_cible)

async def add_bully_to_player(ctx: Context, player: Player, b: Bully, channel_cible=None) -> None:
    #Par défaut, le channel d'envoie est le channel du contexte
    if(channel_cible==None):
        channel_cible = ctx.channel

    if len(player.get_equipe()) >= BULLY_NUMBER_MAX:
        await channel_cible.send(f"You cannot have more than {BULLY_NUMBER_MAX} bullies!")
        return
    
    player.bullies.append(b)

    await channel_cible.send("You have a new bully : " + b.name)   

async def add_item_to_player(ctx: Context, player: Player, i: Item, channel_cible=None) -> None:
    #Par défaut, le channel d'envoie est le channel du contexte
    if(channel_cible==None):
        channel_cible = ctx.channel


    if len(player.items) >= ITEM_NUMBER_MAX :
        await channel_cible.send("You have to many items. Destroy one to receive the new one.")
        await remove_item(ctx=ctx, user=ctx.author, player=player)
    
        if len(player.items) >= ITEM_NUMBER_MAX :
            await channel_cible.send("You have too many items, the new one is destroyed")

    if len(player.items) < ITEM_NUMBER_MAX :
        await channel_cible.send("You receive a new item : " + i.name)
        player.items.append(i)


async def print_bullies(ctx: Context, player: Player, compact_print=False, print_images=False, channel_cible=None) -> None:
    #Par défaut, le channel d'envoie est le channel du contexte
    if(channel_cible==None):
        channel_cible = ctx.channel


    text = "Your bullies:"
    images: list[Path] = []

    for b in player.get_equipe():
        text += "\n___________\n"
        text += b.get_print(compact_print=compact_print)
        if print_images:
            image_path = b.image_file_path
            image_path_str = str(image_path).replace("\\", "/")
            # if image_path is not None and os.path.isfile(image_path):
            if image_path is not None and os.path.isfile(image_path_str):
                # images.append(image_path)
                images.append(Path(image_path_str))
            else : 
                images.append(bully.BULLY_DEFAULT_PATH_IMAGE)
        
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

def str_bullies(bullies:list[Bully], print_images = False) -> tuple[str, Optional[list[discord.File]]]:
    text = "Your bullies:"
    images: list[Path] = []

    for b in bullies:
        text += "\n___________\n"
        text += b.get_print(compact_print=True)
        if print_images:
            image_path = b.image_file_path
            if image_path is not None:
                images.append(image_path)

    try:
        text = bully.mise_en_forme_str(text)
    except Exception as e:
        print(e)

    if print_images and images :
        files = [discord.File(image) for image in images]
    else :
        files = None
    return (text, files)

def str_fighting_bully(fighting_bully:list[FightingBully], print_images=False) -> tuple[str, Optional[list[discord.File]]]:
    text = "Your bullies:"
    images: list[Path] = []

    for f in fighting_bully:
        text += "\n___________\n"
        text += f.combattant.get_print(compact_print=True, current_hp=f.pv)
        if print_images:
            image_path = f.combattant.image_file_path
            if image_path is not None:
                images.append(image_path)

    try:
        text = bully.mise_en_forme_str(text)
    except Exception as e:
        print(e)

    if print_images and images :
        files = [discord.File(image) for image in images]
    else :
        files = None
    return (text, files)

def str_items(player: Player, compact_print=False) -> str:
    text = "```Items:\n"
    text += "" if compact_print else "___________\n"
    for idx,item in enumerate(player.items) :
        text += item.print(compact_print=compact_print)
        if compact_print :
            if(idx % 2 == 0):
                text+="\t\t\t\t\t"
            else : 
                text+="\n"
        else : 
            text+="\n___________\n"
    text+='```'
    return text

async def player_choose_bully(ctx: Context, user: discord.abc.User, player: Player, bot: Bot, channel_cible=None, timeout = CHOICE_TIMEOUT, from_team=True) -> tuple[Bully, int]:
    '''Il faut try catch cette méthode car elle peut raise une exception en cas de timeout !!!
    '''
    if(channel_cible == None):
        channel_cible = ctx.channel
    
    bullies_in:list[Bully] = player.get_equipe() if from_team else player.get_reserve()

    if len(bullies_in) == 0:
        channel_cible.send(f"{user.mention}, you do not have any bullies!")
        raise IndexError

    #Demande au joueur de choisir son combattant
    message_choose_fighter = await channel_cible.send(f"{user} choose your fighter : ") 

    #On init les variables
    event = asyncio.Event()
    var:Dict[str, Bully | None] = {"choix" : None}
    text, _ = str_bullies(bullies_in, print_images=False)

    #On affiche le message
    message_bullies = await channel_cible.send(content=text, view=ViewBullyChoice(user=user, event=event, list_choix=bullies_in, variable_pointer = var))
    
    #On attend une réponse (et on retourne une erreur si nécessaire avec le timeout)
    await asyncio.wait_for(event.wait(), timeout=timeout)

    #On sélectionne le bully et on crée un FightingBully
    bully_selected = var["choix"]
    if(bully_selected) : 
        bully_number = (bullies_in).index(bully_selected)
    else : 
        raise CancelChoiceException("No selected bully")

    #On envoie les infos sur le bully choisit
    await channel_cible.send(f"{user} sends {bully_selected.name} to fight") 
    
    return bully_selected, bully_number

async def player_choose_fighting_bully(ctx:Context, fighting_bullies:list[FightingBully], user: discord.abc.User, player: Player, bot: Bot, channel_cible=None, timeout = CHOICE_TIMEOUT) -> tuple[FightingBully, int]:
    '''Il faut try catch cette méthode car elle peut raise une exception en cas de timeout !!!
    '''
    if(channel_cible == None):
        channel_cible = ctx.channel

    if len(fighting_bullies) == 0:
        channel_cible.send(f"{user.name}, you do not have any bullies!")
        raise IndexError

    #Demande au joueur de choisir son combattant
    message_choose_fighter = await channel_cible.send(f"{user} choose your fighter : ") 

    #On init les variables
    event = asyncio.Event()
    var:Dict[str, Bully | None] = {"choix" : None}
    text, _ = str_fighting_bully(fighting_bully=fighting_bullies, print_images=False)

    bullies_available = [f.combattant for f in fighting_bullies]

    #On affiche le message
    message_bullies = await channel_cible.send(content=text, view=ViewBullyChoice(user=user, event=event, list_choix=bullies_available, variable_pointer = var))
    
    #On attend une réponse (et on retourne une erreur si nécessaire avec le timeout)
    await asyncio.wait_for(event.wait(), timeout=timeout)

    #On sélectionne le bully et on crée un FightingBully
    bully_selected = var["choix"]
    if(bully_selected) : 
        bully_number = bullies_available.index(bully_selected)
        fighting_bully = fighting_bullies[bully_number]
    else : 
        raise CancelChoiceException("No selected bully")

    #On envoie les infos sur le bully choisit
    await channel_cible.send(f"{user} sends {bully_selected.name} to fight") 
    
    return fighting_bully, bully_number

async def player_choose_item(ctx: Context, user: discord.abc.User, player: Player, bot: Bot, channel_cible=None, timeout = CHOICE_TIMEOUT) -> Optional[Item]:
    if(channel_cible==None):
        channel_cible = ctx.channel

    item:Optional[Item] = None

    text_ask_item = f"{user.mention}, do you want to equip an item?"

    #On créer l'event qui sera set quand le bouton sera cliqué par user. La valeur du bouton (de la réponse) sera stocké dans var
    event = asyncio.Event()
    var:Dict[str, bool] = {"choix" : False}

    #On affiche le message
    message = await ctx.channel.send(content=text_ask_item, view=ViewYesNo(user=user, event=event, variable_pointer = var))

    #On attend que le joueur clique sur un bouton
    try:
        await asyncio.wait_for(event.wait(), timeout=timeout)
    except Exception as e:
        await message.edit(content=f"[{user.mention}] - No item equipped")
        return
    
    #On récup le choix
    want_to_equip_item:bool = var["choix"]

    #On affiche le choix du user
    if(want_to_equip_item) : 
        await message.edit(content=f"{user.mention}, Choose an item to equip")
        item = await select_item_to_equip(ctx, user, player, bot)
    else : 
        await message.edit(content=f"[{user.mention}] - No item equipped")

    return item

async def select_item_to_equip(ctx: Context, user: discord.abc.User, player: Player, bot: Bot, channel_cible=None) -> Optional[Item]:
    if(channel_cible==None):
        channel_cible = ctx.channel
    
    selected_item: Optional[Item] = None

    if(player.items == []):
        await ctx.channel.send(content=f"[{user.mention}] - You don't have any item")
        return None

    #On affiche les items accessibles
    text = str_items(player, compact_print=True)
        
    #On init les variables
    event = asyncio.Event()
    var:Dict[str, Item | None] = {"choix" : None}

    #message_item_choix = await channel_cible.send(text)
    message_item_choix = await channel_cible.send(content=text, view=ViewItemChoice(user=user, event=event, list_choix=player.items, variable_pointer = var))

    #On attend une réponse (et on retourne une erreur si nécessaire avec le timeout)
    try:
        await asyncio.wait_for(event.wait(), timeout=CHOICE_TIMEOUT)
        selected_item = var["choix"]
        if(selected_item):
            print(f"{user.name} a choisit l'item : {selected_item.name}")
    except Exception as e: 
        print(e)

    return selected_item

async def suicide_bully(ctx: Context, user: discord.abc.User, player: Player, bot: Bot, channel_cible=None, timeout = CHOICE_TIMEOUT) -> None :
    if(channel_cible == None):
        channel_cible = ctx.channel

    if len(player.get_equipe()) == 0:
        channel_cible.send(f"{user.mention}, you do not have any bullies!")
        raise IndexError

    #Demande au joueur de choisir son bully
    message_choose_suicide = await channel_cible.send(f"{user} choose a bully to suicide : ") 

    #On init les variables
    event = asyncio.Event()
    var:Dict[str, Bully | None] = {"choix" : None}
    text, _ = str_bullies(player.get_equipe(), print_images=False)

    #On affiche le message
    message_bullies = await channel_cible.send(content=text, view=ViewBullyChoice(user=user, event=event, list_choix=player.get_equipe(), variable_pointer = var))
    
    try:
        #On attend une réponse (et on retourne une erreur si nécessaire avec le timeout)
        await asyncio.wait_for(event.wait(), timeout=timeout)

        #On sélectionne le bully et on crée un FightingBully
        bully_selected = var["choix"]
        if(not bully_selected) : 
            raise CancelChoiceException("No selected bully")

        #On envoie les infos sur le bully choisit
        await message_choose_suicide.edit(content=f"{user} kill {bully_selected.name}")
        await bully_selected.kill()
        money.give_money(player, montant=int(bully_selected.gold_give_when_die()))
        await ctx.send(
            f"Vous avez reçu des {money.MONEY_ICON} ! (+{int(bully_selected.gold_give_when_die())}{money.MONEY_ICON})"
        )
    except Exception as e:
        await message_choose_suicide.edit(content=f"{user} didn't kill any bullies")
    finally:
        await message_bullies.delete()
    
async def remove_item(ctx: Context, user: discord.abc.User, player: Player, channel_cible=None, timeout = CHOICE_TIMEOUT) -> None : 
    if(channel_cible == None):
        channel_cible = ctx.channel

    if len(player.items) == 0:
        channel_cible.send(f"{user.mention}, you do not have any items!")
        raise IndexError
    
    #Demande au joueur de choisir son bully
    message_choose_destroy = await channel_cible.send(f"{user} choose an item to destroy : ") 

    #On init les variables
    event = asyncio.Event()
    var:Dict[str, Item | None] = {"choix" : None}
    text = str_items(player, compact_print=False)

    #On affiche le message
    message_item_choix = await channel_cible.send(content=text, view=ViewItemChoice(user=user, event=event, list_choix=player.items, variable_pointer = var))
    
    try :
        #On attend une réponse (et on retourne une erreur si nécessaire avec le timeout)
        await asyncio.wait_for(event.wait(), timeout=timeout)

        #On sélectionne le bully et on crée un FightingBully
        item_selected = var["choix"]
        if(not item_selected) : 
            raise CancelChoiceException("No selected Item")

        #On envoie les infos sur le bully choisit
        await message_choose_destroy.edit(content=f"{user} destroy {item_selected.name}")
        player.items.remove(item_selected)

    except Exception as e:
        await message_choose_destroy.edit(content=f"{user} didn't destroy any item")
    finally:
        await message_item_choix.delete()


def generate_name() -> str:
    prenom = generate_name_tab.NAME_GENERATOR.generate_name()
    return prenom
    file_prenom = open("prenom_bully.txt", 'r', encoding='utf-8')
    file_nom = open("nom_bully.txt", 'r', encoding='utf-8')
    lignes = [ligne.strip() for ligne in file_prenom.readlines()]
    r = random.randint(0, len(lignes) - 1)
    prenom:str = lignes[r]

    lignes = [ligne.strip() for ligne in file_nom.readlines()]
    r = random.randint(0, len(lignes) - 1)
    nom:str = lignes[r]

    file_prenom.close()
    file_nom.close()
    return prenom + " " + nom

async def increase_all_lvl(ctx: Context, player: Player, nb_level:int = 1,  channel_cible=None) -> None:

    #Par défaut, le channel d'envoie est le channel du contexte
    if(channel_cible==None):
        channel_cible = ctx.channel

    for b in player.bullies:
        for k in range(nb_level):
            b.level_up_one()

    
    await channel_cible.send("done")


def nb_bully_in_team(player: Player) -> int:
    return len(player.get_equipe())


    