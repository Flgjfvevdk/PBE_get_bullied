import os
import random
from bully import Bully #ne pas confondre avec bully (le fichier)
import bully #ne pas confondre avec Bully (la class)
from fighting_bully import FightingBully
from player_info import Player
import interact_game
import fight_manager
import money
import pickle
import asyncio

import utils

from typing import Optional
from typing import List

from discord.ext.commands import Context, Bot
from discord.abc import User
from discord import Thread
import discord.ui as ui

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

ID_joueur_en_donjon = []

enemies_possibles_names=["Thyr O'Flan", "Grobrah Le Musclé", "Plu Didié", "Wè wè", "XxX_BOSS_XxX", "Crapcrap", "Fou Fur", "Eric", "le gars qu'on choisit en dernier en sport et qui se venge" ]
size_dungeon = 5

DUNGEON_CHOICE_TIMEOUT = 30
THREAD_DELETE_AFTER = 90
COEF_XP_WIN = 0.3

minimum_pv = 4
maximum_pv = 10

def generate_donjon_team(level: int, size:int) -> List[FightingBully]:
    enemies_fighters:List[FightingBully] = []

    for k in range(size):
        rarity = bully.Rarity.TOXIC if random.random() < level/10 else bully.Rarity.NOBODY

        enemy_fighter = Bully(enemies_possibles_names[k], stats=bully.Stats(1,1,1,1), rarity=rarity, must_load_image=False)

        point_init = enemy_fighter.rarity.points_bonus
        coef_point_lvl_up = enemy_fighter.rarity.level_bonus
        
        def lerp(start, end, x):
            return x*end + (1-x) * start
        
        xp_points = level * coef_point_lvl_up + point_init
        points_bonus = round(lerp(xp_points / 3, xp_points, k/size))
        pv_enemy = round(lerp(minimum_pv, maximum_pv, k/size))
        
        lvl_enemy = round((points_bonus - 4) * pv_enemy / 10, 1) if points_bonus > 4 else (round(points_bonus / 5 * pv_enemy / 10, 1))    
        if k==size:
            lvl_enemy = level
        
        enemy_fighter.increase_stat_with_seed(points_bonus)
        enemy_fighter.lvl = lvl_enemy # Attention, ne recalcule pas les stats

        new_fighter = FightingBully.create_fighting_bully(enemy_fighter)

        enemies_fighters.append(new_fighter)

    return enemies_fighters

async def enter_the_dungeon(ctx: Context, player: Player, lvl: int, bot: Bot) -> None:
    #Le joueur rentre dans le donjon
    ID_joueur_en_donjon.append(ctx.author.id)

    message = await ctx.channel.send(f"{ctx.author.mention} enters the dungeon lvl : {lvl}")
    try :
        thread = await ctx.channel.create_thread(name=f"Dungeon - Level {lvl}", message=message) #type: ignore
    except Exception as e:
        print(e)
        return

    #On initialise les pv et xp gagné par les bullies
    fighters_joueur: List[FightingBully] = []
    xp_earned_bullies: dict[FightingBully, float] = {} #L'xp gagné par chaque bully
    for b in player.bullies:
        new_fighter = FightingBully.create_fighting_bully(b)
        fighters_joueur.append(new_fighter)
        xp_earned_bullies[new_fighter] = 0
        
    #On génère les ennemies
    enemies_fighters = generate_donjon_team(lvl, size_dungeon)

    #On set les paramètres du donjon
    current_floor = 0

    #On fait la boucle de combat
    while current_floor < size_dungeon :

        #On affiche le prochain ennemy
        fighting_bully_enemy = enemies_fighters[current_floor]
        text_enemy_coming = f"An enemy is coming! {fighting_bully_enemy.combattant.get_print(compact_print=True)}"
        await thread.send(f"{bully.mise_en_forme_str(text_enemy_coming)}") 

        #Le player choisit son bully
        try :
            _, num_bully_j = await interact_game.player_choose_bully(ctx, ctx.author, player, bot, channel_cible=thread, timeout=DUNGEON_CHOICE_TIMEOUT)
        except TimeoutError as e:
            print (e)
            await thread.send(f"Your team left the dungeon. Choose faster next time {ctx.author}") 
            await exit_dungeon(ctx= ctx, thread= thread, time_bfr_close=THREAD_DELETE_AFTER)
            return 
        except IndexError as e:
            print(e)
            await thread.send(
                f"[{ctx.author}] -> You don't have this bully\n" #TODO: fix with ui
                "Your team left the dungeon"
            ) 
            await exit_dungeon(ctx=ctx, thread=thread, time_bfr_close=THREAD_DELETE_AFTER)
            return
        except Exception as e:
            print(e)
            return
        
        #On fait le combat. Les pv sont maj dans la class fightingBully
        fighting_bully_joueur = fighters_joueur[num_bully_j]
        if(fighting_bully_joueur is None or fighting_bully_joueur.pv <= 0):
            await thread.send(f"Your bully is dead or do not exist. \nYour team left the dungeon.") 
            await exit_dungeon(ctx=ctx, thread=thread, time_bfr_close=THREAD_DELETE_AFTER)
            return 
        
        await fight_manager.fight_simulation(ctx, bot= bot, 
                                            fighting_bully_1= fighting_bully_joueur, fighting_bully_2= fighting_bully_enemy,
                                            channel_cible= thread)
        
        pv_restant_joueur = fighting_bully_joueur.pv
        bully_joueur = fighting_bully_joueur.combattant
        #On regarde qui a perdu (le joueur ou l'ennemi)
        if(pv_restant_joueur > 0) :
            #Le joueur a gagné

            #On maj les pv des combattants
            #pv_team_joueur[num_bully_j] = pv_restant_joueur
            #enemies_pv[current_floor] = 0

            #On calcul les récompenses, on les affiches et on les stocks
            (exp_earned, gold_earned) = fight_manager.reward_win_fight(bully_joueur, fighting_bully_enemy.combattant)
            pretext = ""
            if (exp_earned > 0):
                bully_joueur.give_exp(exp_earned)
                xp_earned_bullies[fighting_bully_joueur] += exp_earned
                pretext += f"{bully_joueur.name} earned {exp_earned} xp!\n"
            if (gold_earned > 0):
                money.give_money(player, montant=gold_earned)
                pretext += f"{ctx.author} earned {gold_earned}{money.MONEY_ICON}!\n"

            #On envoie le message de succès et on progress dans le dungeon
            await thread.send(f"{pretext}{fighting_bully_enemy.combattant.name} is dead! You progress in the dungeon.")
            current_floor += 1

        else : 
            #Le joueur à perdu

            #On maj les pv des combattants
            #pv_team_joueur[num_bully_j] = 0
            #enemies_pv[current_floor] = fighting_bully_enemy.pv

            #On tue le bully qui est ded
            await thread.send(f"{bully_joueur.name} died in terrible agony.")
            await bully_joueur.kill()
            fighters_joueur.pop(num_bully_j)

    #On est plus dans le combat, le joueur à triomphé

    #On écrit le message de victoire dans les 2 channels
    await ctx.channel.send(f"{ctx.author.name} has beaten the level {lvl} dungeon!") 
    await thread.send(f"{ctx.author.name} has beaten the level {lvl} dungeon!") 

    #on donne la récompense d'xp aux joueurs encore en vie
    for fighter in fighters_joueur:
        xp_earned = xp_earned_bullies[fighter]
        if xp_earned > 0:
            bully_joueur_recompense = fighter.combattant
            bully_joueur_recompense.give_exp(round(xp_earned * COEF_XP_WIN, 1))

    #On maj le record du joueur sur son dungeon si nécessaire
    if lvl > player.max_dungeon:
        player.max_dungeon = lvl

    #On quitte le donjon
    await exit_dungeon(ctx= ctx, thread= thread, time_bfr_close=THREAD_DELETE_AFTER)



async def exit_dungeon(ctx: Context, thread: Thread, time_bfr_close: int) -> None:
    ID_joueur_en_donjon.remove(ctx.author.id)
    try :
        async def delete_thread():
            await thread.leave() # leave the thread and stop responding to any more message here.
            await asyncio.sleep(time_bfr_close)
            await thread.delete()
        asyncio.create_task(delete_thread())
    except Exception as e:
        print(e)

async def str_leaderboard_donjon(session: AsyncSession) -> str:
    text_classement = ""

    # On récupère tout en une commande SQL
    classement_joueurs = (await session.scalars(select(Player).order_by(Player.max_dungeon.desc()))).all()

    # Afficher le classement des joueurs
    for joueur in classement_joueurs:
        if joueur.max_dungeon > 0:
            text_classement+= f"<@{joueur.id}> - Highest Dungeon Level Reached: {joueur.max_dungeon}\n"
        else:
            text_classement+= f"<@{joueur.id}> is not ranked.\n"

    return text_classement

