import os
import random
from bully import Bully, Rarity, LevelUpException, Stats
import bully
from fighting_bully import FightingBully, BuffFight, get_player_team, setup_buffs_team
import consumable
from consumable import Consumable
import interact_game
from fight_manager import Fight, InterruptionCombat, RecapExpGold, reward_win_fight
import money
import keys
import math
import asyncio
from player_info import Player
import buffs
import inspect

from typing import Any, Optional, overload, Type
from dataclasses import dataclass, field, KW_ONLY

from discord.ext.commands import Context, Bot
import discord
from all_texts import getText
from utils.manage_tread import del_thread_if_possible, create_thread_if_possible

RUIN_CHOICE_TIMEOUT = 60
THREAD_DELETE_AFTER = 60
MAX_PV_ENEMY = 8
COEF_XP_FIGHTER = 0.8
COEF_GOLD_FIGHTER = 1.0
MAX_PV_BOSS = 20

boss_rarity_lvl:dict[int, bully.Rarity] = {k:bully.Rarity.TOXIC for k in range(0,5)} | {k:bully.Rarity.MONSTER for k in range(5,20)} | {k:bully.Rarity.DEVASTATOR for k in range(20,35)} | {k:bully.Rarity.SUBLIME for k in range(35,50)}
fighter_rarities_lvl:dict[int, list[bully.Rarity]] = {k:[bully.Rarity.TOXIC] for k in range(0,10)} | {k:[bully.Rarity.TOXIC, bully.Rarity.MONSTER] for k in range(10,15)} | {k:[bully.Rarity.MONSTER] for k in range(15,25)} | {k:[bully.Rarity.MONSTER, bully.Rarity.DEVASTATOR] for k in range(25,30)} | {k:[bully.Rarity.DEVASTATOR] for k in range(30,40)} | {k:[bully.Rarity.DEVASTATOR, bully.Rarity.SUBLIME] for k in range(40,45)} | {k:[bully.Rarity.SUBLIME] for k in range(45,50)}

#On load les buffs récupérable
classes = [member[1] for member in inspect.getmembers(buffs) if inspect.isclass(member[1])]


class Trap :
    def __init__(self, level: int, rarity: Rarity, stat_index: int|None = None, damage = 4):
        init_R = rarity.base_points
        coef_R = rarity.coef_level_points

        self.difficulty = round((init_R + coef_R * level**2/2) /4) + 1
        if(stat_index == None):
            self.stat_str:str = ["strength", "agility", "lethality", "viciousness"][random.randint(0,3)]
        else :
            self.stat_str:str = ["strength", "agility", "lethality", "viciousness"][stat_index]
        self.damage = damage
        self.text_intro_en = ""
        self.text_reussite_en = ""
        self.text_echec_en = ""
        self.text_intro = ""
        self.text_reussite = ""
        self.text_echec = ""

        self.text_intro = getText(f"trap_{self.stat_str}_intro")
        self.text_reussite = getText(f"trap_{self.stat_str}_success")
        self.text_echec = getText(f"trap_{self.stat_str}_fail")

    def clash(self, fighter: FightingBully) -> bool:
        stat_value = getattr(fighter.stats, self.stat_str)
        vict = Bully.clash_stat(stat_value, self.difficulty)
        return vict
        

@dataclass
class EnemyRoom():
    enemy: FightingBully
    can_switch: bool = False

    @staticmethod
    def generate(level: int, rarity: Rarity) -> "EnemyRoom":
        max_pv_enemy = MAX_PV_ENEMY
        enemy = Bully("Enemy", rarity=rarity, must_load_image= False, max_pv= max_pv_enemy)
        for k in range(1, level) :
            enemy.level_up_one()
        enemy_fighter = FightingBully.create_fighting_bully(enemy)
        enemy_fighter.exp_coef = COEF_XP_FIGHTER
        enemy_fighter.gold_coef = COEF_GOLD_FIGHTER
        return EnemyRoom(enemy_fighter)
    
    async def interact(self, ruin: "Ruin") -> bool:
        await ruin.thread.send(getText("ruin_enemy_intro").format(enemy=bully.mise_en_forme_str(self.enemy.get_print())))
        # await ruin.thread.send(f"An enemy stands in your way! \n{bully.mise_en_forme_str(self.enemy.get_print())}")
        while True:
            fighter = await self.fighter_choice(ruin)
            fight_won = await self.fight(ruin, fighter)
            if fight_won:
                break
        return False
    
    async def fighter_choice(self, ruin: "Ruin") -> FightingBully:
        try :
            fighting_bully_joueur, num_bully_j = await interact_game.player_choose_fighting_bully(ctx=ruin.ctx, fighting_bullies=ruin.fighters_joueur, user=ruin.user, channel_cible=ruin.thread, timeout=RUIN_CHOICE_TIMEOUT)

        except interact_game.CancelChoiceException:
            raise
        except asyncio.exceptions.TimeoutError:
            raise #On propage l'exception
        except IndexError:
            raise #On propage l'exception
        except Exception:
            raise #On propage l'exception

        if (fighting_bully_joueur.pv <= 0):
            await ruin.thread.send(getText("ruin_bully_error"))
            # await ruin.thread.send(f"Your bully is dead or do not exist.\nYour team left the ruin.") 
            raise IndexError
        
        return fighting_bully_joueur
    
    async def fighter_change(self, ruin: "Ruin", fighter: FightingBully) -> FightingBully:
        try :
            fighter, new_num_bully_j = await interact_game.player_choose_fighting_bully(ctx=ruin.ctx, fighting_bullies=ruin.fighters_joueur, user=ruin.user, channel_cible=ruin.thread, timeout=RUIN_CHOICE_TIMEOUT)
        except interact_game.CancelChoiceException:
            await ruin.thread.send(getText("fighter_stay_in_fight").format(fighter_name=fighter.bully.name))
            # await ruin.thread.send(f"{fighter.bully.name} stays in fight.")
        except asyncio.exceptions.TimeoutError:
            await ruin.thread.send(getText("fighter_change_too_slow").format(fighter_name=fighter.bully.name))
            # await ruin.thread.send(f"Too slow, {fighter.bully.name} stays in fight.")
        except IndexError:
            await ruin.thread.send(getText("fighter_change_error").format(fighter_name=fighter.bully.name))
            # await ruin.thread.send(f"Error, {fighter.bully.name} stays in fight.")
        return fighter
    
    async def fight(self, ruin: "Ruin", fighter: FightingBully) -> bool:
        """Make the fighter and the enemy fight.
        Args:
            ruin (Ruin): The ruin the fight occurs in
            fighter (FightingBully): The fighter sent by the player
        Returns:
            bool: Was the enemy defeated?
        """
        print("stats fighting bully :", fighter.stats)
        while True:
            try: 
                nb_swaps = math.inf if self.can_switch else 0
                fight = Fight(ruin.ctx, user_1=ruin.user, player_1=ruin.player, fighter_1=fighter, fighter_2=self.enemy, nb_swaps_1=nb_swaps, channel_cible=ruin.thread, can_be_timeout_damage_2=False)
                recapExpGold:RecapExpGold = await fight.start_fight()

            #Permet de faire une interruption du combat et de changer de bully qui se bat.
            except InterruptionCombat as erreur:
                print(erreur)
                fighter = await self.fighter_change(ruin, fighter)
            else:
                break
        
        pv_restant_joueur = fighter.pv
        bully_joueur = fighter.bully

        #On regarde qui a perdu (le joueur ou l'ennemi)
        if(pv_restant_joueur > 0) :
            #Le joueur a gagné
            is_success = True

            #On calcule les récompenses, on les affiches et on les stock
            (exp_earned, gold_earned) = recapExpGold.exp_earned, recapExpGold.gold_earned

            if (exp_earned > 0):
                try:
                    bully_joueur.give_exp(exp_earned)
                except LevelUpException as lvl_except:
                    await ruin.thread.send(f"{bully_joueur.name} {lvl_except.text}")
                
            if (gold_earned > 0):
                money.give_money(ruin.player, montant=gold_earned)

            #On envoie le message de succès et on progress dans le dungeon
            await ruin.thread.send(getText("ruin_enemy_defeated").format(enemy = self.enemy.bully.name))
            # await ruin.thread.send(f"{self.enemy.bully.name} is dead! You progress in the ruin.")
            
        else : 
            #Le joueur à perdu
            is_success = False

            #On tue le bully qui est ded
            ruin.fighters_joueur.remove(fighter)

        return is_success

@dataclass
class ConsoRoom():
    conso: Consumable

    @staticmethod
    def generate(level: int, rarity: Rarity) -> "ConsoRoom":
        if random.random() < 0.33:
            Buff = random.choice(buffs.BuffsLVL[math.floor(level/10)])
            buff_tag = Buff.__name__
            conso = consumable.ConsumableElixirBuff(getText("elixir_of").format(elixir = buff_tag), buff_tag)
        else :
            valeur = round(level * rarity.coef_level_points) 
            aliment = random.choice(list(consumable.AlimentEnum))
            conso = aliment.new_conso(value=valeur)
        return ConsoRoom(conso)
    
    async def interact(self, ruin: "Ruin"):
        await ruin.thread.send(getText("found_conso").format(name=self.conso.name))
        await consumable.add_conso_to_player(ruin.ctx, ruin.player, self.conso, channel_cible=ruin.thread)


@dataclass
class BossRoom(EnemyRoom, ConsoRoom): 

    @staticmethod
    def generate(level: int, rarity: Rarity) -> "BossRoom":
        max_pv_boss:int = MAX_PV_BOSS

        boss = Bully("BOSS", rarity=rarity, must_load_image=False, max_pv=max_pv_boss)
        for _ in range(1, level) :
            boss.level_up_one()
        boss_conso = ConsoRoom.generate(level, rarity).conso
        boss_conso.apply(boss)
        boss_fighter = FightingBully.create_fighting_bully(boss)
        return BossRoom(boss_conso, boss_fighter, can_switch = True) #reverse MRO for dataclasses
    
    async def interact(self, ruin: "Ruin"):
        await EnemyRoom.interact(self, ruin)
        await ConsoRoom.interact(self, ruin)

        return True

@dataclass
class TreasureRoom():
    gold:int

    @staticmethod
    def generate(level: int) -> "TreasureRoom":
        gold = int(0.35 * level**2 + 10)
        return TreasureRoom(gold=gold)

    async def interact(self, ruin: "Ruin"):
        await ruin.thread.send(getText("found_treasure").format(gold=self.gold, money_emoji=money.MONEY_EMOJI))
        # await ruin.thread.send(f"You find a **treasure**. It contains **{self.gold}** {money.MONEY_EMOJI}!")
        money.give_money(ruin.player, montant=self.gold)

@dataclass
class TrapRoom():
    trap: Trap

    @staticmethod
    def generate(level: int, rarity: Rarity) -> "TrapRoom":
        trap = Trap(level, rarity)
        return TrapRoom(trap)
    
    async def interact(self, ruin: "Ruin"):
        await ruin.thread.send(self.trap.text_intro)
        fighter:FightingBully = await self.fighter_choice(ruin)
        success = self.trap.clash(fighter)
        if success:
            await ruin.thread.send(self.trap.text_reussite)
        else:
            await ruin.thread.send(self.trap.text_echec)
            fighter.pv -= self.trap.damage
            if fighter.pv <= 0:
                ruin.fighters_joueur.remove(fighter)
                await ruin.thread.send(getText("bully_is_dead").format(bully=fighter.bully.name))
                # await ruin.thread.send(f"{fighter.bully.name} is dead.")
        
        return

    async def fighter_choice(self, ruin: "Ruin") -> FightingBully:
        try :
            fighting_bully_joueur, num_bully_j = await interact_game.player_choose_fighting_bully(ctx=ruin.ctx, fighting_bullies=ruin.fighters_joueur, user=ruin.user, channel_cible=ruin.thread, timeout=RUIN_CHOICE_TIMEOUT)

        except interact_game.CancelChoiceException:
            raise
        except asyncio.exceptions.TimeoutError:
            raise #On propage l'exception
        except IndexError:
            raise #On propage l'exception
        except Exception:
            raise #On propage l'exception

        if (fighting_bully_joueur.pv <= 0):
            await ruin.thread.send(getText("ruin_bully_error"))
            # await ruin.thread.send(f"Your bully is dead or do not exist.\nYour team left the ruin.") 
            raise IndexError

        return fighting_bully_joueur

@dataclass
class RegenRoom():
    #TODO
    pass

    async def interact(self, ruin: "Ruin") -> bool:
        #TODO
        return False
        

Room = BossRoom | EnemyRoom | TrapRoom | RegenRoom | TreasureRoom |ConsoRoom

@dataclass
class Ruin():
    ctx: Context
    bot: Bot
    player: Player
    level: int

    _ : KW_ONLY

    rarity_level: (Rarity | None) = field(default=None)

    user: discord.abc.User = field(init=False)
    rooms: list[Room] = field(init=False, default_factory=list)
    thread: discord.abc.Messageable = field(init=False)
    fighters_joueur: list[FightingBully] = field(init=False, default_factory=list)


    def __post_init__(self):
        self.user = self.ctx.author
        self.generate()

    def generate(self) -> None:
        nb_salle_enemy = 4
        nb_salle_treasure = 1
        nb_salle_item = 0
        nb_salle_regen = 0
        nb_salle_trap = 1

        fighter_rarities:list[bully.Rarity] = fighter_rarities_lvl[self.level - 1]
        boss_rarity:bully.Rarity = boss_rarity_lvl[self.level-1]
        self.rarity_level = boss_rarity

        all_fighters_enemy:list[FightingBully] = []
        
        #Ajout salle boss à la fin
        boss_room = BossRoom.generate(self.level, boss_rarity)  
        self.rooms.append(boss_room)
        all_fighters_enemy.append(boss_room.enemy)

        #Ajout salle Treasure
        for _ in range(nb_salle_treasure):
            self.rooms.append(TreasureRoom.generate(self.level))

        #Ajout salle trap
        for _ in range(nb_salle_trap):
            self.rooms.append(TrapRoom.generate(self.level, rarity=boss_rarity))
        #Ajout salle Enemy
        for _ in range(nb_salle_enemy):
            rarity = random.choice(fighter_rarities)
            new_room = EnemyRoom.generate(self.level, rarity)
            self.rooms.append(new_room)
            all_fighters_enemy.append(new_room.enemy)
        
        setup_buffs_team(all_fighters_enemy, is_team_buff_active=True)


    async def enter(self) -> None:
        message = await self.ctx.channel.send(getText("ruin_enter").format(user=self.user.mention, level=self.level))
        self.thread = await create_thread_if_possible(self.ctx, name=f"Ruin - Level {self.level}", message=message)
        # try :
        #     self.thread = await self.ctx.channel.create_thread(name=f"Ruin - Level {self.level}", message=message) #type: ignore
        # except Exception as e:
        #     print(e)
        #     return

        #On initialise les pv des bullies
        self.fighters_joueur = get_player_team(player=self.player)

        try: 
            # Pop removes the last item
            while not await self.rooms.pop().interact(self):
                pass
            
            await self.thread.send(getText("ruin_victory").format(user=self.user))
        except interact_game.CancelChoiceException as e:
            await self.thread.send(getText("ruin_cancelled").format(user=self.user.name))
        except asyncio.exceptions.TimeoutError as e:
            await self.thread.send(getText("ruin_team_timeout").format(user=self.user))
        except IndexError as e:
            await self.thread.send(getText("ruin_bully_error"))
        else :
            if self.level > self.player.max_ruin:
                self.player.max_ruin = self.level
        finally:
            await self.exit()

    def reset_stats_bullies(self) -> None:
        for f in self.fighters_joueur :
            f.reset_stats()

    async def exit(self, time_bfr_close_thread=THREAD_DELETE_AFTER) -> None:
        await del_thread_if_possible(self.thread, time_bfr_close_thread)
        # try:
        #     await del_thread(self.thread, time_bfr_close_thread)
        # except Exception as e:
        #     print(e)
        


