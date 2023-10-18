import os
import random
from bully import Bully #ne pas confondre avec bully (le fichier)
import bully #ne pas confondre avec Bully (la class)
from fighting_bully import FightingBully
from item import Item, ItemStats, Seed
import interact_game
import fight_manager
import money
import pickle
import asyncio
from player_info import Player

from enum import Enum

from typing import Optional
from typing import List

from discord.ext.commands import Context, Bot
import discord

import utils

RUIN_CHOICE_TIMEOUT = 30
THREAD_DELETE_AFTER = 90
FIGHTER_CHOICE_TIMEOUT = 20



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



def generate_ruine(lvl, index_rarity = None) -> List[tuple[FightingBully, Item] | FightingBully | Item | Trap]:
    nb_salle_enemy = 4
    nb_salle_item = 0
    nb_salle_regen = 0
    nb_salle_trap = 0
    salles_ruine :List[tuple[FightingBully, Item] | FightingBully | Item | Trap] = []

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
    salles_ruine.append(generate_boss_room(lvl= lvl, index_rarity= index_rarity)) #True = salle de boss
    #Ajout salle Enemy
    for k in range(nb_salle_enemy):
        salles_ruine.append(generate_enemy(lvl= lvl, index_rarity= index_rarity))
    #Ajout salle Item
    for k in range(nb_salle_item):
        salles_ruine.append(generate_item(lvl= lvl, index_rarity= index_rarity))
    # #Ajout salle Regen
    # for k in range(nb_salle_regen):
    #    Salles_ruine.append(Type_salle_ruine.REGEN)
    #Ajout salle Trap
    for k in range(nb_salle_trap):
        salles_ruine.append(generate_trap(lvl= lvl, index_rarity= index_rarity))

    random.shuffle(salles_ruine)
    return salles_ruine

async def enter_the_ruin(ctx: Context, user: discord.abc.User, player: Player, lvl: int, bot: Bot) -> None:
    message = await ctx.channel.send(f"{user.mention} enters a mysterious ruin [lvl : {lvl}]")
    try :
        thread = await ctx.channel.create_thread(name=f"Ruin - Level {lvl}", message= message) #type: ignore
    except Exception as e:
        print(e)
        return

    #On met les chemins vers les dossiers du joueur
    player_brute_path = utils.get_player_path(user.id) / "brutes"

    #On initialise les pv des bullies
    #pv_team_joueur = [] #pv du bully n°index. Si bully n°index n'existe pas alors -1
    fighters_joueur: List[Optional[FightingBully]] = []
    for k in range(interact_game.BULLY_NUMBER_MAX):
        file_bully = player_brute_path / f"{k}.pkl"
        if os.path.exists(file_bully):
            try :
                with open(file_bully, 'rb') as pickle_file:
                    bul = pickle.load(pickle_file)
                new_fighter = FightingBully.create_fighting_bully(bul)
                fighters_joueur.append(new_fighter)
                #pv_team_joueur.append(bul.max_pv)
            except Exception as e:
                print (e)
                await thread.send("probleme DATA") 
                raise(e)
        else :
            #pv_team_joueur.append(-1)
            fighters_joueur.append(None)

    ruin_rooms = generate_ruine(lvl= lvl)
    index_room = 0
    end_ruin = False
    while not end_ruin:
        current_room = ruin_rooms[index_room]
        if (isinstance(current_room, FightingBully)):
            #current_room est un enemy que le joueur doit combattre
            current_enemy_fighter = current_room
            #On fait le combat
            try :
                #is_success, fighters_joueur = await fight_manage_ruin(ctx, user, bot, 
                is_success = await fight_manage_ruin(ctx, user, player, bot, 
                                                                      team_fighters_player = fighters_joueur, fighting_bully_enemy = current_enemy_fighter, 
                                                                      channel_cible = thread)
                if is_success :
                    index_room +=1
            except Exception as e:
                #On quitte les ruines en cas d'exception
                print(e)
                await exit_ruin(ctx, thread, THREAD_DELETE_AFTER)
                return
        
        elif (isinstance(current_room, tuple) and isinstance(current_room[0], FightingBully)) :
            current_enemy_fighter = current_room[0]
            item_boss = current_room[1]

            #On fait le combat
            try :
                #is_success, fighters_joueur = await fight_manage_ruin(ctx, user, bot, 
                is_success = await fight_manage_ruin(ctx, user, player, bot, 
                                                                    team_fighters_player= fighters_joueur, fighting_bully_enemy= current_enemy_fighter, 
                                                                    channel_cible=thread, 
                                                                    is_switch_possible=True, item_enemy= item_boss) #On autorise de switch car combat contre un boss de ruine
                end_ruin = is_success
            except Exception as e:
                #On quitte les ruines en cas d'exception
                print(e)
                await exit_ruin(ctx, thread, THREAD_DELETE_AFTER)
                return

            if (is_success):
                await interact_game.add_item_to_player(ctx, player, item_boss, channel_cible=thread)
    await thread.send(f"Congratulation {user}, you beat the boss!") 
    await exit_ruin(ctx, thread, THREAD_DELETE_AFTER)

    return


async def fight_manage_ruin(ctx: Context, user: discord.abc.User, player: Player, bot: Bot, 
                            team_fighters_player:List[Optional[FightingBully]],  fighting_bully_enemy: FightingBully, 
                            channel_cible, is_switch_possible = False, item_enemy:Optional[Item]=None) -> bool:
    
    text_enemy_coming = f"An enemy is coming! {fighting_bully_enemy.combattant.get_print(compact_print=True)}"
    await channel_cible.send(f"{bully.mise_en_forme_str(text_enemy_coming)}") 

    #Le player choisit son bully
    try :
        _, num_bully_j = await interact_game.player_choose_bully(ctx, user, player, bot, channel_cible=channel_cible, timeout=RUIN_CHOICE_TIMEOUT)
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

    fighting_bully_joueur = team_fighters_player[num_bully_j]
    if(fighting_bully_joueur is None or fighting_bully_joueur.pv <= 0):
        await channel_cible.send(f"Your bully is dead or do not exist. \nYour team left the ruin") 
        raise IndexError 

    #On fait le combat

    if item_enemy != None :
        print("item_enemy : ", item_enemy.get_print())
    fin_combat = False
    while not fin_combat:
        try : 
            await fight_manager.fight_simulation(ctx, bot= bot, 
                                fighting_bully_1= fighting_bully_joueur, fighting_bully_2= fighting_bully_enemy,
                                user_1= user, is_switch_possible= is_switch_possible,
                                item_2= item_enemy,
                                channel_cible=channel_cible)

            #Si on arrive ici, c'est le combat s'est terminé
            fin_combat = True
        
        #Permet de faire une interruption du combat et de changer de bully qui se bat.
        except fight_manager.InterruptionCombat as erreur:
            print(erreur)
            fin_combat = False
            try :
                _, new_num_bully_j = await interact_game.player_choose_bully(ctx, user, player, bot, channel_cible= channel_cible, timeout= FIGHTER_CHOICE_TIMEOUT)
                new_fighting_bully_joueur = team_fighters_player[new_num_bully_j]
                if(new_fighting_bully_joueur == None):
                    raise IndexError
            except TimeoutError as e:
                await channel_cible.send(f"Too slow, {fighting_bully_joueur.combattant.name} stays in fight.")
                new_fighting_bully_joueur = fighting_bully_joueur
                new_num_bully_j = num_bully_j
            except IndexError as e:
                await channel_cible.send(f"Erreur, {fighting_bully_joueur.combattant.name} reste en combat.") 
                new_fighting_bully_joueur = fighting_bully_joueur
                new_num_bully_j = num_bully_j
            
            fighting_bully_joueur = new_fighting_bully_joueur
            num_bully_j = new_num_bully_j

    pv_restant_joueur = fighting_bully_joueur.pv
    #pv_restant_enemy = fighting_bully_enemy.pv
    bully_joueur = fighting_bully_joueur.combattant

    #On regarde qui a perdu (le joueur ou l'ennemi)
    if(pv_restant_joueur > 0) :
        #Le joueur a gagné
        is_success = True

        #On calcul les récompenses, on les affiches et on les stocks
        (exp_earned, gold_earned) = fight_manager.reward_win_fight(bully_joueur, fighting_bully_enemy.combattant)
        pretext = ""
        if (exp_earned > 0):
            bully_joueur.give_exp(exp_earned)
            pretext += f"{fighting_bully_joueur.combattant.name} earned {exp_earned} xp\n"
        if (gold_earned > 0):
            user_gagnant = user
            money.give_money(player, montant=gold_earned)
            pretext += f"{user.name} earned {gold_earned}{money.MONEY_ICON}\n"

        #On envoie le message de succès et on progress dans le dungeon
        await channel_cible.send(f"{pretext}{fighting_bully_enemy.combattant.name} is dead! You progress in the ruin.")
        
    else : 
        #Le joueur à perdu
        is_success = False

        #On tue le bully qui est ded
        await channel_cible.send(f"{fighting_bully_joueur.combattant.name} died in terrible agony")
        await fighting_bully_joueur.combattant.kill()
        team_fighters_player[num_bully_j] = None

    return is_success   
    return is_success, team_fighters_player
    return is_success, pv_team_joueur


async def exit_ruin(ctx: Context, thread, time_bfr_close_thread) -> None:
    #ID_joueur_en_donjon.remove(ctx.author.id)
    try :
        await asyncio.sleep(time_bfr_close_thread)
        await thread.delete()
    except Exception as e:
        print(e)
    return


#Les méthodes de générations des salles et tout //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
def generate_boss_room(lvl, index_rarity) -> tuple[FightingBully, Item]:
    max_pv_boss:int = 20

    boss = Bully("BOSS", rarity=bully.Rarity(index_rarity), must_load_image=False, max_pv=max_pv_boss)
    for k in range(1, lvl) :
        boss.level_up_one()
    item_boss:Item = generate_item(lvl, index_rarity)
    boss_fighter = FightingBully.create_fighting_bully(boss)
    return (boss_fighter, item_boss)

def generate_enemy(lvl, index_rarity) -> FightingBully:
    max_pv_enemy = 5
    enemy = Bully("enemy", rarity=bully.Rarity(index_rarity), must_load_image= False, max_pv= max_pv_enemy)
    for k in range(1, lvl) :
        enemy.level_up_one()
    enemy_fighter = FightingBully.create_fighting_bully(enemy)
    return enemy_fighter

def generate_item(lvl:int, index_rarity) -> Item:
    item_list: list[Item] = []
    item_list.append(Item(name="Str - x0.5", is_bfr_fight= True, buff_start_self=ItemStats(1,0,0,0,0), buff_start_self_mult_lvl=Seed(0.5, 0, 0, 0)))
    item_list.append(Item(name="Str - x1", is_bfr_fight= True, buff_start_self=ItemStats(1,0,0,0,0), buff_start_self_mult_lvl=Seed(1, 0, 0, 0)))
    item_list.append(Item(name="Agi - x0.5", is_bfr_fight= True, buff_start_self=ItemStats(0,1,0,0,0), buff_start_self_mult_lvl=Seed(0, 0.5, 0, 0)))
    item_list.append(Item(name="Agi - x2", is_bfr_fight= True, buff_start_self=ItemStats(0,1,0,0,0), buff_start_self_mult_lvl=Seed(0, 2, 0, 0)))
    item_list.append(Item(name="Letha - x0.5", is_bfr_fight= True, buff_start_self=ItemStats(0,0,1,0,0), buff_start_self_mult_lvl=Seed(0, 0, 0.5, 0)))
    item_list.append(Item(name="Vic - x0.5", is_bfr_fight= True, buff_start_self=ItemStats(0,0,0,1,0), buff_start_self_mult_lvl=Seed(0, 0, 0, 0.5)))
    item_list.append(Item(name="HP - 5", is_bfr_fight= True, buff_start_self=ItemStats(0,0,0,0,5)))
    item = random.choice(item_list)
    return item

def generate_trap(lvl, index_rarity) -> Trap:
    trap = Trap(level=lvl, index_rarity= index_rarity)
    return trap

