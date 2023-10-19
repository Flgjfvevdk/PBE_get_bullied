import os
import random

import discord
from bully import Bully, Stats
from item import Item
from fighting_bully import FightingBully
import pickle
import interact_game
import money
import asyncio
import math

from discord.ext.commands import Context, Bot
from player_info import Player
from typing import Optional
from dataclasses import replace


CHOICE_TIMEOUT = 20
fight_msg_time_update = 1

async def proposition_fight(ctx: Context, user_1: discord.abc.User, player_1: Player, user_2: discord.abc.User, player_2: Player, bot: Bot, for_fun = False) -> None:
    await manager_start_fight(ctx, user_1, player_1, user_2, player_2, bot, for_fun)
    return

async def manager_start_fight(ctx: Context, user_1: discord.abc.User, player_1: Player, user_2: discord.abc.User, player_2: Player, bot: Bot, for_fun = False) -> None:
    text_challenge = f"{user_1.mention} challenges {user_2.mention} !"
    if for_fun :
        text_challenge = f"{user_1.mention} challenges {user_2.mention} to a fun fight (no death, no xp)!"
    message = await ctx.channel.send(text_challenge)
    await message.add_reaction("✅")
    await message.add_reaction("❌")
    try :
        reaction, msg = await bot.wait_for("reaction_add", check=check_reaction_yes_no(user_2, message), timeout=CHOICE_TIMEOUT)
        if str(reaction.emoji) == "✅" :
            await message.reply("Challenge accepted!")
        elif str(reaction.emoji) == "❌" :
            await message.reply("Challenge declined")
            return
    except Exception as e :
        await message.reply(f"Too late! No fight between {user_1} and {user_2}")
        print (e)
        return
    await start_fight(ctx, user_1, player_1, user_2, player_2, bot, for_fun)
    return

async def start_fight(ctx: Context, user_1: discord.abc.User, player_1: Player, user_2: discord.abc.User, player_2: Player, bot: Bot, for_fun = False) -> None:
    # bully_1, _ = await interact_game.player_choose_bully(ctx= ctx, user = user_1, bot= bot, timeout = CHOICE_TIMEOUT)
    # bully_2, _ = await interact_game.player_choose_bully(ctx= ctx, user = user_2, bot= bot, timeout = CHOICE_TIMEOUT)
    fighting_bully_1, _ = await interact_game.player_choose_bully(ctx, user_1, player_1, bot, timeout = CHOICE_TIMEOUT)
    fighting_bully_2, _ = await interact_game.player_choose_bully(ctx, user_2, player_2, bot, timeout = CHOICE_TIMEOUT)
    
    item_1, item_2 = await manager_equip_item(ctx, user_1, player_1, user_2, player_2, bot)
    # await fight(ctx, user_1, user_2, bot, bully_1, bully_2, for_fun, item_1=item_1, item_2=item_2)
    await fight(ctx, user_1, player_1, user_2, player_2, bot, fighting_bully_1, fighting_bully_2, for_fun, item_1=item_1, item_2=item_2)
    
    return

async def manager_equip_item(ctx: Context, user_1: discord.abc.User, player_1: Player, user_2: discord.abc.User, player_2: Player, bot: Bot) -> tuple[Optional[Item], Optional[Item]]:
    item_1:Optional[Item] = None
    item_2:Optional[Item] = None

    item_1 = await interact_game.player_choose_item(ctx, user_1, player_1, bot, timeout=CHOICE_TIMEOUT)
    item_2 = await interact_game.player_choose_item(ctx, user_2, player_2, bot, timeout=CHOICE_TIMEOUT)
    return item_1, item_2


async def fight(ctx: Context, user_1: discord.abc.User, player_1: Player, user_2: discord.abc.User, player_2: Player, bot: Bot, fighting_bully_1:FightingBully, fighting_bully_2:FightingBully, 
                for_fun = False, item_1:Optional[Item] = None, item_2:Optional[Item] = None) -> None:
    #On initialise les variables pour le combat :
    # max_pv_1 = fighting_bully_1.pv
    # max_pv_2 = fighting_bully_2.pv
    
    await fight_simulation(ctx= ctx, user_1= user_1, user_2= user_2, bot= bot, 
                                        fighting_bully_1= fighting_bully_1, fighting_bully_2= fighting_bully_2,
                                        item_1= item_1, item_2= item_2)
    
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
            bully_gagnant.give_exp(exp_earned)
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
    for k in range(max_value-v):
        t += "."
    return t


# ____________________________________________________
async def fight_simulation(ctx, bot: Bot, fighting_bully_1:FightingBully, fighting_bully_2:FightingBully,
                            user_1: discord.abc.User|None = None, user_2:discord.abc.User|None = None, is_switch_possible = False, 
                            item_1:Optional[Item] = None, item_2:Optional[Item] = None, channel_cible = None) -> None:    

    print("fighting_bully_1.stats ", fighting_bully_1.stats)
    print("fighting_bully_2.stats ", fighting_bully_2.stats)
    if(channel_cible == None):
        channel_cible = ctx.channel

    #On initialise les variables pour le combat :
    tour = random.randint(0,1)
    
    #S'il y a des items, on change les valeurs des variables :
    if(item_1 != None and item_1.is_bfr_fight) : 
        item_1.effect_before_fight(fighting_bully_self= fighting_bully_1, fighting_bully_adv= fighting_bully_2)
    if(item_2 != None and item_2.is_bfr_fight) : 
        item_2.effect_before_fight(fighting_bully_self= fighting_bully_2, fighting_bully_adv= fighting_bully_1)

    max_pv_1 = fighting_bully_1.pv
    max_pv_2 = fighting_bully_2.pv

    #On calcul le texte
    barre_pv_joueur = value_to_bar_str(fighting_bully_1.pv, max_value= max_pv_1)
    barre_pv_enemy = value_to_bar_str(fighting_bully_2.pv, max_value= max_pv_2)

    text_pv_combat = "\t\tBully 1 : " + fighting_bully_1.combattant.name + "\nhp : " + barre_pv_joueur + "\n\n\t\t\t\tVS\n\n\t\tBully 2 : " + fighting_bully_2.combattant.name + "\nhp : " + barre_pv_enemy
    
    action_combat = "Let's get ready to rumble!"
    text_combat = "```" + text_pv_combat + "\n\n" + action_combat + "```"

    emoji_recap_j1 = ""
    emoji_recap_j2 = ""
    
    #On affiche le texte
    message = await channel_cible.send(text_combat)
    if(is_switch_possible):
        await message.add_reaction('🔁')
    await asyncio.sleep(fight_msg_time_update)

    while fighting_bully_1.pv > 0 and fighting_bully_2.pv > 0 :
        #On l'action
        (text_action, emoji_j1, emoji_j2, tour) = nouvelle_action_stat(fighting_bully_1= fighting_bully_1, fighting_bully_2=fighting_bully_2, tour= tour)
        
        #On save les emoji pour la frise chronologique
        emoji_recap_j1+= emoji_j1
        emoji_recap_j2+= emoji_j2

        #on maj les parametres des pv 
        barre_pv_joueur = value_to_bar_str(fighting_bully_1.pv, max_value= max_pv_1)
        barre_pv_enemy = value_to_bar_str(fighting_bully_2.pv, max_value= max_pv_2)

        #On fait visuellement la modif de pv : 
        #text_pv_combat = "\t\tBully 1 : " + name_1 + "\nhp : " + barre_pv_joueur + "\n\t\t\t\t\t" + emoji_recap_j1 + "\n\t\t\t\tVS\n\t\t\t\t\t" + emoji_recap_j2 + "\n\t\tBully 2 : " + name_2 + "\nhp : " + barre_pv_enemy
        text_pv_combat = "\t\tBully 1 : " + fighting_bully_1.combattant.name + "\nhp : " + barre_pv_joueur + "\n\t\t\t\t\t" + emoji_recap_j1 + "\n\t\t\t\tVS\n\t\t\t\t\t" + emoji_recap_j2 + "\n\t\tBully 2 : " + fighting_bully_2.combattant.name + "\nhp : " + barre_pv_enemy
        action_combat = text_action
        text_combat = "```" + text_pv_combat + "\n\n" + action_combat + "```"
        await message.edit(content = text_combat)
        await asyncio.sleep(fight_msg_time_update)

        #On regarde si changement nécessaire : NB : pour l'instant on regarde que pour J1
        if(is_switch_possible) : 
            try : 
                if(tour == 0):
                    await test_interruption_combat_reaction(user_1, message=message, reaction_interrupt= '🔁' )
                else : 
                    await test_interruption_combat_reaction(user_2, message=message, reaction_interrupt= '🔁' )
            except InterruptionCombat as erreur:
                raise InterruptionCombat(fighting_bully_1.pv, fighting_bully_2.pv)
    return 

async def test_interruption_combat_reaction(user, message, reaction_interrupt) -> None:
    message = await message.channel.fetch_message(message.id)
    user_reacted = False
    for reaction in message.reactions:
        if str(reaction.emoji) == reaction_interrupt :
            async for u in reaction.users():
                if u == user:
                    user_reacted = True
                    break  # No need to continue checking reactions
            if user_reacted:
                break
    if(user_reacted):
        raise InterruptionCombat(pv_1= None, pv_2= None)


# Pour calculer l'action du tour : ///////////////////////////////////////////////////////////////////////////////////////////////////////
#def nouvelle_action_stat(stat_base_1, stat_base_2, name_1, name_2, tour):
def nouvelle_action_stat(fighting_bully_1:FightingBully, fighting_bully_2:FightingBully, tour) ->tuple[str, str, str, int]:
    """
    tour est égale à 0 ou 1. Il indique le tour du bully qui devrait normalement agir maintenant. 0 = bully_1, 1 = bully_2
    Retourne un tuple sous la forme : 
    (text_action, emoji_j1, emoji_j2, tour)
    C4EST DEGUEUX FAIRE UNE CLASS QUI PREN TOUT 9A EN COMPTE ET TOUT BREF LA C4EST NIMP
    """
    Emotes_possibles = ["👊", "🩸", "🛡️","🔪", "💥"] # ,"💔" #C'est juste pour pouvoir copier/coller
    text_action = ""
    pv_perdu_j1 = 0
    pv_perdu_j2 = 0
    pv_perdu = 0
    emoji_j1=""
    emoji_j2=""
    
    name_1 = fighting_bully_1.combattant.name
    name_2 = fighting_bully_2.combattant.name

    #On regarde les fourberies
    fourberie_j1 = challenge_viciosite_stats(fighting_bully_1.stats, fighting_bully_2.stats)
    fourberie_j2 = challenge_viciosite_stats(fighting_bully_2.stats, fighting_bully_1.stats)
    
    #stat_j1 = replace(fighting_bully_1.stats).__dict__
    #stat_j2 = replace(fighting_bully_2.stats).__dict__
    stat_j1 = replace(fighting_bully_1.stats)
    stat_j2 = replace(fighting_bully_2.stats)
    
    if(fourberie_j1 and not fourberie_j2):
        #La meilleure de j2 (hors viciosite) devient égale au minimum entre : la stat de j1-1 et sa propre stat - 1. (minimum 1)
        stat_j1_dict = replace(fighting_bully_1.stats).__dict__
        stat_j2_dict = replace(fighting_bully_2.stats).__dict__
        del stat_j1_dict['_parents']
        del stat_j2_dict['_parents']
        max_stat_name = max((n for n in stat_j2_dict if n != "viciousness"), key=lambda n: stat_j2_dict[n])
        if (stat_j2_dict[max_stat_name] <= stat_j2_dict[max_stat_name]):
            stat_j2_dict[max_stat_name] = max(1,stat_j2_dict[max_stat_name] - 1)
        else :
            diff = stat_j2_dict[max_stat_name] - stat_j1_dict[max_stat_name]
            coef_vicious = stat_j2_dict["viciousness"]/stat_j1_dict["viciousness"]
            stat_j2_dict[max_stat_name] = max (1,stat_j1_dict[max_stat_name] - 1 + round(diff * (1 - math.exp(-coef_vicious / 1.5)) ))
    
    if(fourberie_j2 and not fourberie_j1):
        #La meilleure de j1 (hors viciosite) devient egale au minimum entre : la stat de j2-2 et sa propre stat - 1. (minimum 1)
        stat_j1_dict = replace(fighting_bully_1.stats).__dict__
        stat_j2_dict = replace(fighting_bully_2.stats).__dict__
        del stat_j1_dict['_parents']
        del stat_j2_dict['_parents']
        max_stat_name = max((n for n in stat_j1_dict if n != "viciousness"), key=lambda n: stat_j1_dict[n])
        if (stat_j1_dict[max_stat_name] <= stat_j2_dict[max_stat_name]):
            stat_j1_dict[max_stat_name] = max(1,stat_j1_dict[max_stat_name] - 1)
        else :
            diff = stat_j1_dict[max_stat_name] - stat_j2_dict[max_stat_name]
            coef_vicious = stat_j1_dict["viciousness"]/stat_j2_dict["viciousness"]
            stat_j1_dict[max_stat_name] = max (1,stat_j2_dict[max_stat_name] - 1 + round(diff * (1 - math.exp(-coef_vicious / 1.5)) ))


    #(name_actif, stat_j_actif), (name_passif, stat_j_passif) = ((name_1, stat_j1.copy()), (name_2, stat_j2.copy())) if tour==0 else ((name_2, stat_j2.copy()), (name_1, stat_j1.copy()))
    (name_actif, stat_j_actif), (name_passif, stat_j_passif) = ((name_1, stat_j1), (name_2, stat_j2)) if tour==0 else ((name_2, stat_j2), (name_1, stat_j1))
    
    if challenge_prendre_de_vitesse_stats(stat_j_passif, stat_j_actif) :
        #On inverse le tour
        tour = (tour - 1) * - 1 
        # (name_actif, stat_j_actif), (name_passif, stat_j_passif) = ((name_1, stat_j1.copy()), (name_2, stat_j2.copy())) if tour==0 else ((name_2, stat_j2.copy()), (name_1, stat_j1.copy()))
        (name_actif, stat_j_actif), (name_passif, stat_j_passif) = ((name_1, stat_j1), (name_2, stat_j2)) if tour==0 else ((name_2, stat_j2), (name_1, stat_j1))
        
        text_action += f"{name_actif} follows up with another punch. "
    else : 
        text_action += f"{name_actif} strikes. "
        
    
    if challenge_defense_stats(stat_j_actif, stat_j_passif):
        text_action += f"But {name_passif} block! "
        emoji_j1 = "👊" if tour==0 else "🛡️"
        emoji_j2 = "🛡️" if tour==0 else "👊"
    else :
        if challenge_coup_critique_stats(stat_j_actif, stat_j_passif) :
            text_action += f"The punch shatters {name_passif}!"
            pv_perdu = 3
            emoji_j1 = "🔪" if tour==0 else "💥"
            emoji_j2 = "💥" if tour==0 else "🔪"
        else :
            text_action += f"{name_passif} is hurt."
            pv_perdu = 1
            emoji_j1 = "👊" if tour==0 else "🩸"
            emoji_j2 = "🩸" if tour==0 else "👊"
            
    pv_perdu_j1 = pv_perdu if (name_passif == name_1) else 0
    pv_perdu_j2 = pv_perdu if (name_passif == name_2) else 0
    tour = (tour - 1) * -1 

    fighting_bully_1.pv -= pv_perdu_j1
    fighting_bully_2.pv -= pv_perdu_j2
    
    return (text_action, emoji_j1, emoji_j2, tour)
    #return (text_action, pv_perdu_j1, pv_perdu_j2, emoji_j1, emoji_j2, tour)

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

def challenge_coup_critique_stats(stat_attaquant: Stats, stat_defenseur: Stats) -> bool:
    stat_att_lethality = stat_attaquant.lethality
    stat_def_strength = stat_defenseur.strength
    coup_critique = Bully.clash_stat(st_actif = stat_att_lethality, st_passif = stat_def_strength)
    return coup_critique

def challenge_viciosite_stats(stat_attaquant: Stats, stat_defenseur: Stats) -> bool:
    stat_att_vicieux = stat_attaquant.viciousness
    stat_def_vicieux = stat_defenseur.viciousness
    minim = min(stat_att_vicieux, stat_def_vicieux)
    fourberie = Bully.clash_stat(st_actif = stat_att_vicieux, st_passif = stat_def_vicieux, neutre=minim)
    
    return fourberie

# __________________________________________________________________
# ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

# Les récompenses ____________________________________
def reward_win_fight(b_win, b_lose) -> tuple[float, int]:
    exp_earned = 0
    gold_earned = 0
    if(b_win.lvl >= b_lose.lvl + 5):
        gold_earned = b_lose.gold_give_when_die()
    else : 
        exp_earned = b_lose.exp_give_when_die()
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

