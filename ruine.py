import os
import random
from typing import Optional
from bully import Bully #ne pas confondre avec bully (le fichier)
import bully #ne pas confondre avec Bully (la class)
from item import Item
import interract_game
import fight_manager
import money
import pickle
import asyncio

from enum import Enum

from discord.ext.commands import Context

import utils

RUIN_CHOICE_TIMEOUT = 30
THREAD_DELETE_AFTER = 90
FIGHTER_CHOICE_TIMEOUT = 20

def generate_ruine(lvl, index_rarity = None):
    nb_salle_enemy = 4
    nb_salle_item = 0
    nb_salle_regen = 0
    nb_salle_trap = 0
    Salles_ruine = []

    if (index_rarity == None):
        if(lvl <= 10):
            index_rarity = 0
        elif(lvl <= 25):
            index_rarity = 1
        elif(lvl <= 35):
            index_rarity = 2
        elif(lvl <= 45):
            index_rarity = 3
        else:
            index_rarity = 4

    #Ajout salle boss
    Salles_ruine.append(generate_boss_room(lvl= lvl, index_rarity= index_rarity)) #True = salle de boss
    #Ajout salle Enemy
    for k in range(nb_salle_enemy):
        Salles_ruine.append(generate_enemy(lvl= lvl, index_rarity= index_rarity))
    #Ajout salle Item
    for k in range(nb_salle_item):
        Salles_ruine.append(generate_item(lvl= lvl, index_rarity= index_rarity))
    # #Ajout salle Regen
    # for k in range(nb_salle_regen):
    #    Salles_ruine.append(Type_salle_ruine.REGEN)
    #Ajout salle Trap
    for k in range(nb_salle_trap):
        Salles_ruine.append(generate_trap(lvl= lvl, index_rarity= index_rarity))

    random.shuffle(Salles_ruine)
    return Salles_ruine

async def enter_the_ruin(ctx: Context, user, lvl, bot):
    message = await ctx.channel.send(f"{user.mention} enters a mysterious ruin [lvl : {lvl}]")
    try :
        thread = await ctx.channel.create_thread(name=f"Ruin - Level {lvl}", message= message) #type: ignore
    except Exception as e:
        print(e)
        return

    #On met les chemins vers les dossiers du joueur
    player_brute_path = utils.get_player_path(user.id) / "brutes"

    #On initialise les pv des bullies
    pv_team_joueur = [] #pv du bully n°index. Si bully n°index n'existe pas alors -1
    for k in range(interract_game.BULLY_NUMBER_MAX):
        file_bully = player_brute_path / f"{k}.pkl"
        if os.path.exists(file_bully):
            try :
                with open(file_bully, 'rb') as pickle_file:
                    bul = pickle.load(pickle_file)
                pv_team_joueur.append(bul.max_pv)
            except Exception as e:
                print (e)
                await thread.send("probleme DATA") 
                pv_team_joueur.append(10)
        else :
            pv_team_joueur.append(-1)

    Ruin_rooms = generate_ruine(lvl= lvl)
    index_room = 0
    end_ruin = False
    while not end_ruin:
        current_room = Ruin_rooms[index_room]
        if (isinstance(current_room, Bully)):
            #current_room est un enemy que le joueur doit combattre
            current_enemy = current_room
            #On fait le combat
            try :
                is_success, pv_team_joueur = await fight_manage_ruin(ctx, user, bot, current_enemy= current_enemy, pv_team_joueur=pv_team_joueur, channel_cible=thread)
                if is_success :
                    index_room +=1
            except Exception as e:
                #On quitte les ruines en cas d'exception
                print(e)
                await exit_ruin(ctx, thread, THREAD_DELETE_AFTER)
                return
        
        elif (isinstance(current_room, tuple) and isinstance(current_room[0], Bully)) :
            current_enemy = current_room[0]
            item_boss = current_room[1]

            #On fait le combat
            try :
                is_success, pv_team_joueur = await fight_manage_ruin(ctx, user, bot, current_enemy= current_enemy, 
                                                                     pv_team_joueur= pv_team_joueur, channel_cible=thread, 
                                                                     is_switch_possible=True, item_enemy= item_boss) #On autorise de switch car combat contre un boss de ruine
                end_ruin = is_success
            except Exception as e:
                #On quitte les ruines en cas d'exception
                print(e)
                await exit_ruin(ctx, thread, THREAD_DELETE_AFTER)
                return

            if (is_success):
                await interract_game.add_item_to_player(ctx= ctx, user_id= user.id, item=item_boss, channel_cible= thread)
    await thread.send(f"Congratulation {user}, you beat the boss!") 
    await exit_ruin(ctx, thread, THREAD_DELETE_AFTER)

    return


async def fight_manage_ruin(ctx: Context, user, bot, current_enemy, pv_team_joueur, channel_cible, is_switch_possible = False, item_enemy:Optional[Item]=None):
    #channel_cible = thread, current_enemy = current_room
    text_enemy_coming = f"An enemy is coming! {current_enemy.get_print(compact_print=True)}"
    await channel_cible.send(f"{bully.mise_en_forme_str(text_enemy_coming)}") 

    #Le player choisit son bully
    try :
        bully_joueur, num_bully_j = await interract_game.player_choose_bully(ctx, user=user, bot=bot, channel_cible=channel_cible, timeout=RUIN_CHOICE_TIMEOUT)
    except TimeoutError as e:
        await channel_cible.send(f"Your team left the ruin. Choose faster next time {user}") 
        raise e #On propage l'exception
    except IndexError as e:
        await channel_cible.send(
            f"[{user}] -> you don't have a bully n°{e.args[0]}\n"
            "Your team left the ruin") 
        raise e #On propage l'exception
    except Exception as e:
        raise e #On propage l'exception

    #On fait le combat et on récup les pv restants des combattants
    stat_joueur = [bully_joueur.strength, bully_joueur.agility, bully_joueur.lethality, bully_joueur.viciousness]
    stat_enemy = [current_enemy.strength, current_enemy.agility, current_enemy.lethality, current_enemy.viciousness]
    pv_enemy = current_enemy.max_pv

    if item_enemy != None :
        print("item_enemy : ", item_enemy.get_print())
    fin_combat = False
    while not fin_combat:
        try : 
            pv_restant_joueur, pv_restant_enemy = await fight_manager.fight_simulation(ctx= ctx, bot= bot, 
                                                            stat_base_1= stat_joueur, stat_base_2= stat_enemy, 
                                                            name_1= bully_joueur.name, name_2= current_enemy.name, 
                                                            user_1= user, is_switch_possible= is_switch_possible,
                                                            max_pv_1= pv_team_joueur[num_bully_j], max_pv_2= pv_enemy, 
                                                            lvl_1= bully_joueur.lvl, lvl_2= current_enemy.lvl,
                                                            item_2= item_enemy,
                                                            channel_cible=channel_cible)
            #Si on arrive ici, c'est le combat s'est terminé
            fin_combat = True
        
        #Permet de faire une interruption du combat et de changer de bully qui se bat.
        except fight_manager.InterruptionCombat as erreur:
            print(erreur)
            fin_combat = False
            try :
                new_bully_joueur, new_num_bully_j = await interract_game.player_choose_bully(ctx, user= user, bot= bot, channel_cible= channel_cible, timeout= FIGHTER_CHOICE_TIMEOUT)
                
            except TimeoutError as e:
                await channel_cible.send(f"Too slow, {bully_joueur.name} stays in fight.")
                new_bully_joueur = bully_joueur
                new_num_bully_j = num_bully_j
            except IndexError as e:
                await channel_cible.send(f"Erreur, {bully_joueur.name} reste en combat.") 
                new_bully_joueur = bully_joueur
                new_num_bully_j = num_bully_j
            
            pv_team_joueur[num_bully_j] = erreur.pv_1
            pv_enemy = erreur.pv_2
            bully_joueur = new_bully_joueur
            num_bully_j = new_num_bully_j
            stat_joueur = [bully_joueur.strength, bully_joueur.agility, bully_joueur.lethality, bully_joueur.viciousness]
            print(pv_team_joueur)

    #On regarde qui a perdu (le joueur ou l'ennemi)
    if(pv_restant_joueur > 0) :
        #Le joueur a gagné
        is_success = True

        #maj pv
        pv_team_joueur[num_bully_j] = pv_restant_joueur

        #On calcul les récompenses, on les affiches et on les stocks
        (exp_earned, gold_earned) = fight_manager.reward_win_fight(bully_joueur, current_enemy)
        pretext = ""
        if (exp_earned > 0):
            bully_joueur.give_exp(exp_earned)
            pretext += f"{bully_joueur.name} earned {exp_earned} xp\n"
        if (gold_earned > 0):
            user_gagnant = user
            money.give_money(user_id=user_gagnant.id, montant=gold_earned)
            pretext += f"{user.name} earned {gold_earned}{money.MONEY_ICON}\n"

        #On envoie le message de succès et on progress dans le dungeon
        await channel_cible.send(f"{pretext}{current_enemy.name} is dead! You progress in the ruin.")
        
    else : 
        #Le joueur à perdu
        is_success = False

        #On maj les pv des combattants
        pv_team_joueur[num_bully_j] = 0
        current_enemy.max_pv = pv_restant_enemy

        #On tue le bully qui est ded
        await channel_cible.send(f"{bully_joueur.name} died in terrible agony")
        bully_joueur.kill()
        
    return is_success, pv_team_joueur


async def exit_ruin(ctx: Context, thread, time_bfr_close_thread):
    #ID_joueur_en_donjon.remove(ctx.author.id)
    try :
        await asyncio.sleep(time_bfr_close_thread)
        await thread.delete()
    except Exception as e:
        print(e)
    return


#Les méthodes de générations des salles et tout //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
def generate_boss_room(lvl, index_rarity):
    max_pv_boss = 20

    boss = Bully("BOSS", "", rarity=bully.Rarity(index_rarity), must_load_image=False, max_pv=max_pv_boss)
    for k in range(1, lvl) :
        boss.level_up_one()
    item_boss = Item()
    item_boss = generate_item(lvl, index_rarity)
    return (boss, item_boss)

def generate_enemy(lvl, index_rarity):
    max_pv_enemy = 5
    enemy = Bully("enemy", "", rarity=bully.Rarity(index_rarity), must_load_image= False, max_pv= max_pv_enemy)
    for k in range(1, lvl) :
        enemy.level_up_one()
    return enemy

def generate_item(lvl, index_rarity):
    Items_list = []
    Items_list.append(Item(name="Str - x0.5", is_bfr_fight= True, buff_self_start=[0,1,0,0,0], buff_self_start_multiplicatif_lvl=[0.5, 0, 0, 0]))
    Items_list.append(Item(name="Str - x1", is_bfr_fight= True, buff_self_start=[0,1,0,0,0], buff_self_start_multiplicatif_lvl=[1, 0, 0, 0]))
    Items_list.append(Item(name="Agi - x0.5", is_bfr_fight= True, buff_self_start=[0,0,1,0,0], buff_self_start_multiplicatif_lvl=[0, 0.5, 0, 0]))
    Items_list.append(Item(name="Agi - x2", is_bfr_fight= True, buff_self_start=[0,0,1,0,0], buff_self_start_multiplicatif_lvl=[0, 2, 0, 0]))
    Items_list.append(Item(name="Letha - x0.5", is_bfr_fight= True, buff_self_start=[0,0,0,1,0], buff_self_start_multiplicatif_lvl=[0, 0, 0.5, 0]))
    Items_list.append(Item(name="Vic - x0.5", is_bfr_fight= True, buff_self_start=[0,0,0,0,1], buff_self_start_multiplicatif_lvl=[0, 0, 0, 0.5]))
    Items_list.append(Item(name="HP - 5", is_bfr_fight= True, buff_self_start=[5,0,0,0,0]))
    random.shuffle(Items_list)
    item = Items_list[0]
    return item

def generate_trap(lvl, index_rarity):
    trap = Trap(level=lvl, index_rarity= index_rarity)
    return trap


#Classes utile pour ruine 

class Trap :
    def __init__(self, level, index_rarity, stat_index = None, damage = 3):
        init_R = bully.BULLY_RARITY_POINTS[index_rarity]
        coef_R = bully.BULLY_RARITY_LEVEL[index_rarity]

        self.difficulty = round((init_R + coef_R *level) /4) + 1
        if(stat_index == None):
            self.index_stat = random.randint(0,3)
        else :
            self.index_stat = stat_index
        self.damage = damage
        self.text_intro = ""
        self.text_reussite = ""
        self.text_echec = ""
        if (self.index_stat == 0):
            #trap force
            self.text_intro = "The room is filled with large, sharp stones. One must create a path by moving these large stones."
            self.text_reussite = "Your bully moved rocks and created a safe path for everyone."
            self.text_echec = "Moving these rocks has left your bully with numerous wounds and bleeding, but the path is cleared."
        elif (self.index_stat == 1):
            #trap agility
            self.text_intro = "The door to the next room is at the top of a ruined stone starcase. One must climb and tied a rope on top to create a path"
            self.text_reussite = "Your bully climbed perfectly and tied a rope on top."
            self.text_echec = "Climbing has left your bully with numerous wounds and bleeding, but the rope is tied."
        elif (self.index_stat == 2):
            #trap lethality
            self.text_intro = "A terrifying creature is sleeping in the room. One must assassinate it to create a safe path."
            self.text_reussite = "Your bully stabbed the creature, which died instantly."
            self.text_echec = "Your bully stabbed the creature, but it didn't instantly die, and hurt your bully."
        elif (self.index_stat == 3):
            #trap viciousness
            self.text_intro = "The room is full of traps. One must identify them and find a safe path."
            self.text_reussite = "Your bully identify every traps and find a safe path for everyone."
            self.text_echec = "Your bully was wounded by many traps but ended up finding a safe path."

