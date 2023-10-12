import os
import random
import pickle
import money
from bully import Bully
import bully
from item import Item
import item

import fight_manager # ##$$$

import discord

number_bully_max = 5
delaie_timeout = 20

path_player_data = "game_data/player_data"

async def join_game(ctx, user_player_path, channel_cible=None):

    #Par défaut, le channel d'envoie est le channel du contexte
    if(channel_cible==None):
        channel_cible = ctx.channel

    folder_exist =  os.path.exists(user_player_path)
    if(folder_exist):
        await channel_cible.send("You already joined")
        return 
    else :
        try:
            os.makedirs(user_player_path, exist_ok=False)
            os.makedirs(user_player_path + "/brutes", exist_ok=True)
            os.makedirs(user_player_path + "/items", exist_ok=True)
            file = open(user_player_path + "/playerMoney.txt", "w")
            file.write(str(money.money_join_value))
            file.close()
            
            file = open(user_player_path + "/playerMaxDungeon.txt", "w")
            file.close()

        except FileExistsError:
            print("Folder already exists! ERROR")
        except Exception as e:
            print(e)

        await channel_cible.send("Welcome to the adventure !")
        return 

async def add_random_bully_to_player(ctx, user_id, name_brute, channel_cible=None):
    
    #Par défaut, le channel d'envoie est le channel du contexte
    if(channel_cible==None):
        channel_cible = ctx.channel

    player_path = "game_data/player_data/" + str(user_id)
    player_brute_path = player_path + "/brutes"
    ind = 0
    while os.path.exists(player_brute_path + "/" + str(ind) + ".pkl"):
        ind += 1

    if(ind > number_bully_max - 1) :
        await channel_cible.send(f"You can't have more than {number_bully_max} bullies at the same time")
        return
    
    id_brute = str(ind)

    file_path = player_brute_path + "/" + id_brute + ".pkl"
    
    # Open the file in write mode (creates the file if it doesn't exist)
    file = open(file_path, "wb")
    name_bully = name_brute[0] + " " + name_brute[1]
    new_bully = Bully(name_bully, file_path)
    try :
        pickle.dump(new_bully, file)
    except Exception as e :
        print(e)

    await channel_cible.send("You have a new bully : " + name_bully)
    # Close the file
    file.close()

async def add_bully_to_player(ctx, user_id, b, channel_cible=None):
    #Par défaut, le channel d'envoie est le channel du contexte
    if(channel_cible==None):
        channel_cible = ctx.channel

    player_path = "game_data/player_data/" + str(user_id)
    player_brute_path = player_path + "/brutes"
    ind = 0
    
    while os.path.exists(player_brute_path + "/" + str(ind) + ".pkl"):
        ind += 1

    if(ind > number_bully_max - 1) :
        await channel_cible.send(f"You can't have more than {number_bully_max} bullies at the same time")
        return
    
    id_brute = str(ind)

    file_path = player_brute_path + "/" + id_brute + ".pkl"
    
    # Open the file in write mode (creates the file if it doesn't exist)
    file = open(file_path, "wb")
    new_bully = b
    new_bully.set_file_path(file_path)
    try :
        pickle.dump(new_bully, file)
    except Exception as e :
        print(e)

    await channel_cible.send("You have a new bully : " + b.name)
    # Close the file
    file.close()

async def add_item_to_player(ctx, user_id, i, channel_cible=None):
    #Par défaut, le channel d'envoie est le channel du contexte
    if(channel_cible==None):
        channel_cible = ctx.channel

    player_path = "game_data/player_data/" + str(user_id)
    player_item_path = player_path + "/items"
    ind = 0
    
    while os.path.exists(player_item_path + "/" + str(ind) + ".pkl"):
        ind += 1
    
    id_item = str(ind)

    file_path = player_item_path + "/" + id_item + ".pkl"
    
    # Open the file in write mode (creates the file if it doesn't exist)
    file = open(file_path, "wb")
    new_item = i
    new_item.set_file_path(file_path)
    try :
        pickle.dump(new_item, file)
    except Exception as e :
        print(e)

    await channel_cible.send("You have a new item : " + i.name)
    # Close the file
    file.close()

async def print_bullies(ctx, player_path, compact_print=False, print_images=False, channel_cible=None):
    #Par défaut, le channel d'envoie est le channel du contexte
    if(channel_cible==None):
        channel_cible = ctx.channel

    player_brute_path = player_path + "/brutes"
    text = "Your bullies:"
    images = []

    for f in sorted(os.listdir(player_brute_path)):
        chemin_fichier = os.path.join(player_brute_path, f)
        if os.path.isfile(chemin_fichier) and f.endswith(".pkl"):
            text += "\n___________\n"
            with open(chemin_fichier, 'rb') as pickle_file:
                b = pickle.load(pickle_file)
            text += b.get_print(compact_print=compact_print)

            if print_images:
                image_path = b.get_image_path()  # Remplacez cette fonction par votre propre méthode pour obtenir le chemin de l'image
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

async def print_items(ctx, player_path, compact_print=False, channel_cible=None):
    #Par défaut, le channel d'envoie est le channel du contexte
    if(channel_cible==None):
        channel_cible = ctx.channel

    player_item_path = player_path + "/items"
    text = "Your items:"

    for f in sorted(os.listdir(player_item_path)):
        chemin_fichier = os.path.join(player_item_path, f)
        if os.path.isfile(chemin_fichier) and f.endswith(".pkl"):
            text += "\n___________\n"
            with open(chemin_fichier, 'rb') as pickle_file:
                i = pickle.load(pickle_file)
            text += i.get_print(compact_print=compact_print)

    text = item.mise_en_forme_str(text)

    await channel_cible.send(text)

    return

async def player_choose_bully(ctx, user, bot, channel_cible=None, delaie_timeout = delaie_timeout):
    '''Il faut try catch cette méthode car elle peut raise une exception en cas de timeout !!!
    '''
    if(channel_cible == None):
        channel_cible = ctx.channel

    path_players_data = "game_data/player_data"
    player_brute_path = path_players_data + "/" + str(user.id) + "/brutes"

    #Demande au joueur de choisir son combattant
    message_choose_fighter = await channel_cible.send(f"{user} choose your fighter : ") 
    await print_bullies(ctx, path_players_data + "/" + str(user.id), compact_print = True, channel_cible= channel_cible)
    for k in range(number_bully_max):
        if os.path.exists(player_brute_path + "/" + str(k) + ".pkl"):
            await message_choose_fighter.add_reaction(fight_manager.from_number_to_emote(k))

    #On attend le choix du joueur
    try : 
        reaction, msg = await bot.wait_for("reaction_add", check= fight_manager.check_reaction_number(user, message_choose_fighter), timeout= delaie_timeout)
        bully_number = fight_manager.from_emote_to_number(reaction.emoji)
    except Exception as e:
        raise TimeoutError("Timeout choose bully delay")
    
    #On a récup le bully associé au choix du joueur
    file_path = player_brute_path + "/" + str(bully_number) + ".pkl"
    try :
        with open(file_path, 'rb') as pickle_file:
            bully_selected = pickle.load(pickle_file)
        await channel_cible.send(f"{user} sends {bully_selected.name} to fight") 
    except Exception as e:
        raise IndexError("Player don't have this bully")
    
    return bully_selected, bully_number

async def player_choose_item(ctx, user, bot, channel_cible=None, delaie_timeout = delaie_timeout):
    if(channel_cible==None):
        channel_cible = ctx.channel
    item = None

    text_ask_item = f"{user.mention}, do you want to equip an item?"
    message = await channel_cible.send(text_ask_item)
    await message.add_reaction("✅")
    await message.add_reaction("❌")
    try :
        reaction, msg = await bot.wait_for("reaction_add", check=fight_manager.check_reaction_yes_no(user, message), timeout=delaie_timeout)
        if str(reaction.emoji) == "✅" :
            await message.edit(content=f"{user.mention}, Choose an item to equip")
            item = await select_item_to_equip(ctx = ctx, user=user, bot=bot)
        elif str(reaction.emoji) == "❌" :
            await message.edit(content=f"[{user.mention}] - No item equipped")
    except Exception as e :
        await message.edit(content=f"[{user.mention}] - No item equipped")

    return item

async def select_item_to_equip(ctx, user, bot):
    selected_item = None

    #Lien vers le dossier des items
    path_players_data = "game_data/player_data"
    player_path_items = path_players_data + "/" + str(user.id) + "/items"

    #On récup la liste des items dispos.
    Liste_items = []
    try :
        for file in (os.listdir(player_path_items)):
            if file.endswith(".pkl"):
                try :
                    with open(player_path_items + "/" + file, 'rb') as pickle_file:
                        item = pickle.load(pickle_file)
                    Liste_items.append(item)
                except Exception as e:
                    print("un pb ici")
                    print (e)
    except Exception as e:
        print(e)

    if(Liste_items == []):
        await ctx.channel.send(content=f"[{user.mention}] - You don't have any item")
        return None

    #On affiche les items accessibles
    text = "Items:\n"
    for idx,item in enumerate(Liste_items) :
        text+=f"[{idx}] - {item.name}"
        if(idx % 2 == 0):
            text+="\t\t\t\t\t"
        else : 
            text+="\n"
        
    message_item_choix = await ctx.channel.send(text)

    #On ajoute une réaction par item
    for idx,item in enumerate(Liste_items) :
        await message_item_choix.add_reaction(fight_manager.from_number_to_emote(idx))

    #On check si le joueur clique sur une réaction
    try : 
        reaction, msg = await bot.wait_for("reaction_add", check=fight_manager.check_reaction_number(user, message_item_choix), timeout=delaie_timeout)
        num_item_equipped = fight_manager.from_emote_to_number(reaction.emoji)
        selected_item = Liste_items[num_item_equipped]
    except Exception as e:
        await ctx.channel.send(content=f"[{user.mention}] - No item equipped")

    print(f"{user.name} a choisit l'item : {selected_item.name}")
    return selected_item


def generate_name():
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
async def add_bully_custom(ctx, player_path, name_brute, stats, rarity, channel_cible=None):
    
    #Par défaut, le channel d'envoie est le channel du contexte
    if(channel_cible==None):
        channel_cible = ctx.channel
    
    player_brute_path = player_path + "/brutes"
    ind = 0
    while os.path.exists(player_brute_path + "/" + str(ind) + ".pkl"):
        ind += 1

    if(ind > 4) :
        await channel_cible.send(f"You can't have more than 5 bullies at the same time")
        return
    
    id_brute = str(ind)

    file_path = player_brute_path + "/" + id_brute + ".pkl"
    
    # Open the file in write mode (creates the file if it doesn't exist)
    file = open(file_path, "wb")
    name_bully = name_brute[0] + " " + name_brute[1]
    new_bully = Bully(name_bully, file_path, stats=stats, rarity=rarity)
    try :
        pickle.dump(new_bully, file)
    except Exception as e :
        print(e)

    await channel_cible.send("You have a new bully : " + name_bully)
    # Close the file
    file.close()

async def increase_all_lvl(ctx, player_path, channel_cible=None):

    #Par défaut, le channel d'envoie est le channel du contexte
    if(channel_cible==None):
        channel_cible = ctx.channel

    player_brute_path = player_path + "/brutes"
    print("yep")
    try :
        for f in sorted(os.listdir(player_brute_path)) :
            chemin_fichier = os.path.join(player_brute_path, f)
            if os.path.isfile(chemin_fichier) and f.endswith(".pkl"):
                with open(chemin_fichier, 'rb') as pickle_file:
                    b = pickle.load(pickle_file)
                    b.level_up_one()
                    b.save_changes()
    except Exception as e:
        print(e)
        return
    #await ctx.channel.send("done")
    await channel_cible.send("done")

def nb_bully_in_team(user_id):
    player_path = "game_data/player_data/" + str(user_id)
    player_brute_path = player_path + "/brutes"
    ind = 0
    for k in range(number_bully_max):
        if os.path.exists(player_brute_path + "/" + str(k) + ".pkl"):
            ind += 1

    return ind


def correct_missing_folder(user_path):
    if(not os.path.exists(user_path)):
        raise Exception("Le joueur n'existe pas dans la bdd, il doit join")
    else : 
        if (not os.path.exists(user_path + "/brutes")):
            os.makedirs(user_path + "/brutes", exist_ok=True)
        if (not os.path.exists(user_path + "/items")):
            os.makedirs(user_path + "/items", exist_ok=True)

    