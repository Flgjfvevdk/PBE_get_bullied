import os
import random

import discord
from bully import Bully, Stats, LevelUpException, Rarity
import fighting_bully
from fighting_bully import FightingBully, get_player_team
import interact_game
import money
import asyncio
import math

from discord.ext.commands import Context, Bot
from player_info import Player
from typing import Optional, Dict
from dataclasses import replace
import utils.color_str  as color_str
from utils.color_str import CText
from utils.manage_tread import del_thread, create_thread
from tournament import tournaments

CHOICE_TIMEOUT = 30
RECAP_MAX_EMOJI = 15
FIGHT_MSG_TIME_UPDATE = 1.0

TIMEOUT_START_ROUND = 100
TIMEOUT_DELAIE_INCREASE_DAMAGE = 10
DELAIE_DELETE_THREAD_FIGHT = 30
from all_texts import getText

async def proposition_fight(ctx:Context, user_1:discord.abc.User, user_2:discord.abc.User, player_1: Player, player_2: Player, bot: Bot, for_fun = False):
    text_challenge = getText("challenge_fight").format(user1=user_1.mention, user2=user_2.mention)
    if for_fun :
        text_challenge = getText("challenge_fight_for_fun").format(user1=user_1.mention, user2=user_2.mention)

    #On créer l'event qui sera set quand le bouton sera cliqué par user_2. La valeur du bouton (de la réponse) sera stocké dans var
    event = asyncio.Event()
    var:Dict[str, bool] = {"choix" : False}

    if(user_1 != user_2):
        #On affiche le message
        message = await ctx.channel.send(content=text_challenge, view=interact_game.ViewYesNo(user=user_2, event=event, variable_pointer = var))

        #On attend que le joueur clique sur un bouton
        try:
            await asyncio.wait_for(event.wait(), timeout=CHOICE_TIMEOUT)
        except asyncio.exceptions.TimeoutError as e:
            await message.reply(getText("challenge_too_late").format(user1=user_1.name, user2=user_2.name))
            return
        #On récup le choix
        challenge_accepte:bool = var["choix"]
    else : 
        message = await ctx.channel.send(content=text_challenge)
        challenge_accepte = True

    #On affiche le choix de user_2
    if(challenge_accepte) : 
        message_accept = await message.reply(getText("challenge_accepted"))
    else : 
        await message.reply(getText("challenge_declined"))
        return
    
    # thread_challenge = await ctx.channel.create_thread(name=getText("title_challenge").format(user1= user_1.name, user2=user_2.name), message=message_accept) #type: ignore
    thread_challenge = await create_thread(ctx, getText("title_challenge").format(user1= user_1.name, user2=user_2.name), message=message_accept)

    #On selectionne les 2 combattants
    try :
        fighter_1, fighter_2 = await select_fighters(ctx, user_1, user_2, player_1, player_2, channel_cible=thread_challenge)

        #On commence le combat
        fight = Fight(ctx=ctx, user_1=user_1, user_2=user_2, player_1=player_1, player_2=player_2, fighter_1=fighter_1, fighter_2=fighter_2, for_fun=for_fun,
                    channel_cible=thread_challenge)
        await fight.start_fight()
    finally:
        await del_thread(thread=thread_challenge, time_bfr_close=DELAIE_DELETE_THREAD_FIGHT)
    return

async def select_fighters(ctx: Context, user_1: discord.abc.User, user_2: discord.abc.User, player_1: Player, player_2: Player
                          , talkative:bool = False
                          , channel_cible = None) -> tuple[FightingBully, FightingBully]:
    if(channel_cible == None):
        channel_cible = ctx.channel
    
    try:
        bully_1 = await interact_game.select_bully(ctx, user_1, player_1, timeout = CHOICE_TIMEOUT, channel_cible=channel_cible)
        fighting_bully_1 = FightingBully.create_fighting_bully(bully_1)
        if talkative : await channel_cible.send(getText("challenge_selected_bully").format(user=user_1.name, bully=bully_1.name, lvl=bully_1.lvl))
    except asyncio.exceptions.TimeoutError as e:
        await channel_cible.send(getText("timeout_choose_faster").format(user=user_1.name))
        raise e
    except interact_game.CancelChoiceException as e:
        await channel_cible.send(getText("fight_cancel").format(user=user_1.name))
        raise e
    try:
        bully_2 = await interact_game.select_bully(ctx, user_2, player_2, timeout = CHOICE_TIMEOUT, channel_cible=channel_cible)
        fighting_bully_2 = FightingBully.create_fighting_bully(bully_2)
        if talkative : await channel_cible.send(getText("challenge_selected_bully").format(user=user_2.name, bully=bully_2.name, lvl=bully_2.lvl))
    except asyncio.exceptions.TimeoutError as e:
        await channel_cible.send(getText("fight_cancel").format(user=user_2.name))
        raise e
    except interact_game.CancelChoiceException as e:
        await channel_cible.send(getText("fight_cancel").format(user=user_2.name))
        raise e
    
    return fighting_bully_1, fighting_bully_2

class RecapExpGold:
    def __init__(self, exp_earned:float, gold_earned:int):
        self.exp_earned = exp_earned
        self.gold_earned = gold_earned

class Fight():
    def __init__(self, ctx:Context, fighter_1:FightingBully, fighter_2:FightingBully, user_1: discord.abc.User|None = None, user_2: discord.abc.User|None=None
                 , player_1: Player|None=None, player_2: Player|None = None, for_fun = False, channel_cible = None, nb_swaps_1:float = 0, nb_swaps_2:float = 0,
                 can_be_timeout_damage_1:bool = True, can_be_timeout_damage_2:bool = True):
        self.ctx = ctx
        self.user_1 = user_1
        self.user_2 = user_2
        self.player_1 = player_1
        self.player_2 = player_2
        self.fighter_1 = fighter_1
        self.fighter_2 = fighter_2
        self.for_fun = for_fun
        if(channel_cible is None):
            channel_cible = ctx.channel
        self.channel_cible:discord.abc.Messageable = channel_cible

        self.max_pv_1 = self.fighter_1.bully.max_pv
        self.max_pv_2 = self.fighter_2.bully.max_pv

        self.message_1:discord.Message
        self.message_mid:discord.Message
        self.message_2:discord.Message
        self.emojis_recap:list[list["str"]]= [[],[]]
        self.tour = random.randint(0,1)
        self.nb_rounds = 0

        self.nb_swaps_1 = nb_swaps_1 if isinstance(user_1, discord.abc.User) else 0
        self.nb_swaps_2 = nb_swaps_2 if isinstance(user_2, discord.abc.User) else 0

        self.users_can_swap:list[discord.abc.User] = []
        self.events_click_swap:list[asyncio.Event] = []
        self.labels_swap:list[str] = []
        if self.nb_swaps_1 > 0 and self.user_1:
            self.users_can_swap.append(self.user_1)
            self.events_click_swap.append(asyncio.Event())
            self.labels_swap.append(f"Swap j1 {(': ' + str(self.nb_swaps_1)) if self.nb_swaps_1 < math.inf else ''}")
        if self.nb_swaps_2 > 0 and self.user_2:
            self.users_can_swap.append(self.user_2)
            self.events_click_swap.append(asyncio.Event())
            self.labels_swap.append(f"Swap j2 {(': ' + str(self.nb_swaps_2)) if self.nb_swaps_2 < math.inf else ''}")

        self.can_be_timeout_damage_1 = can_be_timeout_damage_1
        self.can_be_timeout_damage_2 = can_be_timeout_damage_2

    async def start_fight(self):
        await self.apply_buff_before_fight()
        await self.channel_cible.send("``` ```")
        await self.setup_message()
        await asyncio.sleep(FIGHT_MSG_TIME_UPDATE)

        while self.fighter_1.pv > 0 and self.fighter_2.pv > 0 :
            await self.play_round()

            await self.update_message()
            await asyncio.sleep(FIGHT_MSG_TIME_UPDATE)

            #On regarde si changement nécessaire 
            if((self.nb_swaps_1 > 0 or self.nb_swaps_2 > 0) and self.fighter_1.pv > 0 and self.fighter_2.pv > 0) : 
                for k in range(len(self.users_can_swap)):
                    if self.events_click_swap[k].is_set():
                        raise InterruptionCombat(self.fighter_1.pv, self.fighter_2.pv, user_interrupt=self.users_can_swap[k])
          
        recapExpGold = await self.end_fight()
        return recapExpGold

    async def play_round(self):
        self.nb_rounds += 1
        self.apply_timeout_damage()
        
        pv_perdu = 0
        attacker, defender = (self.fighter_1, self.fighter_2) if self.tour == 0 else (self.fighter_2, self.fighter_1)
        recap_round = fighting_bully.RecapRound(attacker, defender, False, False, False, False, 0)

        if challenge_agility(defender.stats, attacker.stats):
            self.tour ^= 1 
            attacker, defender = (self.fighter_1, self.fighter_2) if self.tour == 0 else (self.fighter_2, self.fighter_1)
            recap_round.attacker = attacker
            recap_round.defender = defender
            recap_round.is_success_agility = True
        
        if challenge_block(attacker.stats, defender.stats) :
            recap_round.is_success_block = True
            if challenge_viciousness(attacker.stats, defender.stats):
                recap_round.vicious_target_str = defender.stats.max_stat()
                malus_vicious = apply_viciousness(attacker.stats, defender.stats, is_attack_success=False, is_attacker=True)
                self.emojis_recap[0].append("🗡️" if self.tour==0 else "🛡️")
                self.emojis_recap[1].append("🛡️" if self.tour==0 else "🗡️")
                recap_round.is_success_vicious = True
                recap_round.malus_vicious = malus_vicious
            else : 
                self.emojis_recap[0].append( "👊" if self.tour==0 else "🛡️")
                self.emojis_recap[1].append( "🛡️" if self.tour==0 else "👊")
        else :
            lethal_buff = challenge_lethality(attacker.stats, defender.stats)
            lethal_buff += 1 if lethal_buff > 1 else 0
            em_att = "👊"
            em_def = "🩸"
            if lethal_buff > 0 :
                pv_perdu = 1 + lethal_buff
                defender.pv -= pv_perdu
                em_att = "🔪"
                em_def = "💥"
                recap_round.is_success_lethal = True
                recap_round.damage_receive_defender = pv_perdu
                recap_round.damage_bonus_lethal = lethal_buff
            else :
                pv_perdu = 1
                defender.pv -= pv_perdu
                recap_round.damage_receive_defender = pv_perdu
            
            if challenge_viciousness(attacker.stats, defender.stats):
                recap_round.vicious_target_str = defender.stats.max_stat()
                malus_vicious = apply_viciousness(attacker.stats, defender.stats, is_attack_success=True, is_attacker=True)
                em_att = "🔪" if lethal_buff > 0 else "🗡️"
                em_def = "💔"
                recap_round.is_success_vicious = True
                recap_round.malus_vicious = malus_vicious

            self.emojis_recap[0].append(em_att if self.tour==0 else em_def)
            self.emojis_recap[1].append(em_def if self.tour==0 else em_att)

        self.tour ^= 1 

        await self.apply_buff_fight(recap_round=recap_round)
        return
    
    def apply_timeout_damage(self):
        if self.nb_rounds > TIMEOUT_START_ROUND:
            diff_rounds = self.nb_rounds - TIMEOUT_START_ROUND
            damage = 1 + diff_rounds // TIMEOUT_DELAIE_INCREASE_DAMAGE
            if (self.can_be_timeout_damage_1):
                self.fighter_1.pv -= damage
                self.emojis_recap[0].append("💀")
            else : 
                self.emojis_recap[0].append("👻")
            if (self.can_be_timeout_damage_2):
                self.fighter_2.pv -= damage
                self.emojis_recap[1].append("💀")
            else : 
                self.emojis_recap[1].append("👻")

    async def apply_buff_before_fight(self):
        for b in self.fighter_1.buffs:
            b.before_fight(fighter=self.fighter_1, opponent=self.fighter_2)
        for b in self.fighter_2.buffs:
            b.before_fight(fighter=self.fighter_2, opponent=self.fighter_1)

    async def apply_buff_fight(self, recap_round:fighting_bully.RecapRound):
        damage_j1, damage_j2 = 0, 0
        for b in self.fighter_1.buffs:
            d1, d2 = b.apply_damage(fighter=self.fighter_1, opponent=self.fighter_2, recap_round=recap_round)
            damage_j1 += d1
            damage_j2 += d2
        for b in self.fighter_2.buffs:
            d2, d1 = b.apply_damage(fighter=self.fighter_2, opponent=self.fighter_1, recap_round=recap_round)
            damage_j1 += d1
            damage_j2 += d2
        recap_round.add_damage_receive(self.fighter_1, damage_j1)
        recap_round.add_damage_receive(self.fighter_2, damage_j2)

        heal_j1, heal_j2 = 0, 0
        for b in self.fighter_1.buffs:
            h1, h2 = b.apply_heal(fighter=self.fighter_1, opponent=self.fighter_2, recap_round=recap_round)
            heal_j1 += h1
            heal_j2 += h2
        for b in self.fighter_2.buffs:
            h2, h1 = b.apply_heal(fighter=self.fighter_2, opponent=self.fighter_1, recap_round=recap_round)
            heal_j1 += h1
            heal_j2 += h2
        recap_round.add_damage_receive(self.fighter_1, -heal_j1)
        recap_round.add_damage_receive(self.fighter_2, -heal_j2)

        for b in self.fighter_1.buffs:
            b.apply_effect(fighter=self.fighter_1, opponent=self.fighter_2, recap_round=recap_round)
        for b in self.fighter_2.buffs:
            b.apply_effect(fighter=self.fighter_2, opponent=self.fighter_1, recap_round=recap_round)

        for b in self.fighter_1.buffs:
            b.on_death(fighter=self.fighter_1, opponent=self.fighter_2, recap_round=recap_round)
        for b in self.fighter_2.buffs:
            b.on_death(fighter=self.fighter_2, opponent=self.fighter_1, recap_round=recap_round)

    async def end_fight(self) -> RecapExpGold:
        if(self.fighter_1.pv <= 0):
            bully_gagnant = self.fighter_2.bully 
            bully_perdant = self.fighter_1.bully 
            fighting_bully_perdant = self.fighter_1
            user_gagnant, user_perdant = self.user_2, self.user_1

        elif(self.fighter_2.pv <= 0):
            bully_gagnant = self.fighter_1.bully 
            bully_perdant = self.fighter_2.bully 
            fighting_bully_perdant = self.fighter_2
            user_gagnant, user_perdant = self.user_1, self.user_2
        else:
            raise Exception("aucun perdant?")
        
        text_recap_end = ""
        text_recap_end +=getText("fight_winner").format(winner=bully_gagnant.name) +  "\n"
        # await self.channel_cible.send(getText("fight_winner").format(winner=bully_gagnant.name))
        if (not self.for_fun) :
            bully_gagnant.increment_win_loose(win=True)
            bully_perdant.increment_win_loose(win=False)

            if (user_gagnant is None):
                (exp_earned, gold_earned) = (0, 0)
            else : 
                (exp_earned, gold_earned) = reward_win_fight(bully_gagnant, bully_perdant)
                exp_earned *= fighting_bully_perdant.exp_coef
                exp_earned = round(exp_earned, 1)
                gold_earned = int(gold_earned * fighting_bully_perdant.gold_coef)


            pretext = ""
            if (exp_earned > 0):
                txt_lvl = ""
                try :
                    bully_gagnant.give_exp(exp_earned)
                except LevelUpException as lvl_except:
                    txt_lvl = f"{bully_gagnant.name} {lvl_except.text}"
                
                text_recap_end += getText("gain").format(name=bully_gagnant.name, reward = exp_earned) + "xp\n"
                text_recap_end += txt_lvl + "\n"
            if (gold_earned > 0):
                player_gagnant = self.player_1 if bully_gagnant == self.fighter_1.bully else self.player_2
                if user_gagnant is not None and player_gagnant is not None:
                    money.give_money(player_gagnant, montant=gold_earned)
                    text_recap_end += getText("gain").format(name=bully_gagnant.name, reward = gold_earned) + f"{money.MONEY_EMOJI}\n"
            
            if (user_perdant is not None):
                text_recap_end += await bully_perdant.die_in_fight()
            
        else : 
            exp_earned, gold_earned = 0.0, 0
        await self.channel_cible.send(text_recap_end)
        return RecapExpGold(exp_earned, gold_earned)
        
    
    async def setup_message(self):
        with open(self.fighter_1.bully.get_image(), "rb") as bully_image_file_1, open(self.fighter_2.bully.get_image(), "rb") as bully_image_file_2:
            if (self.fighter_1.bully.image_file_path is not None):
                bully_image_file_1 = discord.File(bully_image_file_1, filename="bully_image_file_1.png")
            else : bully_image_file_1 = None
            # bully_image_file_1 = discord.File(bully_image_file_1, filename="bully_image_file_1.png") 
            if (self.fighter_2.bully.image_file_path is not None):
                bully_image_file_2 = discord.File(bully_image_file_2, filename="bully_image_file_2.png")
            else : bully_image_file_2 = None
            # bully_image_file_2 = discord.File(bully_image_file_2, filename="bully_image_file_2.png")
            
            texts = self.texts_fight()
            # Création du premier embed avec une miniature (image à gauche) et un texte d'exemple
            self.embed1 = discord.Embed(title=f"{self.fighter_1.bully.name}", description=texts[0], color=0x3498db)
            self.embed1.set_thumbnail(url="attachment://bully_image_file_1.png")
            
            # Création du second embed avec une miniature (image à droite) et un texte d'exemple
            self.embed2 = discord.Embed(title=f"{self.fighter_2.bully.name}", description=texts[1], color=0xe74c3c)
            self.embed2.set_thumbnail(url="attachment://bully_image_file_2.png")

            self.message_1 = await self.channel_cible.send(file=bully_image_file_1, embed=self.embed1) #type: ignore
            self.message_mid = await self.channel_cible.send(texts[2])
            if (len(self.users_can_swap)>0) : 
                self.message_2 = await self.channel_cible.send(file=bully_image_file_2, embed=self.embed2,  view=interact_game.ViewClickBoolMultiple(users=self.users_can_swap, events=self.events_click_swap, labels=self.labels_swap, emoji="🔁"))#type: ignore
            else :
                self.message_2 = await self.channel_cible.send(file=bully_image_file_2, embed=self.embed2)#type: ignore
        
    async def update_message(self):
        texts = self.texts_fight()
        await self.message_mid.edit(content=texts[2])
        if self.embed1.description != texts[0]:
            self.embed1.description = texts[0]
            await self.message_1.edit(embed=self.embed1)
        if self.embed2.description != texts[1]:
            self.embed2.description = texts[1]
            await self.message_2.edit(embed=self.embed2)

    def texts_fight(self) -> tuple[str, str, str]:
        barre_pv_1 = value_to_bar_str(self.fighter_1.pv, max_value= self.max_pv_1)
        barre_pv_2 = value_to_bar_str(self.fighter_2.pv, max_value= self.max_pv_2)
        text_1 = buff_to_str(self.fighter_1.buffs)
        text_2 = buff_to_str(self.fighter_2.buffs)

        pv1 = round(self.fighter_1.pv,1); pv2 = round(self.fighter_2.pv,1)
        text_mid = CText(
            f"HP : {barre_pv_1} ({pv1:02}/{self.max_pv_1:02}) \t{self.fighter_1.stats.to_str_color()} \n"
            f"{''.join(self.emojis_recap[0][-RECAP_MAX_EMOJI:])}\n"
            f"{''.join(self.emojis_recap[1][-RECAP_MAX_EMOJI:])}\n"
            f"HP : {barre_pv_2} ({pv2:02}/{self.max_pv_2:02}) \t{self.fighter_2.stats.to_str_color()}"
        ).str()

        return text_1, text_2, text_mid
    
async def proposition_team_fight(ctx:Context, user_1:discord.abc.User, user_2:discord.abc.User, player_1: Player, player_2: Player, for_fun = True):
    text_challenge = getText("challenge_teamfight").format(user1=user_1.mention, user2=user_2.mention)
    if for_fun :
        text_challenge = getText("challenge_teamfight_for_fun").format(user1=user_1.mention, user2=user_2.mention)

    #On créer l'event qui sera set quand le bouton sera cliqué par user_2. La valeur du bouton (de la réponse) sera stocké dans var
    event = asyncio.Event()
    var:Dict[str, bool] = {"choix" : False}

    if(user_1 != user_2):
        #On affiche le message
        message = await ctx.channel.send(content=text_challenge, view=interact_game.ViewYesNo(user=user_2, event=event, variable_pointer = var))
        #On attend que le joueur clique sur un bouton
        try:
            await asyncio.wait_for(event.wait(), timeout=CHOICE_TIMEOUT)
        except asyncio.exceptions.TimeoutError as e:
            await message.reply(getText("challenge_too_late").format(user1=user_1.mention, user2=user_2.mention))
            return
        #On récup le choix
        challenge_accepte:bool = var["choix"]
    else : 
        message = await ctx.channel.send(content=text_challenge)
        challenge_accepte = True

    #On affiche le choix de user_2
    if(challenge_accepte) : 
        message_accept = await message.reply(getText("challenge_accepted"))
    else : 
        await message.reply(getText("challenge_declined"))
        return


    #On commence le teamfight
    # thread_challenge = await ctx.channel.create_thread(name=getText("title_challenge").format(user1= user_1.name, user2=user_2.name), message=message_accept) #type: ignore
    thread_challenge = await create_thread(ctx, getText("title_challenge").format(user1= user_1.name, user2=user_2.name), message=message_accept)
    try : 
        teamfight = TeamFight(ctx=ctx, user_1=user_1, user_2=user_2, player_1=player_1, player_2=player_2, for_fun=for_fun, can_swap=True, 
                            channel_cible=thread_challenge)
        teamfight.setup_teams()
        await teamfight.start_teamfight()
    finally:
        await del_thread(thread=thread_challenge, time_bfr_close=DELAIE_DELETE_THREAD_FIGHT)
    return

class TeamFight():
    def __init__(self, ctx:Context, user_1: discord.abc.User|None, user_2: discord.abc.User|None, player_1: Player|None, player_2: Player|None
                 , for_fun = True, can_swap=False, channel_cible=None):
        self.ctx = ctx
        self.user_1 = user_1
        self.user_2 = user_2
        self.player_1 = player_1
        self.player_2 = player_2
        self.team_1:list[FightingBully] = []
        self.team_2:list[FightingBully] = []
        self.for_fun = for_fun
        self.can_swap = can_swap
        if(channel_cible is None):
            channel_cible = ctx.channel
        self.channel_cible:discord.abc.Messageable = channel_cible

        self.nb_swaps_1 = 1 if can_swap and isinstance(user_1, discord.abc.User) else 0
        self.nb_swaps_2 = 1 if can_swap and isinstance(user_2, discord.abc.User) else 0

        self.users_can_swap:list[discord.abc.User] = []
        self.events_click_swap:list[asyncio.Event] = []
        self.labels_swap:list[str] = []
        if self.nb_swaps_1 > 0 and self.user_1:
            self.users_can_swap.append(self.user_1)
            self.events_click_swap.append(asyncio.Event())
            self.labels_swap.append(f"Swap j1 {(': ' + str(self.nb_swaps_1)) if self.nb_swaps_1 < math.inf else ''}")
        if self.nb_swaps_2 > 0 and self.user_2:
            self.users_can_swap.append(self.user_2)
            self.events_click_swap.append(asyncio.Event())
            self.labels_swap.append(f"Swap j2 {(': ' + str(self.nb_swaps_1)) if self.nb_swaps_1 < math.inf else ''}")

    def setup_teams(self, team_1:list[FightingBully] | None = None, team_2:list[FightingBully] | None = None):
        if team_1 is not None:
            self.team_1 = team_1.copy()
        elif self.player_1 is not None:
            self.team_1 = get_player_team(self.player_1, is_team_buff_active=True)
        else :
            raise Warning("Team 1 failed to setup")
        if team_2 is not None:
            self.team_2 = team_2.copy()
        elif self.player_2 is not None:
            self.team_2 =  get_player_team(self.player_2, is_team_buff_active=True) 
        else :
            raise Warning("Team 2 failed to setup")

    async def start_teamfight(self) -> bool:
        fighter_1:FightingBully | None = None
        fighter_2:FightingBully | None = None

        while len(self.team_1) > 0 and len(self.team_2) > 0 :
            if fighter_1 is None :
                fighter_1 = await self.select_next_fighter(user=self.user_1, player=self.player_1, team=self.team_1)
            if fighter_2 is None :
                fighter_2 = await self.select_next_fighter(user=self.user_2, player=self.player_2, team=self.team_2)
            
            fight = Fight(self.ctx, user_1=self.user_1, user_2=self.user_2, player_1=self.player_1, player_2=self.player_2
                          , fighter_1=fighter_1, fighter_2=fighter_2, for_fun=self.for_fun, nb_swaps_1=self.nb_swaps_1, nb_swaps_2=self.nb_swaps_2, channel_cible=self.channel_cible)
            try : 
                await fight.start_fight()
            except InterruptionCombat as interrupt:
                if interrupt.user == self.user_1:
                    fighter_1 = None
                    self.nb_swaps_1 -= 1
                elif interrupt.user == self.user_2:
                    fighter_2 = None
                    self.nb_swaps_2 -= 1
                else :
                    raise interrupt
            
            if fighter_1 is not None and fighter_1.pv <= 0 :
                self.team_1.remove(fighter_1)
                fighter_1 = None
                self.increase_swap()
            if fighter_2 is not None and fighter_2.pv <= 0 :
                self.team_2.remove(fighter_2)
                fighter_2 = None
                self.increase_swap()

        return await self.end_teamfight()

    async def select_next_fighter(self, user:discord.abc.User|None, player:Player|None, team:list[FightingBully]) -> FightingBully:
        if user is None or player is None :
            return team[0]
        try:
            f_bully, _ = await interact_game.player_choose_fighting_bully(ctx=self.ctx, fighting_bullies=team, user=user, timeout=CHOICE_TIMEOUT, channel_cible=self.channel_cible)
        except asyncio.exceptions.TimeoutError as e:
            await self.channel_cible.send(getText("select_to_late_random").format(user=user.name))
            return team[0]
        except interact_game.CancelChoiceException as e:
            await self.channel_cible.send(getText("fight_giveup").format(user=user.name))
            raise e
        return f_bully

    async def end_teamfight(self) -> bool:
        async def announce_winner(winner_name:str, loser_name:str, winner_player:Player|None):
            txt_end = getText("teamfight_winner").format(winner=winner_name, loser=loser_name)
            await self.channel_cible.send(txt_end)
            if self.ctx.channel != self.channel_cible:
                await self.ctx.channel.send(txt_end)
            if self.player_1 is not None and self.player_2 is not None and self.ctx.guild is not None and winner_player is not None:
                id_server = self.ctx.guild.id
                if id_server in tournaments:
                    
                    tournaments[id_server].register_teamfight_result(player_id1=self.player_1.id
                                                    , player_id2=self.player_2.id
                                                    , winner_id=winner_player.id
                                                    , channel=self.ctx.channel)

        if len(self.team_1) > 0:
            winner = self.user_1.name if self.user_1 is not None else 'Team 1'
            loser = self.user_2.name if self.user_2 is not None else 'Team 2'
            await announce_winner(winner, loser, self.player_1)
            return True

        if len(self.team_2) > 0:
            winner = self.user_2.name if self.user_2 is not None else 'Team 2'
            loser = self.user_1.name if self.user_1 is not None else 'Team 1'
            await announce_winner(winner, loser, self.player_2)
            return False
        raise Exception("No winner found")

    def increase_swap(self):
        if self.can_swap :
            if self.user_1 :
                self.nb_swaps_1 += 1
            if self.user_2 :
                self.nb_swaps_2 += 1
# Pour les comparaisons de stat ____________________________________
def challenge_agility(stat_voulant_rejouer: Stats, stat_qui_attaque_normalement: Stats) -> bool:
    stat_veux_rejouer_agility = stat_voulant_rejouer.agility
    stat_attaquant_normal_agility = stat_qui_attaque_normalement.agility
    rejouer = Bully.clash_stat(stat_veux_rejouer_agility, stat_attaquant_normal_agility)
    return rejouer
def challenge_block(stat_attaquant: Stats, stat_defenseur: Stats) -> bool:
    stat_att_strength = stat_attaquant.strength
    stat_def_strength = stat_defenseur.strength
    parade_reussie = Bully.clash_stat(st_actif = stat_def_strength, st_passif = stat_att_strength)
    return parade_reussie
def challenge_lethality(stat_attaquant: Stats, stat_defenseur: Stats) -> int:
    nb_succes = 0
    nb_succes += 1 if Bully.clash_stat(st_actif = stat_attaquant.lethality, st_passif = stat_defenseur.strength) else 0
    nb_succes += 1 if Bully.clash_stat(st_actif = stat_attaquant.lethality, st_passif = stat_defenseur.lethality) else 0
    return nb_succes
def challenge_viciousness(stat_challenger: Stats, stat_defender: Stats) -> bool:
    stat_att_vicieux = stat_challenger.viciousness
    stat_def_vicieux = stat_defender.viciousness
    minim = min(stat_att_vicieux, stat_def_vicieux)
    fourberie = Bully.clash_stat(st_actif = stat_att_vicieux, st_passif = stat_def_vicieux, neutre=minim)
    return fourberie

def apply_viciousness(stat_challenger:Stats, stat_defender:Stats, is_attack_success, is_attacker) -> float:
    """Apply a permanent viciousness debuff to the defender's highest stat.
    Return the debuff stat value"""
    max_stat_name = stat_defender.max_stat()
    total_stat_points = stat_defender.sum_stats()
    if getattr(stat_defender, max_stat_name) > getattr(stat_challenger, max_stat_name) :
        if is_attack_success and is_attacker:
            malus = total_stat_points * 0.12
        elif is_attacker:
            malus = total_stat_points * 0.08
    else:
        if is_attack_success and is_attacker:
            malus = total_stat_points * 0.02
        elif is_attacker:
            malus = total_stat_points * 0.02
    setattr(stat_defender, max_stat_name, max(1, getattr(stat_defender, max_stat_name) - malus))
    return malus

def value_to_bar_str(v:int, max_value=10) -> str:
    v = max(0,v) #Pour éviter des valeurs négatives
    v = math.floor(v)
    t = ""
    for k in range(v):
        t += "▮"
    for k in range(max_value-v):
        t += "."
    return t

def buff_to_str(buffs:list[fighting_bully.BuffFight]):
    txt = "\n" if buffs == [] else "\nBuff : \n" 
    for b in buffs : 
        # txt += f" {b.name} |"
        txt += f" **{b.name}** : {b.description}\n"
    return txt

# Les récompenses 
def reward_win_fight(b_win:Bully, b_lose:Bully) -> tuple[float, int]:
    exp_earned = 0
    gold_earned = 0
    if(b_win.lvl >= b_lose.lvl + 5):
        gold_earned = b_lose.gold_give_when_die()
    else : 
        exp_earned = b_lose.exp_give_when_die()
        if b_win.rarity.death_exp_coeff > 1 :
            exp_earned /= b_win.rarity.death_exp_coeff
    return (exp_earned, int(gold_earned))

class InterruptionCombat(Exception):
    def __init__(self, pv_1, pv_2, text="", user_interrupt:discord.abc.User|None = None):
        self.user = user_interrupt
        #Save les pv = inutile ?
        self.pv_1 = pv_1
        self.pv_2 = pv_2
        super().__init__(f"{text}. [pv_1 = {pv_1}, pv_2 = {pv_2}]")


