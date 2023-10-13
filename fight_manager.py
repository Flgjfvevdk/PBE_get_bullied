import os
import random
from bully import Bully
from item import Item
import pickle
import interract_game
import money
import asyncio
import math

from discord.ext.commands import Context
from typing import Optional


CHOICE_TIMEOUT = 20
fight_msg_time_update = 1

async def proposition_fight(ctx: Context, user_1, user_2, bot, for_fun = False):
    await manager_start_fight(ctx, user_1, user_2, bot, for_fun)
    return

async def manager_start_fight(ctx: Context, user_1, user_2, bot, for_fun = False):
    text_challenge = f"{user_1.mention} challenge {user_2.mention} !"
    if for_fun :
        text_challenge = f"{user_1.mention} challenge {user_2.mention} to a fun fight (no death, no xp)!"
    message = await ctx.channel.send(text_challenge)
    await message.add_reaction("✅")
    await message.add_reaction("❌")
    try :
        reaction, msg = await bot.wait_for("reaction_add", check=check_reaction_yes_no(user_2, message), timeout=CHOICE_TIMEOUT)
        if str(reaction.emoji) == "✅" :
            #await ctx.channel.send("Challenge accepted!")
            await message.reply("Challenge accepted!")
        elif str(reaction.emoji) == "❌" :
            #await ctx.channel.send("Challenge declined")
            await message.reply("Challenge declined")
            return
    except Exception as e :
        #await ctx.channel.send(f"Too late! No fight between {user_1} and {user_2}")
        await message.reply(f"Too late! No fight between {user_1} and {user_2}")
        print (e)
        return
    await start_fight(ctx, user_1, user_2, bot, for_fun)
    return

async def start_fight(ctx: Context, user_1, user_2, bot, for_fun = False):
    bully_1, _ = await interract_game.player_choose_bully(ctx= ctx, user = user_1, bot= bot, timeout = CHOICE_TIMEOUT)
    bully_2, _ = await interract_game.player_choose_bully(ctx= ctx, user = user_2, bot= bot, timeout = CHOICE_TIMEOUT)
    
    item_1, item_2 = await manager_equip_item(ctx=ctx, user_1=user_1, user_2=user_2, bot=bot)
    await fight(ctx, user_1, user_2, bot, bully_1, bully_2, for_fun, item_1=item_1, item_2=item_2)

    return

async def manager_equip_item(ctx: Context, user_1, user_2, bot):
    item_1 = None
    item_2 = None

    item_1 = await interract_game.player_choose_item(ctx= ctx, user= user_1, bot= bot, timeout=CHOICE_TIMEOUT)
    item_2 = await interract_game.player_choose_item(ctx= ctx, user= user_2, bot= bot, timeout=CHOICE_TIMEOUT)
    return item_1, item_2


async def fight(ctx: Context, user_1, user_2, bot, bully_1:Bully, bully_2:Bully, for_fun = False, item_1:Optional[Item] = None, item_2:Optional[Item] = None):
    #On initialise les variables pour le combat :
    max_pv_1 = bully_1.max_pv
    max_pv_2 = bully_2.max_pv
    
    stat_base_1 = [bully_1.strength, bully_1.agility, bully_1.lethality, bully_1.viciousness]
    stat_base_2 = [bully_2.strength, bully_2.agility, bully_2.lethality, bully_2.viciousness]
    
    pv_1, pv_2 = await fight_simulation(ctx= ctx, user_1= user_1, user_2= user_2, bot= bot, 
                                        stat_base_1= stat_base_1, stat_base_2= stat_base_2, name_1= bully_1.name, name_2=bully_2.name, 
                                        max_pv_1= max_pv_1, max_pv_2= max_pv_2, 
                                        lvl_1= bully_1.lvl, lvl_2= bully_2.lvl,
                                        item_1= item_1, item_2= item_2)
    
    if(pv_1 <= 0):
        bully_gagnant = bully_2
        bully_perdant = bully_1
    if(pv_2 <= 0):
        bully_gagnant = bully_1
        bully_perdant = bully_2
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
            user_gagnant = user_1 if bully_gagnant == bully_1 else user_2
            money.give_money(user_id=user_gagnant.id, montant=gold_earned)
            pretext += f"{user_gagnant.name} earned {gold_earned}{money.MONEY_ICON}\n"
        bully_perdant.kill()
        await ctx.channel.send(f"{pretext}{bully_perdant.name} died in terrible agony")

    return


def value_to_bar_str(v:int, max_value=10):
    v = max(0,v) #Pour éviter des valeurs négatives
    t = ""
    for k in range(v):
        t += "▮"
    for k in range(max_value-v):
        t += "."
    return t


# ____________________________________________________
async def fight_simulation(ctx, bot, stat_base_1, stat_base_2, name_1, name_2, max_pv_1 = 10, max_pv_2 = 10,
                            lvl_1 = 1, lvl_2 = 1,
                            user_1 = None, user_2 = None, is_switch_possible = False, 
                            item_1:Optional[Item] = None, item_2:Optional[Item] = None, channel_cible = None):
    """
    return : (pv_restant_joueur_1, pv_restant_joueur_2)
    """

    if(channel_cible == None):
        channel_cible = ctx.channel

    #On initialise les variables pour le combat :
    tour = random.randint(0,1)
    
    #S'il y a des items, on change les valeurs des variables :
    if(item_1 != None and item_1.is_bfr_fight) : 
        max_pv_1, stat_base_1, max_pv_2, stat_base_2 = item_1.effect_before_fight(pv_self=max_pv_1, stat_self=stat_base_1, pv_adv=max_pv_2, stat_adv=stat_base_2, lvl_self=lvl_1, lvl_adv=lvl_2)
    if(item_2 != None and item_2.is_bfr_fight) : 
        max_pv_2, stat_base_2, max_pv_1, stat_base_1 = item_2.effect_before_fight(pv_self=max_pv_2, stat_self=stat_base_2, pv_adv=max_pv_1, stat_adv=stat_base_1, lvl_self=lvl_2, lvl_adv=lvl_1)
    pv_1 = max_pv_1
    pv_2 = max_pv_2

    print("pv_1 : ", pv_1)
    print("pv_2 : ", pv_2)
    print("stat_base_1 : ", stat_base_1)
    print("stat_base_2 : ", stat_base_2)

    #On calcul le texte
    barre_pv_joueur = value_to_bar_str(pv_1, max_value=max_pv_1)
    barre_pv_enemy = value_to_bar_str(pv_2, max_value=max_pv_2)

    text_pv_combat = "\t\tBully 1 : " + name_1 + "\nhp : " + barre_pv_joueur + "\n\n\t\t\t\tVS\n\n\t\tBully 2 : " + name_2 + "\nhp : " + barre_pv_enemy
    action_combat = "Let's get ready to rumble!"
    text_combat = "```" + text_pv_combat + "\n\n" + action_combat + "```"

    emoji_recap_j1 = ""
    emoji_recap_j2 = ""
    
    #On affiche le texte
    message = await channel_cible.send(text_combat)
    if(is_switch_possible):
        await message.add_reaction('🔁')
    await asyncio.sleep(fight_msg_time_update)

    while pv_1 > 0 and pv_2 > 0 :
        #On l'action
        (text_action, pv_perdu_1, pv_perdu_2,  emoji_j1, emoji_j2, tour) = nouvelle_action_stat(stat_base_1= stat_base_1, stat_base_2= stat_base_2, name_1= name_1, name_2= name_2, tour= tour)

        #On save les emoji pour la frise chronologique
        emoji_recap_j1+= emoji_j1
        emoji_recap_j2+= emoji_j2

        #on maj les parametres des pv 
        pv_1 -= pv_perdu_1
        pv_2 -= pv_perdu_2
        barre_pv_joueur = value_to_bar_str(pv_1, max_value=max_pv_1)
        barre_pv_enemy = value_to_bar_str(pv_2, max_value=max_pv_2)

        #On fait visuellement la modif de pv : 
        text_pv_combat = "\t\tBully 1 : " + name_1 + "\nhp : " + barre_pv_joueur + "\n\t\t\t\t\t" + emoji_recap_j1 + "\n\t\t\t\tVS\n\t\t\t\t\t" + emoji_recap_j2 + "\n\t\tBully 2 : " + name_2 + "\nhp : " + barre_pv_enemy
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
                raise InterruptionCombat(pv_1= pv_1, pv_2= pv_2)
            # message = await message.channel.fetch_message(message.id)
            # user_reacted = False
            # for reaction in message.reactions:
            #     if str(reaction.emoji) == '🔁' :
            #         async for user in reaction.users():
            #             if user == user_1:
            #                 user_reacted = True
            #                 break  # No need to continue checking reactions
            #         if user_reacted:
            #             break
            # if(user_reacted):
            #     raise InterruptionCombat(pv_1= pv_1, pv_2= pv_2)
                

    return pv_1, pv_2

async def test_interruption_combat_reaction(user, message, reaction_interrupt):
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
def nouvelle_action_stat(stat_base_1, stat_base_2, name_1, name_2, tour):
    """
    tour est égale à 0 ou 1. Il indique le tour du bully qui devrait normalement agir maintenant. 0 = bully_1, 1 = bully_2
    Retourne un tuple sous la forme : 
    (text_action, pv_perdu_j1, pv_perdu_j2, emoji_j1, emoji_j2, tour)
    """
    Emotes_possibles = ["👊", "🩸", "🛡️","🔪", "💥"] # ,"💔" #C'est juste pour pouvoir copier/coller
    text_action = ""
    pv_perdu_j1 = 0
    pv_perdu_j2 = 0
    pv_perdu = 0
    emoji_j1=""
    emoji_j2=""

    stat_j1 = stat_base_1.copy()
    stat_j2 = stat_base_2.copy()

    #On regarde les fourberies
    fourberie_j1 = challenge_viciosite_stats(stat_j1, stat_j2)
    fourberie_j2 = challenge_viciosite_stats(stat_j2, stat_j1)
    if(fourberie_j1 and not fourberie_j2):
        #La meilleure de j2 (hors viciosite) devient égale au minimum entre : la stat de j1-1 et sa propre stat - 1. (minimum 1)
        max_value, max_index = max((value, index) for index, value in enumerate(stat_j2[0:3]))
        #stat_j2[max_index] = max(1, min(stat_j1[max_index], stat_j2[max_index]) - 1)
        if (stat_j2[max_index] <= stat_j1[max_index]):
            stat_j2[max_index] = max(1,stat_j2[max_index] - 1)
        else :
            diff = stat_j2[max_index] - stat_j1[max_index]
            stat_j2[max_index] = max (1,stat_j1[max_index] - 1 + round(diff * (1 - math.exp(-stat_j2[3]/stat_j1[3] / 1.5)) ))
    
    if(fourberie_j2 and not fourberie_j1):
        #La meilleure de j1 (hors viciosite) devient egale au minimum entre : la stat de j2-2 et sa propre stat - 1. (minimum 1)
        max_value, max_index = max((value, index) for index, value in enumerate(stat_j1[0:3]))
        #stat_j1[max_index] = max(1, min(stat_j2[max_index], stat_j1[max_index]) - 1)
        if (stat_j1[max_index] <= stat_j2[max_index]):
            stat_j1[max_index] = max(1,stat_j1[max_index] - 1)
        else :
            diff = stat_j1[max_index] - stat_j2[max_index]
            stat_j1[max_index] = max (1,stat_j2[max_index] - 1 + round(diff * (1 - math.exp(-stat_j1[3]/stat_j2[3] / 1.5)) ))

    
    (name_actif, stat_j_actif), (name_passif, stat_j_passif) = ((name_1, stat_j1.copy()), (name_2, stat_j2.copy())) if tour==0 else ((name_2, stat_j2.copy()), (name_1, stat_j1.copy()))

    if challenge_prendre_de_vitesse_stats(stat_j_passif, stat_j_actif) :
        #On inverse le tour
        tour = (tour - 1) * - 1 
        (name_actif, stat_j_actif), (name_passif, stat_j_passif) = ((name_1, stat_j1.copy()), (name_2, stat_j2.copy())) if tour==0 else ((name_2, stat_j2.copy()), (name_1, stat_j1.copy()))
        
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
    return (text_action, pv_perdu_j1, pv_perdu_j2, emoji_j1, emoji_j2, tour)

# Pour les comparaisons de stat ____________________________________
def challenge_prendre_de_vitesse_stats(stat_voulant_rejouer, stat_qui_attaque_normalement):
    stat_veux_rejouer_agility = stat_voulant_rejouer[1]
    stat_attaquant_normal_agility = stat_qui_attaque_normalement[1]
    rejouer = Bully.clash_stat(stat_veux_rejouer_agility, stat_attaquant_normal_agility)
    return rejouer

def challenge_defense_stats(stat_attaquant, stat_defenseur):
    stat_att_strength = stat_attaquant[0]
    stat_def_strength = stat_defenseur[0]
    parade_reussie = Bully.clash_stat(st_actif = stat_def_strength, st_passif = stat_att_strength)
    return parade_reussie

def challenge_coup_critique_stats(stat_attaquant, stat_defenseur):
    stat_att_lethality = stat_attaquant[2]
    stat_def_strength = stat_defenseur[0]
    coup_critique = Bully.clash_stat(st_actif = stat_att_lethality, st_passif = stat_def_strength)
    return coup_critique

def challenge_viciosite_stats(stat_attaquant, stat_defenseur):
    stat_att_vicieux = stat_attaquant[3]
    stat_def_vicieux = stat_defenseur[3]
    minim = min(stat_att_vicieux, stat_def_vicieux)
    fourberie = Bully.clash_stat(st_actif = stat_att_vicieux, st_passif = stat_def_vicieux, neutre=minim)
    
    return fourberie

# __________________________________________________________________
# ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

# Les récompenses ____________________________________
def reward_win_fight(b_win, b_lose):
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

def check_reaction_number(author, sent_message):
    def inner_check(reaction, user): 
        return author.id == user.id and sent_message.id == reaction.message.id and str(reaction.emoji) in ["\u0030\u20E3", "\u0031\u20E3", "\u0032\u20E3", "\u0033\u20E3", "\u0034\u20E3"]
    
    return inner_check

# emote <-> int

def from_number_to_emote(nb):
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

def from_emote_to_number(emote):
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
         
    return -1

class InterruptionCombat(Exception):
    def __init__(self, pv_1, pv_2, text=""):
        self.pv_1 = pv_1
        self.pv_2 = pv_2
        super().__init__(f"{text}. [pv_1 = {pv_1}, pv_2 = {pv_2}]")