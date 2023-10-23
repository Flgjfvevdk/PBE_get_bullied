import os
import random
from bully import Bully, Rarity
import bully
from fighting_bully import FightingBully
from item import Item, ItemStats, Seed
import interact_game
import fight_manager
import money
import pickle
import asyncio
from player_info import Player

from enum import Enum

from typing import Any, Optional, overload
from typing import List
from dataclasses import dataclass, field, KW_ONLY

from discord.ext.commands import Context, Bot
import discord

import utils

RUIN_CHOICE_TIMEOUT = 30
THREAD_DELETE_AFTER = 90
FIGHTER_CHOICE_TIMEOUT = 20

class Trap :
    def __init__(self, level: int, rarity: Rarity, stat_index: int|None = None, damage = 3):
        init_R = rarity.points_bonus
        coef_R = rarity.level_bonus

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
            self.text_intro = "The door to the next room is at the top of a ruined stone starcase. One must climb and tie a rope on top to create a path"
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

@dataclass
class EnemyRoom():
    enemy: FightingBully
    can_switch: bool = False

    @staticmethod
    def generate(level: int, rarity: Rarity) -> "EnemyRoom":
        max_pv_enemy = 5
        enemy = Bully("enemy", rarity=rarity, must_load_image= False, max_pv= max_pv_enemy)
        for k in range(1, level) :
            enemy.level_up_one()
        enemy_fighter = FightingBully.create_fighting_bully(enemy)
        return EnemyRoom(enemy_fighter)
    
    async def interact(self, ruin: "Ruin") -> bool:
        #await ruin.fight_manage(self.enemy)
        await ruin.thread.send(f"An enemy stands in your way! \n{bully.mise_en_forme_str(self.enemy.combattant.get_print(compact_print=True))}")
        while True:
            fighter = await self.fighter_choice(ruin)
            fight_won = await self.fight(ruin, fighter)
            if fight_won:
                break
        return False
    
    async def fighter_choice(self, ruin: "Ruin") -> FightingBully:
        try :
            _, num_bully_j = await interact_game.player_choose_bully(ruin.ctx, ruin.user, ruin.player, ruin.bot, channel_cible=ruin.thread, timeout=RUIN_CHOICE_TIMEOUT)
        except TimeoutError:
            await ruin.thread.send(f"Your team left the ruin. Choose faster next time {ruin.user.mention}!") 
            raise #On propage l'exception
        except IndexError:
            await ruin.thread.send(
                f"[{ruin.user.mention}] -> you don't have that bully.\n"
                "Your team left the ruin.") 
            raise #On propage l'exception
        except Exception:
            raise #On propage l'exception

        fighting_bully_joueur = ruin.fighters_joueur[num_bully_j]
        if (fighting_bully_joueur.pv <= 0):
            await ruin.thread.send(f"Your bully is dead or do not exist.\nYour team left the ruin.") 
            raise IndexError
        
        return fighting_bully_joueur
    
    async def fighter_change(self, ruin: "Ruin", fighter: FightingBully) -> FightingBully:
        try :
            _, new_num_bully_j = await interact_game.player_choose_bully(ruin.ctx, ruin.user, ruin.player, ruin.bot, channel_cible=ruin.thread, timeout=FIGHTER_CHOICE_TIMEOUT)
            fighter = ruin.fighters_joueur[new_num_bully_j]
        except TimeoutError as e:
            await ruin.thread.send(f"Too slow, {fighter.combattant.name} stays in fight.")
        except IndexError as e:
            await ruin.thread.send(f"Error, {fighter.combattant.name} stays in fight.")
        return fighter
    
    async def fight(self, ruin: "Ruin", fighter: FightingBully) -> bool:
        """Make the fighter and the enemy fight.

        Args:
            ruin (Ruin): The ruin the fight occurs in
            fighter (FightingBully): The fighter sent by the player

        Returns:
            bool: Was the enemy defeated?
        """
        while True:
            try: 
                await fight_manager.fight_simulation(ruin.ctx, bot=ruin.bot, 
                                    fighting_bully_1=fighter, fighting_bully_2=self.enemy,
                                    user_1=ruin.user, is_switch_possible=self.can_switch,
                                    channel_cible=ruin.thread)
                
            #Permet de faire une interruption du combat et de changer de bully qui se bat.
            except fight_manager.InterruptionCombat as erreur:
                print(erreur)
                fighter = await self.fighter_change(ruin, fighter)
            else:
                break
        
        pv_restant_joueur = fighter.pv
        #pv_restant_enemy = enemy.pv
        bully_joueur = fighter.combattant

        #On regarde qui a perdu (le joueur ou l'ennemi)
        if(pv_restant_joueur > 0) :
            #Le joueur a gagné
            is_success = True

            #On calcule les récompenses, on les affiches et on les stock
            (exp_earned, gold_earned) = fight_manager.reward_win_fight(bully_joueur, self.enemy.combattant)
            pretext = ""
            if (exp_earned > 0):
                bully_joueur.give_exp(exp_earned)
                pretext += f"{fighter.combattant.name} earned {exp_earned} xp\n"
            if (gold_earned > 0):
                money.give_money(ruin.player, montant=gold_earned)
                pretext += f"{ruin.user.name} earned {gold_earned}{money.MONEY_ICON}\n"

            #On envoie le message de succès et on progress dans le dungeon
            await ruin.thread.send(f"{pretext}{self.enemy.combattant.name} is dead! You progress in the ruin.")
            
        else : 
            #Le joueur à perdu
            is_success = False

            #On tue le bully qui est ded
            await ruin.thread.send(f"{fighter.combattant.name} died in terrible agony")
            await fighter.combattant.kill()
            ruin.fighters_joueur.remove(fighter)

        return is_success

@dataclass
class ItemRoom():
    item: Item

    @staticmethod
    def generate(level: int, rarity: Rarity) -> "ItemRoom":
        item_list: list[Item] = []
        item_list.append(Item(name="Str - x0.5", is_bfr_fight= True, buff_start_self=ItemStats(1,0,0,0,0), buff_start_self_mult_lvl=Seed(0.5, 0, 0, 0)))
        item_list.append(Item(name="Str - x1", is_bfr_fight= True, buff_start_self=ItemStats(1,0,0,0,0), buff_start_self_mult_lvl=Seed(1, 0, 0, 0)))
        item_list.append(Item(name="Agi - x0.5", is_bfr_fight= True, buff_start_self=ItemStats(0,1,0,0,0), buff_start_self_mult_lvl=Seed(0, 0.5, 0, 0)))
        item_list.append(Item(name="Agi - x2", is_bfr_fight= True, buff_start_self=ItemStats(0,1,0,0,0), buff_start_self_mult_lvl=Seed(0, 2, 0, 0)))
        item_list.append(Item(name="Letha - x0.5", is_bfr_fight= True, buff_start_self=ItemStats(0,0,1,0,0), buff_start_self_mult_lvl=Seed(0, 0, 0.5, 0)))
        item_list.append(Item(name="Vic - x0.5", is_bfr_fight= True, buff_start_self=ItemStats(0,0,0,1,0), buff_start_self_mult_lvl=Seed(0, 0, 0, 0.5)))
        item_list.append(Item(name="HP - 5", is_bfr_fight= True, buff_start_self=ItemStats(0,0,0,0,5)))
        item = random.choice(item_list)
        item = Item(name="HP + 5", is_bfr_fight= True, buff_start_self=ItemStats(0,0,0,0,5))
        return ItemRoom(item)
    
    async def interact(self, ruin: "Ruin"):
        await ruin.thread.send(f"You found an item: {self.item.name}!")
        await interact_game.add_item_to_player(ruin.ctx, ruin.player, self.item, channel_cible=ruin.thread)

    
@dataclass
class BossRoom(EnemyRoom, ItemRoom): 

    @staticmethod
    def generate(level: int, rarity: Rarity) -> "BossRoom":
        max_pv_boss:int = 20

        boss = Bully("BOSS", rarity=rarity, must_load_image=False, max_pv=max_pv_boss)
        for _ in range(1, level) :
            boss.level_up_one()
        boss_item = ItemRoom.generate(level, rarity).item
        boss_fighter = FightingBully.create_fighting_bully(boss, boss_item)

        fight_manager.apply_effect_item_before_fight(fighter_self=boss_fighter)

        return BossRoom(boss_item, boss_fighter, can_switch = True) #reverse MRO for dataclasses
    
    async def interact(self, ruin: "Ruin"):
        await EnemyRoom.interact(self, ruin)
        await ItemRoom.interact(self, ruin)

        return True



@dataclass
class TrapRoom():
    trap: Trap

    @staticmethod
    def generate(level: int, rarity: Rarity) -> "TrapRoom":
        trap = Trap(level, rarity)
        return TrapRoom(trap)
    
    async def interact(self, ruin: "Ruin") -> bool:
        #TODO
        return False

@dataclass
class RegenRoom():
    #TODO
    pass

    async def interact(self, ruin: "Ruin") -> bool:
        #TODO
        return False
        

Room = BossRoom | EnemyRoom | ItemRoom | TrapRoom | RegenRoom

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
    thread: discord.Thread = field(init=False)
    fighters_joueur: list[FightingBully] = field(init=False, default_factory=list)


    def __post_init__(self):
        self.user = self.ctx.author
        self.generate()

    def generate(self) -> None:
        nb_salle_enemy = 4
        nb_salle_item = 0
        nb_salle_regen = 0
        nb_salle_trap = 0

        if (self.rarity_level == None):
            if(self.level <= 10):
                self.rarity_level = Rarity(0)
            elif(self.level <= 25):
                self.rarity_level = Rarity(1)
            elif(self.level <= 35):
                self.rarity_level = Rarity(2)
            elif(self.level <= 45):
                self.rarity_level = Rarity(3)
            else:
                self.rarity_level = Rarity(4)

        #Ajout salle boss
        self.rooms.append(BossRoom.generate(self.level, self.rarity_level))
        #Ajout salle Enemy
        for _ in range(nb_salle_enemy):
            self.rooms.append(EnemyRoom.generate(self.level, self.rarity_level))
        #Ajout salle Item
        for _ in range(nb_salle_item):
            self.rooms.append(ItemRoom.generate(self.level, self.rarity_level))
        # #Ajout salle Regen
        # for k in range(nb_salle_regen):
        #    Salles_ruine.append(Type_salle_ruine.REGEN)
        #Ajout salle Trap
        for _ in range(nb_salle_trap):
            self.rooms.append(TrapRoom.generate(self.level, self.rarity_level))

        random.shuffle(self.rooms)

    async def enter(self) -> None:
        message = await self.ctx.channel.send(f"{self.user.mention} enters a mysterious ruin [lvl : {self.level}]")
        try :
            self.thread = await self.ctx.channel.create_thread(name=f"Ruin - Level {self.level}", message=message) #type: ignore
        except Exception as e:
            print(e)
            return

        #On initialise les pv des bullies
        #pv_team_joueur = [] #pv du bully n°index. Si bully n°index n'existe pas alors -1
        self.fighters_joueur = [FightingBully.create_fighting_bully(b) for b in self.player.bullies]

        try: 
            while not await self.rooms.pop().interact(self):
                pass

            await self.thread.send(f"Congratulation {self.user}, you beat the boss and won their item!")
        except (TimeoutError, IndexError):
            pass
        finally:
            await self.exit()

    async def exit(self, time_bfr_close_thread=THREAD_DELETE_AFTER) -> None:
        try:
            async def delete_thread():
                await asyncio.sleep(time_bfr_close_thread)
                await self.thread.delete()
            asyncio.create_task(delete_thread())
        except Exception as e:
            print(e)
        

