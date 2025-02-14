import random
import os
import money
from bully import Bully
import bully
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
from all_texts import getText

BULLY_NUMBER_MAX = 5
ITEM_NUMBER_MAX = 6
CHOICE_TIMEOUT = 20
NB_REFERRAL_REWARD = 5


class CancelChoiceException(Exception):
    def __init__(self, text = "Choice cancelled"):
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

class ButtonMultipleChoice(discord.ui.Button):
    def __init__(self, users: List[discord.abc.User], events: List[asyncio.Event], variable_pointers: List[Dict], valeur_assigne, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.users = users
        self.events = events
        self.variable_pointers = variable_pointers
        self.valeur_assigne = valeur_assigne

    async def callback(self, interaction):
        if interaction.user in self.users:
            user_index = self.users.index(interaction.user)
            self.variable_pointers[user_index]["choix"] = self.valeur_assigne
            self.events[user_index].set()
            await interaction.response.defer()

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


T = TypeVar('T')
class ViewChoice(discord.ui.View, Generic[T]): 
    def __init__(self, user:discord.abc.User, event:asyncio.Event, list_choix:List[T], list_choix_name:List[str], variable_pointer:Dict[str, T | None]):
        super().__init__()
        self.list_choix:List[T] = list_choix

        for index, choix in enumerate(list_choix):
            label = list_choix_name[index]
            self.add_item(ButtonChoice(style=discord.ButtonStyle.secondary, label=label, custom_id=f"button_{index}", 
                                   user = user, event=event, variable_pointer= variable_pointer, valeur_assigne=choix))
            
        self.add_item(ButtonClickBool(style=discord.ButtonStyle.secondary,  label = "Cancel", user = user, event=event, emoji = "❌"))

class ViewYesNo(discord.ui.View):
    def __init__(self, user:discord.abc.User, event:asyncio.Event, variable_pointer:Dict[str, bool]):
        super().__init__()

        self.add_item(ButtonChoice(style=discord.ButtonStyle.secondary, label="Accept", emoji="✅",
                                   user = user, event=event, variable_pointer= variable_pointer, valeur_assigne=True))
        self.add_item(ButtonChoice(style=discord.ButtonStyle.secondary, label="Decline", emoji="❌",
                                   user = user, event=event, variable_pointer= variable_pointer, valeur_assigne=False))

class ViewMultipleYesNo(discord.ui.View):
    def __init__(self, users: List[discord.abc.User], events: List[asyncio.Event], variable_pointers: List[Dict[str, bool]]):
        super().__init__()

        if not (len(users) == len(events) == len(variable_pointers)):
            raise ValueError("Les listes users, events et variable_pointers doivent avoir la même longueur.")

        self.users = users
        self.events = events
        self.variable_pointers = variable_pointers

        self.add_item(ButtonMultipleChoice(style=discord.ButtonStyle.secondary, label="Accept", emoji="✅",
                                           users=users, events=events, variable_pointers=variable_pointers, valeur_assigne=True))
        self.add_item(ButtonMultipleChoice(style=discord.ButtonStyle.secondary, label="Decline", emoji="❌",
                                           users=users, events=events, variable_pointers=variable_pointers, valeur_assigne=False))

class ViewClickBool(discord.ui.View):
    def __init__(self, user:discord.abc.User, event:asyncio.Event, label:str, emoji:str|None = None):
        super().__init__()
        self.add_item(ButtonClickBool(style=discord.ButtonStyle.secondary, label=label, emoji=emoji,
                                   user = user, event=event))
class ViewClickBoolMultiple(discord.ui.View):
    def __init__(self, users:list[discord.abc.User], events:list[asyncio.Event], labels:list[str], emoji:str|None = None):
        super().__init__()
        if len(users) != len(events) or len(users) != len(labels):
            raise Exception("Les tailles des listes ne correspondent pas")
        for k in range(len(users)):
            self.add_item(ButtonClickBool(style=discord.ButtonStyle.secondary, label=labels[k], emoji=emoji,
                                    user = users[k], event=events[k]))

## _________________________________________________________________________

async def join_game(ctx: Context, user:discord.Member|discord.User, session: AsyncSession, channel_cible: Optional[discord.abc.Messageable]=None) -> Player|None:
    # Par défaut, le channel d'envoie est le channel du contexte
    if(channel_cible==None):
        channel_cible = ctx.channel
    
    player = Player(money.MONEY_JOIN_VALUE)
    player.id = user.id
    try:
        session.add(player)
        await session.commit()
    except IntegrityError:
        await ctx.reply(getText("already_joined_game"))
        # await ctx.reply("You have already joined the game!")
        return

    await ctx.reply(getText("welcome_adventure"))
    # await ctx.reply("Welcome to the adventure ! (!!tuto)")
    return player

async def invite_join(ctx: Context, parrain:Player, user:discord.Member|discord.User, session: AsyncSession, channel_cible: Optional[discord.abc.Messageable]=None) -> None:
    event = asyncio.Event()
    var:Dict[str, bool] = {"choix" : False}

    if(user != ctx.author):
        #On affiche le message
        message = await ctx.channel.send(content=getText("invite_join_game").format(user=user.mention), view=ViewYesNo(user=user, event=event, variable_pointer = var))
        # message = await ctx.channel.send(content=f"{user}, do you want to join game ?", view=ViewYesNo(user=user, event=event, variable_pointer = var))
        try:
            await asyncio.wait_for(event.wait(), timeout=CHOICE_TIMEOUT)
        except asyncio.exceptions.TimeoutError as e:
            await message.delete()
            return
        join_accept:bool = var["choix"]
        await message.delete()
        if join_accept :
            new_player = Player(money.MONEY_JOIN_VALUE)
            new_player.id = user.id
            try:
                session.add(new_player)
                parrain.nb_referrals += 1
                parrain.money += money.MONEY_REFERRAL
                bully_gift = Bully(f"{ctx.author.name}'s gift", stats=bully.Stats(8, 8, 8, 8), buff_fight_tag="Friendship")
                new_player.bullies.append(bully_gift)
                if (parrain.nb_referrals == NB_REFERRAL_REWARD):
                    await ctx.send(getText("referral_reward").format(user=ctx.author.mention, nb=NB_REFERRAL_REWARD))
                    # await ctx.send(f"{ctx.author.mention} you have invited {NB_REFERRAL_REWARD} friends ! You deserve a prize (ask for it :wink: )") 
                await ctx.send(getText("other_join").format(user=user))
                # await ctx.send(f"{user} has joined the game!")
                await session.commit()
            except IntegrityError:
                await ctx.reply(getText("already_joined_game"))
                # await ctx.reply("You have already joined the game.")
                return            


async def make_bot_join(bot_user : discord.ClientUser, session: AsyncSession) -> Player|None:
    bot_player = Player(0)
    bot_player.id = bot_user.id
    try:
        session.add(bot_player)
        await session.commit()
    except IntegrityError:
        return
    return bot_player


async def add_random_bully_to_player(ctx: Context, player: Player, name_brute: str, channel_cible=None, talkative=True) -> None:
    name_bully:str = name_brute
    new_bully = Bully(name_bully)

    await add_bully_to_player(ctx, player, new_bully, channel_cible, talkative=talkative)

async def add_bully_to_player(ctx: Context, player: Player, b: Bully, channel_cible=None, talkative=True) -> None:
    #Par défaut, le channel d'envoie est le channel du contexte
    if(channel_cible==None):
        channel_cible = ctx.channel

    if len(player.get_equipe()) >= BULLY_NUMBER_MAX:
        if talkative :
            await channel_cible.send(getText("max_bullies_reached").format(user = ctx.author.name, max_bullies=BULLY_NUMBER_MAX))
            # await channel_cible.send(f"You cannot have more than {BULLY_NUMBER_MAX} bullies!")
        return
    
    player.bullies.append(b)

    await channel_cible.send(getText("new_bully_msg").format(bully=b.name))
    # await channel_cible.send(f"You have a new bully : " + b.name)   


async def print_bullies(ctx: Context, player: Player, compact_print=False, print_images=False, channel_cible=None) -> None:
    #Par défaut, le channel d'envoie est le channel du contexte
    if(channel_cible==None):
        channel_cible = ctx.channel

    text = getText("your_bullies")
    # text = "Your bullies:"
    split_txt = []
    # images: list[Path] = []
    images: dict[int, Path] = {}

    player_bullies = player.get_equipe()
    for b in player_bullies:
        text += "\n___________\n"
        text += b.get_print(compact_print=compact_print)
        split_txt.append(bully.mise_en_forme_str(b.get_print(compact_print=compact_print)))
        if print_images:
            image_path = b.image_file_path
            image_path_str = str(image_path).replace("\\", "/")
            if image_path is not None and os.path.isfile(image_path_str):
                # images.append(Path(image_path_str))
                images[b.id] = Path(image_path_str)
            else : 
                # images.append(bully.BULLY_DEFAULT_PATH_IMAGE)
                images[b.id] = bully.BULLY_DEFAULT_PATH_IMAGE
        
    try:
        text = bully.mise_en_forme_str(text)
    except Exception as e:
        print(e)

    event = asyncio.Event()
    var:Dict[str, Bully | None] = {"choix" : None}
    if print_images and False:
        if images:
            files = [discord.File(image) for image in images]
            message = await channel_cible.send(content=text, files=files)
        else:
            message = await channel_cible.send(text)
    else:
        # message = await channel_cible.send(text)
        from utils.embed import create_embed
        message = await channel_cible.send(embed=create_embed("Your bullies", split_txt, columns=1, str_between_element=""))

    await message.edit(view = ViewBullyChoice(user=ctx.author, event=event, list_choix=player_bullies, variable_pointer = var)) 
    
    try:
        await asyncio.wait_for(event.wait(), timeout=CHOICE_TIMEOUT)

        bully_selected = var["choix"]
        if(not bully_selected) : 
            raise Exception("No selected bully")
            
        text_info = bully_selected.str_all_infos()
        if print_images:
            if images:
                
                # file = discord.File(images[bully_selected.id])
                # await message.reply(content=bully.mise_en_forme_str(text_info), file=file)

                filename = str(images[bully_selected.id])
                print("filename is ", filename)
                file = discord.File(images[bully_selected.id], filename=filename)
                await message.reply(embed=create_embed(title="",  description_lines=[bully.mise_en_forme_str(text_info)]), file=file)
            else:
                await message.reply(bully.mise_en_forme_str(text_info))
        else:
            await message.reply(bully.mise_en_forme_str(text_info))
        
    except Exception as e:
        pass
    finally:
        await message.edit(view = None)

    return

def str_bullies(bullies:list[Bully], print_images = False) -> tuple[str, Optional[list[discord.File]]]:
    text = getText("your_bullies")
    # text = "Your bullies:"
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
    text = getText("your_bullies")
    # text = "Your bullies:"
    images: list[Path] = []

    for f in fighting_bully:
        text += "\n___________\n"
        text += f.get_print()
        if print_images:
            image_path = f.bully.image_file_path
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


async def select_bully(ctx: Context, user: discord.abc.User, player: Player, channel_cible=None, timeout = CHOICE_TIMEOUT, from_team=True) -> Bully:
    '''Il faut try catch cette méthode car elle peut raise une exception en cas de timeout !!!'''
    if(channel_cible == None):
        channel_cible = ctx.channel
    
    bullies_in:list[Bully] = player.get_equipe() if from_team else player.get_reserve()

    if len(bullies_in) == 0:
        await channel_cible.send(getText("you_have_no_bully").format(user=user.mention))
        # await channel_cible.send(f"{user.mention}, you do not have any bullies!")
        raise IndexError

    #Demande au joueur de choisir son combattant
    message_choose_bully = await channel_cible.send(getText("choose_bully").format(user=user.mention))
    # message_choose_bully = await channel_cible.send(f"{user} choose a bully : ") 

    #On init les variables
    event = asyncio.Event()
    var:Dict[str, Bully | None] = {"choix" : None}
    text, _ = str_bullies(bullies_in, print_images=False)

    #On affiche le message
    message_bullies = await channel_cible.send(content=text, view=ViewBullyChoice(user=user, event=event, list_choix=bullies_in, variable_pointer = var))
    
    #On attend une réponse (et on retourne une erreur si nécessaire avec le timeout)
    try :
        await asyncio.wait_for(event.wait(), timeout=timeout)
    finally:
        await message_choose_bully.delete()
        await message_bullies.delete()

    #On sélectionne le bully et on crée un FightingBully
    bully_selected = var["choix"]
    if(bully_selected) : 
        bully_number = (bullies_in).index(bully_selected)
    else : 
        raise CancelChoiceException("No selected bully")

    #On envoie les infos sur le bully choisit
    await channel_cible.send(getText("selected_bully").format(user=user, bully=bully_selected.name))
    # await channel_cible.send(f"{user} selects {bully_selected.name}") 
    return bully_selected

async def player_choose_fighting_bully(ctx:Context, fighting_bullies:list[FightingBully], user: discord.abc.User, channel_cible=None, timeout = CHOICE_TIMEOUT) -> tuple[FightingBully, int]:
    '''Il faut try catch cette méthode car elle peut raise une exception en cas de timeout !!!'''
    if(channel_cible == None):
        channel_cible = ctx.channel

    if len(fighting_bullies) == 0:
        await channel_cible.send(getText("you_have_no_bully").format(user=user.name))
        # channel_cible.send(f"{user.name}, you do not have any bullies!")
        raise IndexError

    #Demande au joueur de choisir son combattant
    message_choose_fighter = await channel_cible.send(getText("choose_fighter").format(user=user))
    # message_choose_fighter = await channel_cible.send(f"{user} choose your fighter : ") 

    #On init les variables
    event = asyncio.Event()
    var:Dict[str, Bully | None] = {"choix" : None}
    text, _ = str_fighting_bully(fighting_bully=fighting_bullies, print_images=False)

    bullies_available = [f.bully for f in fighting_bullies]

    message_bullies = await channel_cible.send(content=text, view=ViewBullyChoice(user=user, event=event, list_choix=bullies_available, variable_pointer = var))
    
    #On attend une réponse (et on retourne une erreur si nécessaire avec le timeout)
    try :
        await asyncio.wait_for(event.wait(), timeout=timeout)
    finally:
        await message_choose_fighter.delete()
        await message_bullies.delete()

    #On sélectionne le bully et on crée un FightingBully
    bully_selected = var["choix"]
    if(bully_selected) : 
        bully_number = bullies_available.index(bully_selected)
        fighting_bully = fighting_bullies[bully_number]
    else : 
        raise CancelChoiceException("No selected bully")

    await channel_cible.send(getText("selected_bully").format(user=user, bully=bully_selected.name))
    # await channel_cible.send(f"{user} select {bully_selected.name}.") 
    return fighting_bully, bully_number

async def suicide_bully(ctx: Context, user: discord.abc.User, player: Player, bot: Bot, channel_cible=None, timeout = CHOICE_TIMEOUT) -> None :
    if(channel_cible == None):
        channel_cible = ctx.channel

    if len(player.get_equipe()) == 0:
        await channel_cible.send(getText("you_have_no_bully").format(user=user.mention))
        # await channel_cible.send(f"{user.mention}, you do not have any bullies!")
        raise IndexError

    #Demande au joueur de choisir son bully
    message_choose_suicide = await channel_cible.send(getText("choose_suicide").format(user = user))
    # message_choose_suicide = await channel_cible.send(f"{user} choose a bully to suicide : ") 

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
        await message_choose_suicide.edit(content=getText("suicide_kill"))
        # await message_choose_suicide.edit(content=f"{user} kills {bully_selected.name}")
        await bully_selected.kill()
        money.give_money(player, montant=int(bully_selected.gold_give_when_die()))
        await ctx.send(getText("you_receive_gold").format(value = int(bully_selected.gold_give_when_die()), money_emoji = money.MONEY_EMOJI))
        # await ctx.send(f"Vous avez reçu des {money.MONEY_EMOJI} ! (+{int(bully_selected.gold_give_when_die())}{money.MONEY_EMOJI})")
    except Exception as e:
        await message_choose_suicide.edit(content=getText("no_suicide").format(user=user))
        # await message_choose_suicide.edit(content=f"{user} didn't kill any bullies")
    finally:
        await message_bullies.delete()
   
def generate_name() -> str:
    prenom = generate_name_tab.NAME_GENERATOR.generate_name()
    return prenom

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


    