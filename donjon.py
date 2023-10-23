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
from dataclasses import dataclass, field, KW_ONLY

from typing import Optional
from typing import List

from discord.ext.commands import Context, Bot
from discord.abc import User
from discord import Thread
import discord.ui as ui

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

enemies_possibles_names=["Thyr O'Flan", "Grobrah Le Musclé", "Plu Didié", "Wè wè", "XxX_BOSS_XxX", "Crapcrap", "Fou Fur", "Eric", "le gars qu'on choisit en dernier en sport et qui se venge" ]

DUNGEON_CHOICE_TIMEOUT = 30
THREAD_DELETE_AFTER = 90
COEF_XP_WIN = 0.3

ENEMIES_MIN_PV = 4
ENEMIES_MAX_PV = 10
ENEMIES_GROUP_SIZE = 5

@dataclass
class Dungeon():
    ctx: Context
    bot: Bot
    player: Player
    level: int

    _: KW_ONLY

    size: int = ENEMIES_GROUP_SIZE

    current_floor: int  = field(init = False, default=0)
    enemies_fighters: List[FightingBully] = field(init=False)
    fighters_joueur: list[FightingBully] = field(init=False)
    xp_earned_bullies: List[float] = field(init=False)
    thread: Thread = field(init=False)

    def __post_init__(self):
        self.enemies_fighters = self.generate_dungeon_team()

        #On initialise les pv et xp gagné par les bullies
        self.fighters_joueur: List[FightingBully] = []
        self.xp_earned_bullies: List[float] = [] #L'xp gagné par chaque bully
        for b in self.player.bullies:
            new_fighter = FightingBully.create_fighting_bully(b)
            self.fighters_joueur.append(new_fighter)
            self.xp_earned_bullies.append(0)

    def generate_dungeon_team(self) -> List[FightingBully]:
        enemies_fighters:List[FightingBully] = []

        for k in range(self.size):
            rarity = bully.Rarity.TOXIC if random.random() < self.level/10 else bully.Rarity.NOBODY

            enemy_fighter = Bully(enemies_possibles_names[k], stats=bully.Stats(1,1,1,1), rarity=rarity, must_load_image=False)

            point_init = enemy_fighter.rarity.points_bonus
            coef_point_lvl_up = enemy_fighter.rarity.level_bonus
            
            def lerp(start, end, x):
                return x*end + (1-x) * start
            
            xp_points = self.level * coef_point_lvl_up + point_init
            points_bonus = round(lerp(xp_points / 3, xp_points, k/self.size))
            pv_enemy = round(lerp(ENEMIES_MIN_PV, ENEMIES_MAX_PV, k/self.size))
            
            lvl_enemy = round((points_bonus - 4) * pv_enemy / 10, 1) if points_bonus > 4 else (round(points_bonus / 5 * pv_enemy / 10, 1))    
            if k==self.size:
                lvl_enemy = self.level
            
            enemy_fighter.increase_stat_with_seed(points_bonus)
            enemy_fighter.lvl = lvl_enemy # Attention, ne recalcule pas les stats

            new_fighter = FightingBully.create_fighting_bully(enemy_fighter)

            enemies_fighters.append(new_fighter)

        return enemies_fighters

    async def enter(self) -> None:
        message = await self.ctx.channel.send(f"{self.ctx.author.mention} enters the dungeon lev : {self.level}")
        try :
            self.thread = await self.ctx.channel.create_thread(name=f"Dungeon - Level {self.level}", message=message) #type: ignore
        except Exception as e:
            print(e)
            return
        
        #On fait la boucle de combat
        try:
            while self.current_floor < self.size:
                await self.handle_fight()

        except TimeoutError as e:
            await self.thread.send(f"Your team left the dungeon. Choose faster next time {self.ctx.author}.")
        except IndexError as e:
            await self.thread.send(
                f"[{self.ctx.author}] -> You don't have this bully.\n" #TODO: fix with ui
                "Your team left the dungeon."
            )
        except Exception as e:
            print(e)

        else:
            #On est plus dans le combat, le joueur à triomphé du donjon
            #On écrit le message de victoire dans les 2 channels
            await self.ctx.channel.send(f"{self.ctx.author.name} has beaten the level {self.level} dungeon!") 
            await self.thread.send(f"{self.ctx.author.name} has beaten the level {self.level} dungeon!") 

            #on donne la récompense d'xp aux joueurs encore en vie
            for i,fighter in enumerate(self.fighters_joueur):
                xp_earned = self.xp_earned_bullies[i]
                if xp_earned > 0:
                    bully_joueur_recompense = fighter.combattant
                    bully_joueur_recompense.give_exp(round(xp_earned * COEF_XP_WIN, 1))

            #On maj le record du joueur sur son dungeon si nécessaire
            if self.level > self.player.max_dungeon:
                self.player.max_dungeon = self.level
        finally:
            await self.exit(THREAD_DELETE_AFTER)



    async def handle_fight(self):
        #On affiche le prochain ennemy
        fighting_bully_enemy = self.enemies_fighters[self.current_floor]
        text_enemy_coming = f"An enemy is coming! {fighting_bully_enemy.combattant.get_print(compact_print=True)}"
        await self.thread.send(f"{bully.mise_en_forme_str(text_enemy_coming)}") 

        #Le player choisit son bully
        _, num_bully_j = await interact_game.player_choose_bully(self.ctx, self.ctx.author, self.player, self.bot, channel_cible=self.thread, timeout=DUNGEON_CHOICE_TIMEOUT)
        
        
        #On fait le combat. Les pv sont maj dans la class fightingBully
        fighting_bully_joueur = self.fighters_joueur[num_bully_j]
        if(fighting_bully_joueur.pv <= 0):
            await self.thread.send(f"Your bully is dead or do not exist. \nYour team left the dungeon.")
            raise IndexError()
        
        await fight_manager.fight_simulation(self.ctx, bot=self.bot, 
                                            fighting_bully_1=fighting_bully_joueur, fighting_bully_2=fighting_bully_enemy,
                                            channel_cible=self.thread)
        
        pv_restant_joueur = fighting_bully_joueur.pv
        bully_joueur = fighting_bully_joueur.combattant
        #On regarde qui a perdu (le joueur ou l'ennemi)
        if(pv_restant_joueur > 0) :
            #Le joueur a gagné
            #On calcul les récompenses, on les affiches et on les stocks
            (exp_earned, gold_earned) = fight_manager.reward_win_fight(bully_joueur, fighting_bully_enemy.combattant)
            pretext = ""
            if (exp_earned > 0):
                bully_joueur.give_exp(exp_earned)
                self.xp_earned_bullies[num_bully_j] += exp_earned
                pretext += f"{bully_joueur.name} earned {exp_earned} xp!\n"
            if (gold_earned > 0):
                money.give_money(self.player, montant=gold_earned)
                pretext += f"{self.ctx.author} earned {gold_earned}{money.MONEY_ICON}!\n"

            #On envoie le message de succès et on progress dans le dungeon
            await self.thread.send(f"{pretext}{fighting_bully_enemy.combattant.name} is dead! You progress in the dungeon.")
            self.current_floor += 1

        else : 
            #Le joueur à perdu
            #On tue le bully qui est ded
            await self.thread.send(f"{bully_joueur.name} died in terrible agony.")
            await bully_joueur.kill()
            self.fighters_joueur.pop(num_bully_j)
            self.xp_earned_bullies.pop(num_bully_j)



    async def exit(self, time_bfr_close: int) -> None:
        try :
            async def delete_thread():
                await self.thread.leave() # leave the thread and stop responding to any more message here.
                await asyncio.sleep(time_bfr_close)
                await self.thread.delete()
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

