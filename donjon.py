import os
import random
from bully import Bully, Rarity #ne pas confondre avec bully (le fichier)
import bully #ne pas confondre avec Bully (la class)
from fighting_bully import FightingBully
from player_info import Player
import interact_game
import fight_manager
import money
import math
import keys
import asyncio
import consumable

from dataclasses import dataclass, field, KW_ONLY, replace

from typing import Optional
from typing import List

from discord.ext.commands import Context, Bot
from discord.abc import User
from discord import Thread
import discord

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select



DUNGEON_CHOICE_TIMEOUT = 60
THREAD_DELETE_AFTER = 60
COEF_XP_WIN = 1

ENEMIES_FIGHTER_PV = 5
COEF_XP_FIGHTER = 0.6
COEF_XP_BOSS = 0.6
COEF_GOLD_FIGHTER = 1
ENEMIES_BOSS_PV = 20
ENEMIES_GROUP_SIZE = 6


boss_rarity_lvl:dict[int, bully.Rarity] = {k:bully.Rarity.TOXIC for k in range(0,5)} | {k:bully.Rarity.MONSTER for k in range(5,20)} | {k:bully.Rarity.DEVASTATOR for k in range(20,35)} | {k:bully.Rarity.SUBLIME for k in range(35,50)}
fighter_rarities_lvl:dict[int, list[bully.Rarity]] = {k:[bully.Rarity.TOXIC] for k in range(0,10)} | {k:[bully.Rarity.TOXIC, bully.Rarity.MONSTER] for k in range(10,15)} | {k:[bully.Rarity.MONSTER] for k in range(15,25)} | {k:[bully.Rarity.MONSTER, bully.Rarity.DEVASTATOR] for k in range(25,30)} | {k:[bully.Rarity.DEVASTATOR] for k in range(30,40)} | {k:[bully.Rarity.DEVASTATOR, bully.Rarity.SUBLIME] for k in range(40,45)} | {k:[bully.Rarity.SUBLIME] for k in range(45,50)}

@dataclass
class DungeonFightingBully():
    pv_max:int
    name:str
    seed:bully.Seed
    exp_coef:float=COEF_XP_FIGHTER
    gold_coef:float=COEF_GOLD_FIGHTER
    buffs_tags:list[str] = field(default_factory=lambda: [])

    def init_fighting_bully(self, rarity, level):
        b = bully.Bully(name=self.name, rarity=rarity, must_load_image=False, max_pv=self.pv_max, seed=self.seed)
        for k in range(1, level) :
            b.level_up_one()
        self.fighting_bully = FightingBully.create_fighting_bully(b=b)
        self.fighting_bully.set_buffs(buffs_tags=self.buffs_tags)

    def reward_kill(self, bully_joueur) -> tuple[float, int]:
        if self.fighting_bully is None : 
            raise Exception("fighting bully must be initiated")
        (exp_earned, gold_earned) = fight_manager.reward_win_fight(bully_joueur, self.fighting_bully.bully)
        exp_earned *= self.exp_coef
        gold_earned = int(self.gold_coef * gold_earned)
        return (exp_earned, gold_earned)

dungeon_fighter_bully_list = [DungeonFightingBully(name="Thyr O'Flan", pv_max=5, seed=bully.Seed(0.2, 0.45, 0.2, 0.25)),
                              DungeonFightingBully(name="Grobrah Le Musclé", pv_max=7, seed=bully.Seed(0.65, 0.1, 0.2, 0.05)),
                              DungeonFightingBully(name="Fou Fur", pv_max=6, seed=bully.Seed(0.2, 0.2, 0.5, 0.1)),
                              DungeonFightingBully(name="wè wè", pv_max=6, seed=bully.Seed(0.4, 0.3, 0.1, 0.2)),
                              DungeonFightingBully(name="Craby", pv_max=6, seed=bully.Seed(0.2, 0.1, 0.4, 0.3)),
                              DungeonFightingBully(name="le gars qu'on choisit en dernier en sport et qui se venge", pv_max=5, seed=bully.Seed(0.1, 0.1, 0.45, 0.35)),
                              DungeonFightingBully(name="Plu Didier", pv_max=6, seed=bully.Seed(0.2, 0.4, 0.1, 0.3)),
                              DungeonFightingBully(name="Woah", pv_max=6, seed=bully.Seed(0.3, 0.3, 0.2, 0.2)),
                              DungeonFightingBully(name="Gros Problème", pv_max=8, seed=bully.Seed(0.35, 0.55, 0.01, 0.09), buffs_tags=["Rage"]),
                              DungeonFightingBully(name="Le Fourbe", pv_max=5, seed=bully.Seed(0.15, 0.1, 0.05, 0.65)),
                              DungeonFightingBully(name="Nulos", pv_max=5, seed=bully.Seed(0.1, 0.05, 0.40, 0.45))]

dungeon_fighters_lvl_50 = [DungeonFightingBully(name="Gardien", pv_max=13, seed=bully.Seed(1.3, 0.3, 0.4, 0.0), buffs_tags=["Brutal", "IronSkin"]),
                             DungeonFightingBully(name="Chimère", pv_max=10, seed=bully.Seed(0.5, 0.4, 0.7, 0.4), buffs_tags=["SharpTeeth"]),
                             DungeonFightingBully(name="David, ancien héros", pv_max=7, seed=bully.Seed(0.8, 1.0, 0.05, 0.3), buffs_tags=["CrystalSkin"]),
                             DungeonFightingBully(name="Ombre", pv_max=1, seed=bully.Seed(0.1, 1.2, 0.0, 1.2), buffs_tags=["ShadowMaster"]),
                             DungeonFightingBully(name="Azaan - Dragon Primordial - Maitre du donjon", pv_max=20, seed=bully.Seed(1.3, 0.6, 0.2, 0.2), buffs_tags=["Dragon"])
                            ]

# dungeon_fighters_lvl_666 = [DungeonFightingBully(name="The Devil - Phase 1", pv_max=13, seed=bully.Seed(1.3, 0.3, 0.4, 0.0), buffs_tags=["Brutal"]),]
dungeon_fighters_lvl_legendary = [DungeonFightingBully(name="Phoenix - L'oiseau magnifique", pv_max=14, seed=bully.Seed(0.4, 1.0, 0.7, 0.1), buffs_tags=["Adaptation", "FirePunch"]),
                              DungeonFightingBully(name="Phoenix - L'oeuf de résurrection", pv_max=16, seed=bully.Seed(1.0, 0.0, 0.1, 0.25), buffs_tags=["Adaptation", "FireAura"]),
                              DungeonFightingBully(name="Phoenix - L'abomination de flamme", pv_max=20, seed=bully.Seed(0.8, 0.6, 0.5, 0.1), buffs_tags=["Adaptation", "ExplosiveTouch", "FirePunch"])
                              ]

@dataclass
class Dungeon():
    ctx: Context
    bot: Bot
    player: Player
    level: int

    _: KW_ONLY

    size: int = ENEMIES_GROUP_SIZE

    user: discord.abc.User = field(init=False)
    current_floor: int  = field(init = False, default=0)
    enemies_fighters: List[FightingBully] = field(init=False)
    fighters_joueur: list[FightingBully] = field(init=False)
    xp_earned_bullies: List[float] = field(init=False)
    thread: Thread = field(init=False)

    reward_conso:consumable.Consumable|None = None

    def __post_init__(self):
        self.user = self.ctx.author
        self.name = f"Dungeon Level {self.level}"
        self.enemies_fighters = self.generate_dungeon_team()

        #On initialise les pv et xp gagné par les bullies
        self.fighters_joueur: List[FightingBully] = []
        self.xp_earned_bullies: List[float] = [] #L'xp gagné par chaque bully
        for b in self.player.get_equipe():
            new_fighter = FightingBully.create_fighting_bully(b)
            self.fighters_joueur.append(new_fighter)
            self.xp_earned_bullies.append(0)

    def generate_dungeon_team(self) -> List[FightingBully]:
        enemies_fighters:List[FightingBully] = []
        
        # Initialisation par défaut
        dungeon_fighters = []
        fighters_rarities = []

        # Configuration pour les niveaux spéciaux
        if self.level == 50:
            dungeon_fighters = dungeon_fighters_lvl_50
            fighters_rarities = [bully.Rarity.UNIQUE] * len(dungeon_fighters) 
            self.reward_conso = consumable.ConsumableElixirBuff("Dragon Blood", "Dragon")

        elif self.level == 111:
            self.level = 15
            self.name = "Legendary Boss Dungeon"
            dungeon_fighters = dungeon_fighters_lvl_legendary
            fighters_rarities = [bully.Rarity.UNIQUE] * len(dungeon_fighters)
            self.reward_conso = consumable.ConsumableElixirBuff("Phoenix's Feather", "Phoenix")

        # Configuration pour les autres niveaux
        else:
            dungeon_fighters = random.sample(dungeon_fighter_bully_list, self.size - 1)
            seed = bully.Seed.generate_seed_stat()
            boss_fighter = DungeonFightingBully(name="Boss", pv_max=ENEMIES_BOSS_PV, seed=seed, exp_coef=COEF_XP_BOSS)
            dungeon_fighters.append(boss_fighter)  # Ajout du boss en dernier
            fighters_rarities = [random.choice(fighter_rarities_lvl[self.level]) for _ in range(self.size - 1)] + [boss_rarity_lvl[self.level]]

        # Initialisation des combattants avec les raretés définies
        for df, rarity in zip(dungeon_fighters, fighters_rarities):
            df.init_fighting_bully(rarity=rarity, level=self.level)
            if df.fighting_bully is None:
                raise Exception("L'initialisation n'a pas été bien faite")
            enemies_fighters.append(df.fighting_bully)

        return enemies_fighters

    async def enter(self) -> None:
        message = await self.ctx.channel.send(f"{self.ctx.author.mention} enters the {self.name}")
        try :
            self.thread = await self.ctx.channel.create_thread(name=f"{self.name}", message=message) #type: ignore
        except Exception as e:
            print(e)
            return
        #On fait la boucle de combat
        try:
            while self.current_floor < len(self.enemies_fighters):
                await self.handle_fight(can_switch=self.current_floor ==  len(self.enemies_fighters) - 1 or self.level==50)
                # self.reset_stats_bullies()

        except interact_game.CancelChoiceException as e:
            await self.thread.send(f"{self.ctx.author.name} cancelled the fight and left the dungeon")
        except asyncio.exceptions.TimeoutError as e:
            await self.thread.send(f"Your team left the dungeon. Choose faster next time {self.ctx.author}.")
        except IndexError as e:
            await self.thread.send(
                f"[{self.ctx.author}] -> You don't have this bully.\n" #TODO: fix with ui
                "Your team left the dungeon."
            )
        except Exception as e:
            print(e)

        else:
            #On est plus dans le combat, le joueur à vaincu le donjon
            #On écrit le message de victoire dans les 2 channels
            await self.ctx.channel.send(f"{self.ctx.author.name} has beaten the {self.name}!") 
            await self.thread.send(f"{self.ctx.author.name} has beaten the {self.name}!") 

            #on donne la récompense d'xp aux joueurs encore en vie
            for i,fighter in enumerate(self.fighters_joueur):
                xp_earned = self.xp_earned_bullies[i]
                if xp_earned > 0:
                    bully_joueur_recompense = fighter.bully
                    try:
                        bully_joueur_recompense.give_exp(round(xp_earned * COEF_XP_WIN, 1))
                    except bully.LevelUpException as lvl_except:
                        await self.thread.send(f"{bully_joueur_recompense.name} {lvl_except.text}")

            if self.reward_conso is not None :
                await consumable.add_conso_to_player(self.ctx, player=self.player, c=self.reward_conso, channel_cible=self.thread)

            #On maj le record du joueur sur son dungeon si nécessaire
            if self.level > self.player.max_dungeon:
                self.player.max_dungeon = self.level
        finally:
            await self.exit(THREAD_DELETE_AFTER)

    async def handle_fight(self, can_switch = False):
        #On affiche le prochain ennemy
        fighting_bully_enemy = self.enemies_fighters[self.current_floor]
        text_enemy_coming = f"An enemy is coming! {fighting_bully_enemy.bully.get_print(compact_print=True, current_hp=fighting_bully_enemy.pv)}"
        await self.thread.send(f"{bully.mise_en_forme_str(text_enemy_coming)}") 
        
        fighting_bully_joueur, num_bully_j = await interact_game.player_choose_fighting_bully(ctx=self.ctx, fighting_bullies=self.fighters_joueur, user=self.ctx.author, channel_cible=self.thread, timeout=DUNGEON_CHOICE_TIMEOUT)

        #On fait le combat.
        while True:
            try: 
                nb_swaps = math.inf if can_switch else 0
                fight = fight_manager.Fight(self.ctx, user_1=self.user, player_1=self.player, fighter_1=fighting_bully_joueur, fighter_2=fighting_bully_enemy, nb_swaps_1=nb_swaps, channel_cible=self.thread)
                fight.do_end_fight = False
                await fight.start_fight()
                
            #Permet de faire une interruption du combat et de changer de bully qui se bat.
            except fight_manager.InterruptionCombat as erreur:
                print(erreur)
                fighting_bully_joueur = await self.fighter_change(fighting_bully_joueur)
                num_bully_j = self.fighters_joueur.index(fighting_bully_joueur)
            else:
                break
        
        bully_joueur = fighting_bully_joueur.bully
        #On regarde qui a perdu (le joueur ou l'ennemi)
        if(fighting_bully_joueur.pv > 0) :
            #Le joueur a gagné. On calcul les récompenses, on les affiches et on les stocks
            (exp_earned, gold_earned) = fight_manager.reward_win_fight(bully_joueur, fighting_bully_enemy.bully)
            exp_earned *= COEF_XP_FIGHTER
            gold_earned = int(COEF_GOLD_FIGHTER * gold_earned)
            pretext = ""
            if (exp_earned > 0):
                try:
                    bully_joueur.give_exp(exp_earned)
                except bully.LevelUpException as lvl_except:
                    await self.thread.send(f"{bully_joueur.name} {lvl_except.text}")

                self.xp_earned_bullies[num_bully_j] += exp_earned
                pretext += f"{bully_joueur.name} earned {exp_earned} xp!\n"
            if (gold_earned > 0):
                money.give_money(self.player, montant=gold_earned)
                pretext += f"{self.ctx.author} earned {gold_earned}{money.MONEY_ICON}!\n"

            #On envoie le message de succès et on progress dans le dungeon
            await self.thread.send(f"{pretext}{fighting_bully_enemy.bully.name} is dead! You progress in the dungeon.")
            self.current_floor += 1

        else : 
            #Le joueur à perdu. 
            if bully_joueur.rarity == Rarity.NOBODY :
                await self.thread.send(f"{bully_joueur.name} died in terrible agony.")
                await bully_joueur.kill()
            else : 
                lvl_loss = max(1, math.floor(bully_joueur.lvl/5))
                lvl_loss = min(lvl_loss, bully_joueur.lvl - 1)
                bully_joueur.decrease_lvl(lvl_loss)
                await self.thread.send(f"{bully_joueur.name} lost {lvl_loss} level")
            self.fighters_joueur.pop(num_bully_j)
            self.xp_earned_bullies.pop(num_bully_j)

    async def fighter_change(self, fighter: FightingBully) -> FightingBully:
        try :
            fighter, new_num_bully_j = await interact_game.player_choose_fighting_bully(ctx=self.ctx, fighting_bullies=self.fighters_joueur, user=self.ctx.author, channel_cible=self.thread, timeout=DUNGEON_CHOICE_TIMEOUT)

        except interact_game.CancelChoiceException:
            await self.thread.send(f"{fighter.bully.name} stays in fight.")
        except asyncio.exceptions.TimeoutError:
            await self.thread.send(f"Too slow, {fighter.bully.name} stays in fight.")
        except IndexError:
            await self.thread.send(f"Error, {fighter.bully.name} stays in fight.")
        return fighter
    
    def reset_stats_bullies(self) -> None:
        for f in self.fighters_joueur :
            f.reset_stats()

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

