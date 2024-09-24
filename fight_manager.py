import os
import random

import discord
from bully import Bully, Stats, LevelUpException
import fighting_bully
from fighting_bully import FightingBully
import interact_game
import money
import asyncio
import math

from discord.ext.commands import Context, Bot
from player_info import Player
from typing import Optional, Dict
from dataclasses import replace
import utils.color_str

CHOICE_TIMEOUT = 30
RECAP_MAX_EMOJI = 15
FIGHT_MSG_TIME_UPDATE = 1

async def proposition_fight(ctx: Context, user_1: discord.abc.User, player_1: Player, user_2: discord.abc.User, player_2: Player, bot: Bot, for_fun = False) -> None:
    await manager_start_fight(ctx, user_1, player_1, user_2, player_2, bot, for_fun)
    return

async def manager_start_fight(ctx: Context, user_1: discord.abc.User, player_1: Player, user_2: discord.abc.User, player_2: Player, bot: Bot, for_fun = False) -> None:
    text_challenge = f"{user_1.mention} challenges {user_2.mention} !"
    if for_fun :
        text_challenge = f"{user_1.mention} challenges {user_2.mention} to a fun fight (no death, no xp)!"

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
            await message.reply(f"Too late! No fight between {user_1} and {user_2}")
            return
        #On récup le choix
        challenge_accepte:bool = var["choix"]
    else : 
        message = await ctx.channel.send(content=text_challenge)
        challenge_accepte = True

    #On affiche le choix de user_2
    if(challenge_accepte) : 
        await message.reply("Challenge accepted!")
    else : 
        await message.reply("Challenge declined")
        return
    
    #On commence le combat
    await start_fight(ctx, user_1, player_1, user_2, player_2, bot, for_fun)
    return

async def start_fight(ctx: Context, user_1: discord.abc.User, player_1: Player, user_2: discord.abc.User, player_2: Player, bot: Bot, for_fun = False) -> None:

    try:
        bully_1, _ = await interact_game.player_choose_bully(ctx, user_1, player_1, bot, timeout = CHOICE_TIMEOUT)
        fighting_bully_1 = FightingBully.create_fighting_bully(bully_1)
    except asyncio.exceptions.TimeoutError as e:
        await ctx.send(f"Timeout, choose faster next time {user_1.name}")
        return
    except interact_game.CancelChoiceException as e:
        await ctx.send(f"{user_1.name} cancelled the fight")
        return
    try:
        bully_2, _ = await interact_game.player_choose_bully(ctx, user_2, player_2, bot, timeout = CHOICE_TIMEOUT)
        fighting_bully_2 = FightingBully.create_fighting_bully(bully_2)
    except asyncio.exceptions.TimeoutError as e:
        await ctx.send(f"Timeout, choose faster next time {user_2.name}")
        return
    except interact_game.CancelChoiceException as e:
        await ctx.send(f"{user_2.name} cancelled the fight")
        return
    
    await fight(ctx, user_1, player_1, user_2, player_2, bot, fighting_bully_1, fighting_bully_2, for_fun)
    
    return

async def fight(ctx: Context, user_1: discord.abc.User, player_1: Player, user_2: discord.abc.User, player_2: Player, bot: Bot, fighting_bully_1:FightingBully, fighting_bully_2:FightingBully, 
                for_fun = False) -> None:
    
    await fight_simulation(ctx=ctx, user_1=user_1, user_2=user_2, bot=bot, 
                                        fighting_bully_1=fighting_bully_1, fighting_bully_2=fighting_bully_2)
    
    pv_1 = fighting_bully_1.pv
    pv_2 = fighting_bully_2.pv

    if(pv_1 <= 0):
        bully_gagnant = fighting_bully_2.combattant ##MODIF HERE
        bully_perdant = fighting_bully_1.combattant ##MODIF HERE
    elif(pv_2 <= 0):
        bully_gagnant = fighting_bully_1.combattant ##MODIF HERE
        bully_perdant = fighting_bully_2.combattant ##MODIF HERE
    else:
        print("WTF")
        return
    
    if(for_fun) :
        await ctx.channel.send(f"{bully_gagnant.name} won this fun fight!")
    else :
        (exp_earned, gold_earned) = reward_win_fight(bully_gagnant, bully_perdant)
        pretext = ""
        if (exp_earned > 0):
            try :
                bully_gagnant.give_exp(exp_earned)
            except LevelUpException as lvl_except:
                await ctx.channel.send(f"{bully_gagnant.name} {lvl_except.text}")
            pretext += f"{bully_gagnant.name} earned {exp_earned} xp\n"
        if (gold_earned > 0):
            user_gagnant, player_gagnant = (user_1,player_1) if bully_gagnant == fighting_bully_1.combattant else (user_2, player_2)
            money.give_money(player_gagnant, montant=gold_earned)
            pretext += f"{user_gagnant.name} earned {gold_earned}{money.MONEY_ICON}\n"
        await bully_perdant.kill()
        await ctx.channel.send(f"{pretext}{bully_perdant.name} died in terrible agony")
    return

def value_to_bar_str(v:int, max_value=10) -> str:
    v = max(0,v) #Pour éviter des valeurs négatives
    t = ""
    for k in range(v):
        t += "▮"
        # t += "■"
    for k in range(max_value-v):
        t += "."
        # t += "□"
    
    return t

async def manager_start_team_fight(ctx: Context, user_1: discord.abc.User, player_1: Player, user_2: discord.abc.User, player_2: Player, bot: Bot) -> None:
    text_challenge = f"{user_1.mention} challenges {user_2.mention} to a fun team fight (no death, team vs team)!"

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
            await message.reply(f"Too late! No fight between {user_1} and {user_2}")
            return
        #On récup le choix
        challenge_accepte:bool = var["choix"]
    else : 
        message = await ctx.channel.send(content=text_challenge)
        challenge_accepte = True

    #On affiche le choix de user_2
    if(challenge_accepte) : 
        await message.reply("Challenge accepted!")
    else : 
        await message.reply("Challenge declined")
        return
    
    #On commence le combat
    await team_fight(ctx, user_1, player_1, user_2, player_2, bot)
    return

async def team_fight(ctx: Context, user_1: discord.abc.User, player_1: Player, user_2: discord.abc.User, player_2: Player, bot: Bot) -> None:
    #On initialise fighters_bully des joueurs
    fighters_joueur_1: list[FightingBully] = [FightingBully.create_fighting_bully(b) for b in player_1.get_equipe()]
    fighters_joueur_2: list[FightingBully] = [FightingBully.create_fighting_bully(b) for b in player_2.get_equipe()]
    f_bully_1 = None
    f_bully_2 = None

    while len(fighters_joueur_1) > 0 and len(fighters_joueur_2) > 0:
        if f_bully_1 == None:
            try:
                f_bully_1, _ = await interact_game.player_choose_fighting_bully(ctx=ctx, fighting_bullies=fighters_joueur_1, user=user_1, player=player_1, bot=bot, timeout=CHOICE_TIMEOUT)
            except Exception as e:
                await ctx.send(f"{user_1.name} give up the fight")
                return
        if f_bully_2 == None:
            try:
                f_bully_2, _ = await interact_game.player_choose_fighting_bully(ctx=ctx, fighting_bullies=fighters_joueur_2, user=user_2, player=player_2, bot=bot, timeout=CHOICE_TIMEOUT)
            except Exception as e:
                await ctx.send(f"{user_1.name} give up the fight")
                return
        
        await fight_simulation(ctx, bot=bot, fighting_bully_1=f_bully_1, fighting_bully_2=f_bully_2, user_1=user_1, user_2=user_2)
        if f_bully_1.pv <= 0:
            fighters_joueur_1.remove(f_bully_1)
            await ctx.send(f"{f_bully_1.combattant.name} is defeated.")
            f_bully_1 = None
            
        if f_bully_2.pv <= 0:
            fighters_joueur_2.remove(f_bully_2)
            await ctx.send(f"{f_bully_2.combattant.name} is defeated.")
            f_bully_2 = None
        
    if len(fighters_joueur_1) > 0 :
        await ctx.send(f"{user_1.name} wins the teamfight!")
    if len(fighters_joueur_2) > 0 :
        await ctx.send(f"{user_2.name} wins the teamfight!")


# ____________________________________________________
async def fight_simulation(ctx:Context, bot: Bot, fighting_bully_1:FightingBully, fighting_bully_2:FightingBully,
                            user_1: discord.abc.User|None = None, user_2:discord.abc.User|None = None, is_switch_possible = False,
                            channel_cible = None) -> None:    
    if(channel_cible == None):
        channel_cible = ctx.channel

    #On initialise les variables pour le combat :
    tour = random.randint(0,1)

    max_pv_1 = fighting_bully_1.combattant.max_pv
    max_pv_2 = fighting_bully_2.combattant.max_pv

    #On calcul le texte
    barre_pv_joueur = value_to_bar_str(fighting_bully_1.pv, max_value= max_pv_1)
    barre_pv_enemy = value_to_bar_str(fighting_bully_2.pv, max_value= max_pv_2)
    text_base_combat = f_text_base_combat(fighting_bully_1, fighting_bully_2, max_pv_1, max_pv_2, "", "")
    action_combat = "Let's get ready to rumble!"
    text_combat = "```ansi\n" + text_base_combat + "\n\n" + action_combat + "```"

    emoji_recap_j1: list[str] = []
    emoji_recap_j2: list[str] = []
    
    #On affiche le texte
    if(is_switch_possible and isinstance(user_1, discord.abc.User)): #Ce code n'est fait pour fonctioner que si seul le user_1 peut switch. Faut l'adapter si le user2 peut switch
        event_click_switch = asyncio.Event()
        message = await channel_cible.send(text_combat,  view=interact_game.ViewClickBool(user=user_1, event=event_click_switch, label="Swap Bully", emoji="🔁"))
    else :
        message = await channel_cible.send(text_combat)

    await asyncio.sleep(FIGHT_MSG_TIME_UPDATE)

    while fighting_bully_1.pv > 0 and fighting_bully_2.pv > 0 :
        #On calcule l'action
        (text_action, emoji_j1, emoji_j2, tour) = nouvelle_action_stat(fighting_bully_1=fighting_bully_1, fighting_bully_2=fighting_bully_2, tour= tour)
        
        #On save les emoji pour la frise chronologique
        emoji_recap_j1.append(emoji_j1)
        emoji_recap_j2.append(emoji_j2)

        #on maj les parametres des pv 
        barre_pv_joueur = value_to_bar_str(fighting_bully_1.pv, max_value= max_pv_1)
        barre_pv_enemy = value_to_bar_str(fighting_bully_2.pv, max_value= max_pv_2)
        barre_max_length = max(max_pv_1, max_pv_2)

        #On fait visuellement la modif du texte de combat : 
        text_base_combat = f_text_base_combat(fighting_bully_1, fighting_bully_2, max_pv_1, max_pv_2, emoji_recap_j1, emoji_recap_j2)

        action_combat = text_action
        text_combat = "```ansi\n" + text_base_combat + "\n\n" + action_combat + "```"
        await message.edit(content = text_combat)
        await asyncio.sleep(FIGHT_MSG_TIME_UPDATE)

        #On regarde si changement nécessaire 
        if(is_switch_possible and fighting_bully_1.pv > 0 and fighting_bully_2.pv > 0) : 
            if event_click_switch.is_set():
                raise InterruptionCombat(fighting_bully_1.pv, fighting_bully_2.pv)
    return 

def f_text_base_combat(fighting_bully_1:FightingBully, fighting_bully_2:FightingBully, max_pv_1:int, max_pv_2:int, emoji_recap_j1, emoji_recap_j2):
    barre_pv_joueur = value_to_bar_str(fighting_bully_1.pv, max_value= max_pv_1)
    barre_pv_enemy = value_to_bar_str(fighting_bully_2.pv, max_value= max_pv_2)
    barre_max_length = max(max_pv_1, max_pv_2)
    text_combat = (
            f"\t\tBully 1 : {fighting_bully_1.combattant.name}\n"
            f"HP : {barre_pv_joueur:{barre_max_length}} ({fighting_bully_1.pv:02}/{max_pv_1:02}) \t{fighting_bully_1.stats.to_str_color()}\n"
            f"{''.join(emoji_recap_j1[-RECAP_MAX_EMOJI:])}\n"
             "\t\t\t\tVS\n"
            f"{''.join(emoji_recap_j2[-RECAP_MAX_EMOJI:])}\n"
            f"\t\tBully 2 : {fighting_bully_2.combattant.name}\n"
            f"HP : {barre_pv_enemy:{barre_max_length}} ({fighting_bully_2.pv:02}/{max_pv_2:02}) \t{fighting_bully_2.stats.to_str_color()}"
        )
    return text_combat

def nouvelle_action_stat(fighting_bully_1:FightingBully, fighting_bully_2:FightingBully, tour) ->tuple[str, str, str, int]:
    """
    tour est égale à 0 ou 1. Il indique le tour du bully qui devrait normalement agir maintenant. 0 = bully_1, 1 = bully_2
    Retourne un tuple sous la forme : 
    (text_action, emoji_j1, emoji_j2, tour)
    C4EST DEGUEUX FAIRE UNE CLASS QUI PREN TOUT 9A EN COMPTE ET TOUT BREF LA C4EST NIMP
    """
    Emotes_possibles = ["👊", "🩸", "🛡️","🔪", "💥","💔", "🗡️"]  #C'est juste pour pouvoir copier/coller
    text_action = ""
    pv_perdu_j1 = 0
    pv_perdu_j2 = 0
    pv_perdu = 0
    emoji_j1=""
    emoji_j2=""
    
    name_1 = fighting_bully_1.combattant.name
    name_2 = fighting_bully_2.combattant.name
    
    stat_j1 = (fighting_bully_1.stats)
    stat_j2 = (fighting_bully_2.stats)

    (name_actif, stat_j_actif), (name_passif, stat_j_passif) = ((name_1, stat_j1), (name_2, stat_j2)) if tour==0 else ((name_2, stat_j2), (name_1, stat_j1))
    
    if challenge_prendre_de_vitesse_stats(stat_j_passif, stat_j_actif) :
        #On inverse le tour
        tour = (tour - 1) * - 1 
        (name_actif, stat_j_actif), (name_passif, stat_j_passif) = ((name_1, stat_j1), (name_2, stat_j2)) if tour==0 else ((name_2, stat_j2), (name_1, stat_j1))
        text_action += f"{name_actif} follows up with another punch. "
    else : 
        text_action += f"{name_actif} strikes. "
        
    
    if challenge_defense_stats(stat_j_actif, stat_j_passif):
        text_action += f"But {name_passif} blocks! "
        emoji_j1 = "👊" if tour==0 else "🛡️"
        emoji_j2 = "🛡️" if tour==0 else "👊"

        if challenge_viciosite_stats(stat_j_actif, stat_j_passif):
            text_action += f"{name_actif}'s vicious attack weakens {name_passif}. "
            apply_viciousness(stat_j_actif, stat_j_passif, is_attack_success=False, is_attacker=True)
            emoji_j1 = "🗡️" if tour==0 else "🛡️"
            emoji_j2 = "🛡️" if tour==0 else "🗡️"
        # elif challenge_viciosite_stats(stat_j_passif, stat_j_actif):
        #     apply_viciousness(stat_j_passif, stat_j_actif, is_attack_success=False, is_attacker=False)


    else :
        lethal_buff = challenge_coup_critique_stats(stat_j_actif, stat_j_passif)
        lethal_buff += 1 if lethal_buff > 1 else 0
        
        if lethal_buff > 0 :
            text_action += f"The punch shatters {name_passif}! "
            pv_perdu = 1 + lethal_buff
            emoji_j1 = "🔪" if tour==0 else "💥"
            emoji_j2 = "💥" if tour==0 else "🔪"
        else :
            text_action += f"{name_passif} is hurt."
            pv_perdu = 1
            emoji_j1 = "👊" if tour==0 else "🩸"
            emoji_j2 = "🩸" if tour==0 else "👊"

        if challenge_viciosite_stats(stat_j_actif, stat_j_passif):
            text_action += f"{name_actif}'s vicious attack weakens {name_passif}. "
            apply_viciousness(stat_j_actif, stat_j_passif, is_attack_success=True, is_attacker=True)
            em_att = "🔪" if lethal_buff > 0 else "🗡️"
            emoji_j1 = em_att if tour==0 else "💔"
            emoji_j2 = "💔" if tour==0 else em_att
            
    pv_perdu_j1 = pv_perdu if (name_passif == name_1) else 0
    pv_perdu_j2 = pv_perdu if (name_passif == name_2) else 0
    tour ^= 1 

    fighting_bully_1.pv = max(0,fighting_bully_1.pv - pv_perdu_j1)
    fighting_bully_2.pv = max(0,fighting_bully_2.pv - pv_perdu_j2)
    
    return (text_action, emoji_j1, emoji_j2, tour)

# Pour les comparaisons de stat ____________________________________
def challenge_prendre_de_vitesse_stats(stat_voulant_rejouer: Stats, stat_qui_attaque_normalement: Stats) -> bool:
    stat_veux_rejouer_agility = stat_voulant_rejouer.agility
    stat_attaquant_normal_agility = stat_qui_attaque_normalement.agility
    rejouer = Bully.clash_stat(stat_veux_rejouer_agility, stat_attaquant_normal_agility)
    return rejouer

def challenge_defense_stats(stat_attaquant: Stats, stat_defenseur: Stats) -> bool:
    stat_att_strength = stat_attaquant.strength
    stat_def_strength = stat_defenseur.strength
    parade_reussie = Bully.clash_stat(st_actif = stat_def_strength, st_passif = stat_att_strength)
    return parade_reussie

def challenge_coup_critique_stats(stat_attaquant: Stats, stat_defenseur: Stats) -> int:
    nb_succes = 0
    nb_succes += 1 if Bully.clash_stat(st_actif = stat_attaquant.lethality, st_passif = stat_defenseur.strength) else 0
    nb_succes += 1 if Bully.clash_stat(st_actif = stat_attaquant.lethality, st_passif = stat_defenseur.lethality) else 0
    return nb_succes

def challenge_viciosite_stats(stat_challenger: Stats, stat_defender: Stats) -> bool:
    stat_att_vicieux = stat_challenger.viciousness
    stat_def_vicieux = stat_defender.viciousness
    minim = min(stat_att_vicieux, stat_def_vicieux)
    fourberie = Bully.clash_stat(st_actif = stat_att_vicieux, st_passif = stat_def_vicieux, neutre=minim)
    
    return fourberie

def apply_viciousness(stat_challenger:Stats, stat_defender:Stats, is_attack_success, is_attacker):
    """Apply a permanent viciousness debuff to the defender's highest stat."""
    max_stat_name = stat_defender.max_stat()
    total_stat_points = stat_defender.sum_stats()

    if getattr(stat_defender, max_stat_name) > getattr(stat_challenger, max_stat_name) :
        if is_attack_success and is_attacker:
            malus = total_stat_points * 0.12
        elif is_attacker:
            malus = total_stat_points * 0.08#0.07
        else:
            malus = total_stat_points * 0.0#0.02
    else:
        if is_attack_success and is_attacker:
            malus = total_stat_points * 0.02#0.04
        elif is_attacker:
            malus = total_stat_points * 0.02#0.01
        else:
            malus = total_stat_points * 0.0#0.005

    setattr(stat_defender, max_stat_name, max(1, getattr(stat_defender, max_stat_name) - malus))

# __________________________________________________________________
# ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

# Les récompenses ____________________________________
def reward_win_fight(b_win:Bully, b_lose:Bully) -> tuple[float, int]:
    exp_earned = 0
    gold_earned = 0
    if(b_win.lvl >= b_lose.lvl * 2 and b_win.lvl >= 10):
        gold_earned = b_lose.gold_give_when_die()
    else : 
        exp_earned = b_lose.exp_give_when_die()
        if b_win.rarity.death_exp_coeff > 1 :
            exp_earned /= b_win.rarity.death_exp_coeff
    return (exp_earned, int(gold_earned))

# ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


## check _________________________________

def check_oui_non(author):
    """
    Renvoie une fonction qui permet de vérifier si un message provient bien de l'author en paramètre de check et que ce soit oui ou non
    """
    def inner_check(message): 
        if message.author != author:
            return False
        
        return (message.content.lower() == "oui") or (message.content.lower() == "non")
    
    return inner_check
 
def check_number(author):
    """
    Renvoie une fonction qui permet de vérifier si un message provient bien de l'author en paramètre de check et que ce soit un nombre
    """
    def inner_check(message): 
        if message.author != author:
            return False
        
        return message.content.isdigit()
    
    return inner_check
 
def check_reaction_yes_no(author, sent_message):
    def inner_check(reaction, user): 
        return author.id == user.id and sent_message.id == reaction.message.id and str(reaction.emoji) in ["✅", "❌"]
    
    return inner_check

def check_reaction_number(author: discord.abc.User, sent_message: discord.Message):
    def inner_check(reaction, user): 
        return author.id == user.id and sent_message.id == reaction.message.id and str(reaction.emoji) in ["\u0030\u20E3", "\u0031\u20E3", "\u0032\u20E3", "\u0033\u20E3", "\u0034\u20E3"]
    
    return inner_check

# emote <-> int

def from_number_to_emote(nb) -> str:
    match nb:
        case 0 :
            return "\u0030\u20E3"
        case 1:
            return "\u0031\u20E3"
        case 2 :
            return "\u0032\u20E3"
        case 3:
            return "\u0033\u20E3"
        case 4 :
            return "\u0034\u20E3"
    return ":error:"

def from_emote_to_number(emote) -> int:
    match emote:
        case "\u0030\u20E3" :
            return 0
        case "\u0031\u20E3":
            return 1
        case "\u0032\u20E3" :
            return 2
        case "\u0033\u20E3":
            return 3
        case "\u0034\u20E3" :
            return 4
         
    raise Exception("This is not a valid number!")

class InterruptionCombat(Exception):
    def __init__(self, pv_1, pv_2, text=""):
        self.pv_1 = pv_1
        self.pv_2 = pv_2
        super().__init__(f"{text}. [pv_1 = {pv_1}, pv_2 = {pv_2}]")

