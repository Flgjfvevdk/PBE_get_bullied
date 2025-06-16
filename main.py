# bot.py
import math
from dotenv import load_dotenv

from utils.discord_servers import load_servers, save_server

load_dotenv()

import os
from typing import Optional
import discord
from discord.ext import commands
from pathlib import Path

from utils.helpers import getenv
from utils.locks import PlayerLock
import utils.decorators as decorators
import interact_game
import fight_manager
import donjon
import ruine
import money
import shop
import bully
import utils.database as database
from player_info import Player
import arena_system
from arena_system import Arena
import tuto_text
import lootbox
import consumable
import trades
import tournament

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import configure_mappers

import asyncio
from utils.color_str import CText
from utils.paginate import paginate, paginate_dict

from discord.ext.commands import Bot, Context, CommandNotFound
from discord import Embed
import reserve
from supply_machine import run_snack_machine, run_water_fountain
from all_texts import getText


TOKEN = getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

TEXT_JOIN_THE_GAME:str = getText("join")

class GetBulliedBot(Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def session(self) -> AsyncSession:
        return database.new_session()

bot = GetBulliedBot(command_prefix = "$$", intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} is now running !')
    await shop.init_shop()
    # await keys.init_keys_restock()
    await check_add_bot_database(bot)
    await arena_system.update_arenas(bot)
    await tournament.init_tournaments(bot)

@bot.event
async def on_command_error(ctx: Context, error):
    print(error)
    if isinstance(error, CommandNotFound):
        return
    
async def check_add_bot_database(bot: Bot) -> None:
    if bot.user is None: return
    async with database.new_session() as session:
        await interact_game.make_bot_join(bot.user, session)

# Command général ____________________________________________________________________________________
@bot.command()
@decorators.categories("Game")
async def join(ctx: Context):
    """Pour rejoindre le jeu"""
    async with database.new_session() as session:
        await interact_game.join_game(ctx, user=ctx.author, session=session)

@bot.command(aliases=['parrain', 'referral', 'parrainage'])
@decorators.categories("Game")
async def invite(ctx: Context, user:discord.Member):
    """Pour inviter un amis à rejoindre le jeu"""
    async with database.new_session() as session:
        player_parrain = await session.get(Player, ctx.author.id)
        if player_parrain is None:
            await ctx.reply(TEXT_JOIN_THE_GAME)
            return
        if await session.get(Player, user.id) is not None :
            await ctx.reply(getText("other_already_joined").format(other=user))
            return
        await interact_game.invite_join(ctx, player_parrain, user, session=session)
       

@bot.command(aliases=['py', 'pay'])
@decorators.categories("Money")
async def payday(ctx: Context):
    """Pour recevoir des 🩹"""
    async with database.new_session() as session:
        player = await session.get(Player, ctx.author.id)
        if player is None:
            await ctx.reply(TEXT_JOIN_THE_GAME)
            return
        
        cooldown_restant = await money.cooldown_restant_pay(player)
        if cooldown_restant > 0:
            await ctx.send(getText("cooldown_wait").format(cd=money.format_temps(round(cooldown_restant))))
            return

        server_id = ctx.guild.id #type: ignore
        bonus_champion = await arena_system.get_bonus_payday(session, server_id, player.id.__str__())
        bonus_arena_str = getText("arena_bonus_py").format(bonus=bonus_champion) if bonus_champion > 1 else ""
        # bonus_arena_str = f"×{bonus_champion} (arena champion bonus)" if bonus_champion > 1 else ""
        py_val = money.payday_value(player)
        money.give_money(player, montant=py_val * bonus_champion)
        await ctx.send(getText("payday").format(recu=py_val, bonus_str=bonus_arena_str, money_emoji=money.MONEY_EMOJI, total_money=money.get_money_user(player)))
        # await ctx.send(
        #     f"Vous avez reçu des {money.MONEY_EMOJI} ! +{py_val}{money.MONEY_EMOJI} {bonus_arena_str}\n"
        #     f"Vous avez {money.get_money_user(player)} {money.MONEY_EMOJI}"
        # )

        # Enregistrer l'heure actuelle comme dernière utilisation de la commande
        money.enregistrer_cooldown_pay(player)
        await session.commit()

@bot.command(aliases=['money'])
@decorators.categories("Money")
async def bank(ctx: Context):
    """Afficher ses ressources"""
    async with database.new_session() as session:
        player = await session.get(Player, ctx.author.id)
        if player is None:
            await ctx.reply(TEXT_JOIN_THE_GAME)
            return
        await ctx.send(getText("bank").format(money=money.get_money_user(player), money_emoji=money.MONEY_EMOJI))
        # await ctx.send(f"You have {money.get_money_user(player)} {money.MONEY_EMOJI}")



@bot.command(aliases=['patch', 'update'])
async def patchnote(ctx: Context):
    """Nouvelle mise à jour récente"""
    await ctx.channel.send(tuto_text.patchnote)

@bot.command(aliases=['leader', 'rank'])
@decorators.categories("Game")
async def leaderboard(ctx: Context):
    """Affiche le classement des joueurs en fonction du donjon maximum terminé."""
    async with database.new_session() as session:
        lb = Embed(title="Leaderbord Donjon", description=await donjon.str_leaderboard_donjon(session))
        await ctx.channel.send(embed=lb)
    

@bot.command(aliases=['shop', 'ps'])
@decorators.categories("Money")
async def print_shop(ctx: Context):
    """Affiche le shop de ce server"""
    await shop.print_shop(ctx, bot)

@bot.command(aliases=['lootbox', 'lb'])
@decorators.categories("Money")
async def buy_lootbox(ctx: Context):
    """Pour acheter une lootbox"""
    user = ctx.author
    if not PlayerLock(user.id).check():
        await ctx.reply(getText("already_in_action"))
        return
    await lootbox.shop_lootbox(ctx, user=user)

@bot.command(aliases=['credit'])
async def credits(ctx: Context):
    """Affiche les crédits"""
    await ctx.send(getText("credits"))

@bot.command(aliases=['suicide', 'kill'])
@decorators.categories("Bully")
async def sacrifice(ctx: Context):
    """Élimine un bully de son club"""
    user = ctx.author
    lock = PlayerLock(user.id)
    if not lock.check():
        await ctx.send(getText("already_in_action"))
        # await ctx.send("You are already in an action.")
        return
    with lock:
        async with database.new_session() as session:
            p = await session.get(Player, user.id)
            if p is None:
                await ctx.reply(TEXT_JOIN_THE_GAME)
                return
            await interact_game.suicide_bully(ctx, user=user, player=p, bot=bot)
            await session.commit()

    return

# //////////////////////////////////////////////////////////////////////////////////////////////////////

#Les tutos : ___________________________________________________________
@bot.command()
@decorators.categories("Tuto")
async def tuto(ctx: Context):
    """Affiche un tutoriel général. Faites le si vous êtes perdu !"""
    await ctx.channel.send(tuto_text.tuto)
@bot.command(aliases=['tuto_b'])
@decorators.categories("Tuto", "Bully")
async def tuto_bully(ctx: Context):
    """Affiche un tutoriel concernant le fonctionnemet des bullies"""
    await ctx.channel.send(tuto_text.tuto_bully)
@bot.command(aliases=['tuto_f'])
@decorators.categories("Tuto", "Bully")
async def tuto_fight(ctx: Context):
    """Affiche un tutoriel concernant les combats"""
    await ctx.channel.send(tuto_text.tuto_fight)
@bot.command(aliases=['tuto_d', 'tuto_donjon'])
@decorators.categories("Tuto", "Fight")
async def tuto_dungeon(ctx: Context):
    """Affiche un tutoriel concernant les donjons"""
    await ctx.channel.send(tuto_text.tuto_dungeon)
@bot.command(aliases=['tuto_r', 'tuto_ruine'])
@decorators.categories("Tuto", "Fight")
async def tuto_ruin(ctx: Context):
    """Affiche un tutoriel concernant les ruines"""
    await ctx.channel.send(tuto_text.tuto_ruin)
@bot.command(aliases=['tuto_s'])
@decorators.categories("Tuto", "Money")
async def tuto_shop(ctx: Context):
    """Affiche un tutoriel concernant le shop"""
    await ctx.channel.send(tuto_text.tuto_shop)
@bot.command(aliases=['tuto_lb', 'tuto_l'])
@decorators.categories("Tuto", "Money")
async def tuto_lootbox(ctx: Context):
    """Affiche un tutoriel concernant les lootbox"""
    await ctx.channel.send(tuto_text.tuto_lootbox)
@bot.command(aliases=['tuto_buffs'])
@decorators.categories("Tuto", "Bully")
async def tuto_buff(ctx: Context):
    """Affiche un tutoriel concernant les buffs"""
    await ctx.channel.send(tuto_text.tuto_buff)
@bot.command(aliases=['tuto_conso', 'tuto_consumables'])
@decorators.categories("Tuto", "Consumable")
async def tuto_consumable(ctx: Context):
    """Affiche un tutoriel concernant les consommables"""
    await ctx.channel.send(tuto_text.tuto_consumable)
@bot.command(aliases=['list_buff', 'liste_buff', 'liste_buffs', 'buffs', 'buff'])
@decorators.categories("Tuto", "Bully")
async def list_buffs(ctx: Context):
    """Affiche la liste des buffs"""
    txt = ""
    from buffs import name_to_buffs_class
    from fighting_bully import CategoryBuff
    dict_text:dict[str, str] = {"Buffs Positifs":"", "Buffs Négatifs":""}
    for buffClass in name_to_buffs_class.values():
        if buffClass.category == CategoryBuff.NONE:
            continue
        category = buffClass.category.name
        if category not in dict_text:
            dict_text[category] = ""
        dict_text[category] += f"{buffClass.__name__} : {buffClass.description}\n"

    await paginate_dict(ctx, dict_text=dict_text)


# //////////////////////////////////////////////////////////////////////////////////////////////////////

#Les combats : ___________________________________________________________
@bot.command(aliases=['ch', 'fight'])
@decorators.categories("Fight")
async def challenge(ctx: Context, opponent:discord.Member):
    """Pour provoquer un joueur en duel à mort, bully vs bully"""
    user = ctx.author

    lock1 = PlayerLock(user.id)
    if not lock1.check():
        await ctx.send(getText("already_in_action"))
        return
    lock2 = PlayerLock(opponent.id)
    if not lock2.check():
        await ctx.send(getText("other_is_in_action").format(user=opponent))
        return
    
    with lock1, lock2:
        async with database.new_session() as session:
            p1 = await session.get(Player, user.id)
            p2 = await session.get(Player, opponent.id)
            if p1 is None:
                await ctx.reply(TEXT_JOIN_THE_GAME)
                return
            if p2 is None:
                await ctx.reply(getText("other_hasnt_joined").format(other=opponent))
                return
            await fight_manager.proposition_fight(ctx, user, opponent, p1, p2, bot)
            await session.commit()

    return

@bot.command(aliases=['fch', 'fun_fight'])
@decorators.categories("Fight")
async def fun_challenge(ctx: Context, opponent:discord.Member):
    """Pour provoquer un joueur en duel amical, bully vs bully"""
    user = ctx.author
    
    lock1 = PlayerLock(user.id)
    if not lock1.check():
        await ctx.send(getText("already_in_action"))
        #await ctx.send("You are already in an action.")
        return
    lock2 = PlayerLock(opponent.id)
    if not lock2.check():
        await ctx.send(getText("other_is_in_action").format(user=opponent))
        # await ctx.channel.send(f"Sorry, but {opponent} is already busy!")
        return

    with lock1, lock2:
        async with database.new_session() as session:
            p1 = await session.get(Player, user.id)
            p2 = await session.get(Player, opponent.id)
            if p1 is None:
                await ctx.reply(TEXT_JOIN_THE_GAME)
                return
            if p2 is None:
                await ctx.reply(getText("other_hasnt_joined").format(other=opponent))
                return
            await fight_manager.proposition_fight(ctx, user, opponent, p1, p2, bot, for_fun=True)

    return

@bot.command(aliases=['tch', 'teamfight', 'team_fight'])
@decorators.categories("Fight")
async def team_challenge(ctx: Context, opponent:discord.Member):
    """Pour provoquer un joueur en combat (amical) TEAM vs TEAM"""
    user = ctx.author

    if user == opponent:
        await ctx.send(getText("cant_self_tf"))
        return
    
    lock1 = PlayerLock(user.id)
    if not lock1.check():
        await ctx.send(getText("already_in_action"))
        # await ctx.send("You are already in an action.")
        return
    lock2 = PlayerLock(opponent.id)
    if not lock2.check():
        await ctx.send(getText("other_is_in_action").format(user=opponent))
        # await ctx.channel.send(f"Sorry, but {opponent} is already busy!")
        return

    with lock1, lock2:
        async with database.new_session() as session:
            p1 = await session.get(Player, user.id)
            p2 = await session.get(Player, opponent.id)
            if p1 is None:
                await ctx.reply(TEXT_JOIN_THE_GAME)
                return
            if p2 is None:
                await ctx.reply(getText("other_hasnt_joined").format(other=opponent))
                return
            await fight_manager.proposition_team_fight(ctx, user_1=user, user_2=opponent, player_1=p1, player_2=p2, for_fun=True)

    return

    
@bot.command(aliases=['dungeon', 'donjon', 'dj', 'dg'])
@decorators.categories("Fight")
async def explore_dungeon(ctx: Context, level:int|str):
    """Pour explorer un donjon. Très utile pour xp rapidement"""
    if isinstance(level, str):
        for dg_tags in donjon.special_dg_name_number.values():
            if level in dg_tags:
                level = next(key for key, value in donjon.special_dg_name_number.items() if level in value)
                break
        else : 
            await ctx.send(getText("dg_error_param"))
            # await ctx.channel.send("Dungeon level must be a number (or a specific keyword).")
            return
    
    if(level <= 0) :
        await ctx.send(getText("dg_greater_0"))
        # await ctx.channel.send("Dungeon level must be greater than 0.")
        return
    if level > 50 and level not in donjon.special_dg_name_number.keys():
        await ctx.send(getText("dg_lower_50"))
        # await ctx.channel.send("Level max is 50.")
        return

    user = ctx.author
    lock = PlayerLock(user.id)
    if not lock.check():
        await ctx.send(getText("already_in_action"))
        return

    with lock:
        async with database.new_session() as session:
            player = await session.get(Player, user.id)
            if player is None:
                await ctx.reply(TEXT_JOIN_THE_GAME)
                return
            
            pallier_boss_vaincu = math.floor(player.max_dungeon/10) * 10
            if (level - 10 > pallier_boss_vaincu) and level not in donjon.special_dg_name_number.keys():
                pallier_minimum = math.floor((level-1)/10)*10
                await ctx.send(getText("dg_pallier").format(lvl_pallier=pallier_minimum))
                return

            try :
                await donjon.Dungeon(ctx, bot, player, level).enter()
            except Exception as e:
                print(e)
                raise e
            await session.commit()
    

@bot.command(aliases=['ruin', 'ruine'])
@decorators.categories("Fight")
async def explore_ruin(ctx: Context, level:int):
    """Pour explorer une ruine. Très utile pour obtenir des items et de la monnaie"""
    if(level <= 0) :
        await ctx.send(getText("ruin_greater_0"))
        # await ctx.channel.send("Ruin level must be greater than 0")
        return
    if(level > 50) :
        await ctx.send(getText("ruin_lower_50"))
        # await ctx.channel.send("50 is the maximum")
        return
    
    user = ctx.author
    lock = PlayerLock(user.id)
    if not lock.check():
        await ctx.send(getText("already_in_action"))
        # await ctx.send("You are already in an action.")
        return

    with lock:
        async with database.new_session() as session:
            player = await session.get(Player, user.id)
            if player is None:
                await ctx.reply(TEXT_JOIN_THE_GAME)
                return
            try:
                await ruine.Ruin(ctx, bot, player, level).enter()
            except Exception as e :
                raise e
            await session.commit()


@challenge.error
@fun_challenge.error
@team_challenge.error
@explore_dungeon.error
@explore_ruin.error
async def challenge_error(ctx: Context, error: commands.CommandError):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(getText("missing_argument").format(arg=error.param.name))
        # await ctx.send(f"Error: Missing required argument `{error.param.name}`.")

@bot.command(aliases=['arene'])
@decorators.categories("Fight")
async def arena(ctx: Context):
    """Pour afficher l'arène"""
    if ctx.guild is None:
        return

    user = ctx.author
    server_id = ctx.guild.id
    async with database.new_session() as session:
        arena = await session.get(Arena, server_id)
        if arena is None:
            await ctx.send(getText("no_arena"))
            # await ctx.send("No arena found for this server. Please create an arena first.")
            return

        player = await session.get(Player, user.id)
        if player is None:
            await ctx.reply(TEXT_JOIN_THE_GAME)
            return

        arena_fight = arena_system.ArenaFight(arena, ctx=ctx, session=session, bot=bot, user=user, player=player)
        await arena_fight.enter_hall()


# //////////////////////////////////////////////////////////////////////////////////////////////////////

# Par rapport au club ____________________________
@bot.command(aliases=['print', 'pr', 'bullies', 'team', 'equipe', 'bully'])
@decorators.categories("Bully")
async def club(ctx: Context, user:Optional[discord.User |discord.Member] = None):
    """Affiche les bullies d'un joueur"""
    if(user is None):
        user = ctx.author
    async with database.new_session() as session:
        player = await session.get(Player, user.id)
        if player is None:
            await ctx.reply(TEXT_JOIN_THE_GAME)
            return
        await interact_game.print_bullies(ctx, player, print_images = True)

@bot.command(aliases=['reserve'])
@decorators.categories("Bully")
async def print_reserve(ctx: Context, user:Optional[discord.User |discord.Member] = None):
    """Affiche les bullies de la réserve d'un joueur"""
    if(user is None):
        user = ctx.author
    async with database.new_session() as session:
        player = await session.get(Player, user.id)
        if player is None:
            await ctx.reply(TEXT_JOIN_THE_GAME)
            return
        await reserve.print_reserve(ctx, user, player, bot, session=session, print_images = True)
        
@bot.command(aliases=['exchange', 'trade_offer'])
@decorators.categories("Bully")
async def trade(ctx: Context, other:discord.Member):
    """Pour faire un échange de bullies"""
    user = ctx.author
    if user == other:
        await ctx.send(getText("cant_trade_self"))
        return
 
    async with database.new_session() as session:
        p1 = await session.get(Player, user.id)
        p2 = await session.get(Player, other.id)
        if p1 is None:
            await ctx.reply(TEXT_JOIN_THE_GAME)
            return
        if p2 is None:
            await ctx.reply(getText("other_hasnt_joined").format(other=other))
            # await ctx.reply(f"{other} has not joined the game.")
            return
        await trades.trade_offer(ctx, user, other, p1, p2)
        await session.commit()

    return


@bot.command(aliases=['h'])
@decorators.categories("Bully")
async def hire(ctx: Context):
    """Pour engager un NOBODY"""
    user = ctx.author
    lock = PlayerLock(user.id)
    if not lock.check():
        await ctx.send(getText("already_in_action"))
        # await ctx.send("You are already in an action.")
        return

    with lock:
        async with database.new_session() as session:
            player = await session.get(Player, ctx.author.id)
            if player is None:
                await ctx.reply(TEXT_JOIN_THE_GAME)
                return
            await interact_game.add_random_bully_to_player(ctx, player, interact_game.generate_name())
            await session.commit()

@bot.command(aliases=['h_all', 'hall', 'hh'])
@decorators.categories("Bully")
async def hire_all(ctx: Context):
    """Pour remplir son club de NOBODY"""
    user = ctx.author
    lock = PlayerLock(user.id)
    if not lock.check():
        await ctx.send(getText("already_in_action"))
        # await ctx.send("You are already in an action.")
        return

    with lock:
        async with database.new_session() as session:
            player = await session.get(Player, ctx.author.id)
            if player is None:
                await ctx.reply(TEXT_JOIN_THE_GAME)
                return
            for _ in range(interact_game.BULLY_NUMBER_MAX):
                await interact_game.add_random_bully_to_player(ctx, player, interact_game.generate_name(), talkative=False)
            await session.commit()

@bot.command()
@decorators.is_admin()
@decorators.categories("Admin")
async def kill_all(ctx: Context):
    user = ctx.author
    lock = PlayerLock(user.id)
    if not lock.check():
        await ctx.send(getText("already_in_action"))
        # await ctx.send("You are already in an action.")
        return
    with lock:
        async with database.new_session() as session:
            player = await session.get(Player, user.id)
            if player is None:
                await ctx.reply(TEXT_JOIN_THE_GAME)
                return
            all_bullies = player.bullies
            for b in all_bullies:
                if isinstance(b, bully.Bully):
                    await b.kill()
            await session.commit()
    

@bot.command(aliases=['use_c', 'use_conso', 'use_consumables'])
@decorators.categories("Consumable")
async def use_consumable(ctx: Context):
    """Pour utiliser un consommable"""
    user = ctx.author
    lock = PlayerLock(user.id)
    if not lock.check():
        await ctx.send(getText("already_in_action"))
        return

    with lock:
        async with database.new_session() as session:
            player = await session.get(Player, ctx.author.id)
            if player is None:
                await ctx.reply(TEXT_JOIN_THE_GAME)
                return
            await consumable.use_consumable(ctx=ctx, user=user, player=player, session=session, bot=bot)
            await session.commit()

@bot.command(aliases=['consommable', 'consumable', 'conso', 'print_c'])
@decorators.categories("Consumable")
async def print_consumables(ctx: Context):
    """Pour afficher vos consommables"""
    user = ctx.author

    async with database.new_session() as session:
        player = await session.get(Player, ctx.author.id)
        if player is None:
            await ctx.reply(TEXT_JOIN_THE_GAME)
            return
        embed = consumable.embed_consumables(player,user)
        await ctx.channel.send(embed=embed)

@bot.command(aliases=['del_c', 'delete_conso', 'remove_conso'])
@decorators.categories("Consumable")
async def del_conso(ctx: Context):
    """Pour supprimer un consommable"""
    user = ctx.author
    lock = PlayerLock(user.id)
    if not lock.check():
        await ctx.send(getText("already_in_action"))
        return

    with lock:
        async with database.new_session() as session:
            player = await session.get(Player, ctx.author.id)
            if player is None:
                await ctx.reply(TEXT_JOIN_THE_GAME)
                return

            await consumable.remove_consumable(ctx, user, player)
            await session.commit()

# //////////////////////////////////////////////////////////////////////////////////////////////////////
# Les commandes pour les supply_bully : 
@bot.command(aliases=['sm', 'snack', 'smachine', 'snackmachine'])
@decorators.categories("Consumable")
async def snack_machine(ctx: Context, value:int|None = None):
    """Pour acheter un consommable snack (modifie les stats)"""
    user = ctx.author
    lock = PlayerLock(user.id)
    if not lock.check():
        await ctx.send(getText("already_in_action"))
        return
    with lock:
        async with database.new_session() as session:
            player = await session.get(Player, user.id)
            if player is None:
                await ctx.reply(TEXT_JOIN_THE_GAME)
                return

            await run_snack_machine(ctx, bot, session, user, player = player, value = value)

@bot.command(aliases=['wf', 'water', 'fontaine', 'waterfountain', 'eau'])
@decorators.categories("Consumable")
async def water_fountain(ctx: Context, level: int | None = None):
    """Pour acheter un consommable eau XP."""
    user = ctx.author
    lock = PlayerLock(user.id)
    if not lock.check():
        await ctx.send(getText("already_in_action"))
        return
    with lock:
        async with database.new_session() as session:
            player = await session.get(Player, user.id)
            if player is None:
                await ctx.reply(TEXT_JOIN_THE_GAME)
                return

            await run_water_fountain(ctx, bot, session, user, player, value=level)

# //////////////////////////////////////////////////////////////////////////////////////////////////////

#Command d'admin _____________________________________________________________________________________________________
@bot.command()
@decorators.is_admin()
@decorators.categories("Admin")
async def admin_give(ctx: Context,user: discord.User, name: str, lvl:int, rarity:str , strength: float, agility: float, lethality: float, viciousness: float, path_image: str = "", seed_str:str = "", max_pv:int = bully.BULLY_MAX_BASE_HP, buff_tag:str = "NoBuff"):
    stats = bully.Stats(strength, agility, lethality, viciousness)
    
    b = bully.Bully(name=name, rarity= bully.Rarity[rarity], stats=stats)
    b.lvl = lvl
    b.max_pv = max_pv
    b.buff_fight_tag = buff_tag
    sum_stats = stats.sum_stats() 
    if seed_str == "" :
        b.seed = bully.Seed(stats.strength/sum_stats, stats.agility/sum_stats, stats.lethality/sum_stats, stats.viciousness/sum_stats)
    else : 
        s_strength, s_agility, s_lethality, s_viciousness = map(float, seed_str.split(","))
        if bully.Rarity[rarity] != bully.Rarity.UNIQUE : 
            tot = s_strength + s_agility + s_lethality + s_viciousness
            b.seed = bully.Seed(s_strength/tot, s_agility/tot, s_lethality/tot, s_viciousness/tot)
        else : 
            b.seed = bully.Seed(s_strength, s_agility, s_lethality, s_viciousness)
            
    if path_image != "":
        b.image_file_path=Path(path_image)

    
    async with database.new_session() as session:
        player = await session.get(Player, user.id)
        if player is None:
            await ctx.reply(getText("other_hasnt_joined").format(other=user))
            return
        await interact_game.add_bully_to_player(ctx, player, b)
        await session.commit()


@bot.command(aliases=['new_shop', 'ns'])
@decorators.is_admin()
@decorators.categories("Admin")
async def admin_new_shop(ctx: Context):
    try:
        await shop.restock_shop()
        await shop.print_shop(ctx, bot)
    except Exception as e:
        print(e)

@bot.command()
@decorators.is_admin()
@decorators.categories("Admin")
async def admin_add_server_to_list(ctx: Context):
    if ctx.guild is None:
        await ctx.send('This command can only be used in a server, not in a DM.')
        return
    
    shop_servers_id = load_servers()
    server_id = ctx.guild.id
    if server_id not in shop_servers_id:
        shop_servers_id.append(server_id)
        save_server(shop_servers_id)
        await ctx.send(f'Server {ctx.guild.name} has been saved!')
    else:
        await ctx.send(f'Server {ctx.guild.name} is already saved.')

@bot.command()
@decorators.is_admin()
@decorators.categories("Admin")
async def admin_set_max_dg_lvl(ctx: Context, lvl:int):
    async with database.new_session() as session:
        player = await session.get(Player, ctx.author.id)
        if player is None:
            await ctx.reply(TEXT_JOIN_THE_GAME)
            return
        player.max_dungeon = lvl
        await session.commit()

@bot.command()
@decorators.is_admin()
@decorators.categories("Admin")
async def admin_set_max_ruin_lvl(ctx: Context, lvl:int):
    async with database.new_session() as session:
        player = await session.get(Player, ctx.author.id)
        if player is None:
            await ctx.reply(TEXT_JOIN_THE_GAME)
            return
        player.max_ruin = lvl
        await session.commit()

@bot.command()
@decorators.is_admin()
@decorators.categories("Admin")
async def py_admin(ctx: Context):
    async with database.new_session() as session:
        player = await session.get(Player, ctx.author.id)
        if player is None:
            await ctx.reply(TEXT_JOIN_THE_GAME)
            return
        
        money.give_money(player, montant=10000)
        await ctx.send(
            f"Vous avez reçu des {money.MONEY_EMOJI} ! (+{10000}{money.MONEY_EMOJI})\n"
            f"Vous avez {money.get_money_user(player)} {money.MONEY_EMOJI}"
        )
        await session.commit()
    
@bot.command()
@decorators.is_admin()
@decorators.pbe_only()
@decorators.categories("Admin")
async def give_lvl(ctx: Context, nombre_lvl : Optional[int] = None ):
    user = ctx.author
    lock = PlayerLock(user.id)
    if not lock.check():
        await ctx.send("You are already in an action.")
        return

    with lock:
        async with database.new_session() as session:
            player = await session.get(Player, ctx.author.id)
            if player is None:
                await ctx.reply(TEXT_JOIN_THE_GAME)
                return
            nb_level = 1 if nombre_lvl is None else nombre_lvl
            await interact_game.increase_all_lvl(ctx, player, nb_level = nb_level)
            await session.commit()

@bot.command()
@decorators.is_admin()
@decorators.categories("Admin")
async def add_food(ctx: Context):
    user = ctx.author
    lock = PlayerLock(user.id)
    if not lock.check():
        await ctx.send("You are already in an action.")
        return
    
    with lock:
        async with database.new_session() as session:
            player = await session.get(Player, ctx.author.id)
            if player is None:
                await ctx.reply(TEXT_JOIN_THE_GAME)
                return
            c = consumable.AlimentEnum.Gigot.new_conso(2)
            player.consumables.append(c)
            await session.commit()

@bot.command()
@decorators.is_admin()
@decorators.categories("Admin")
async def add_water(ctx: Context):
    user = ctx.author
    lock = PlayerLock(user.id)
    if not lock.check():
        await ctx.send("You are already in an action.")
        return
    
    with lock:
        async with database.new_session() as session:
            player = await session.get(Player, ctx.author.id)
            if player is None:
                await ctx.reply(TEXT_JOIN_THE_GAME)
                return
            c = consumable.ConsumableWaterLvl("WaterMst", 3, bully.Rarity.MONSTER)
            player.consumables.append(c)
            await session.commit()

@bot.command()
@decorators.is_admin()
@decorators.categories("Admin")
async def add_elixir(ctx: Context, buff_name : str, cible_user:Optional[discord.User] = None):
    if cible_user is None : 
        user = ctx.author
    else : 
        user = cible_user
    lock = PlayerLock(user.id)
    if not lock.check():
        await ctx.send("You are already in an action.")
        return
    
    with lock:
        async with database.new_session() as session:
            player = await session.get(Player, user.id)
            if player is None:
                await ctx.reply(TEXT_JOIN_THE_GAME)
                return
            e = consumable.ConsumableElixirBuff(getText("elixir_of").format(elixir = buff_name), buff_name)
            player.consumables.append(e)
            await ctx.send(f"{user} has received an elixir of {buff_name}")
            await session.commit()

@bot.command()
@decorators.is_admin()
@decorators.categories("Admin")
async def del_all_c(ctx: Context):
    user = ctx.author
    lock = PlayerLock(user.id)
    if not lock.check():
        await ctx.send("You are already in an action.")
        return

    with lock:
        async with database.new_session() as session:
            player = await session.get(Player, ctx.author.id)
            if player is None:
                await ctx.reply(TEXT_JOIN_THE_GAME)
                return
            player.consumables = []
            await session.commit()


@bot.command(aliases=['update_arena', 'create_arena', 'create_arenas'])
@decorators.is_admin()
@decorators.categories("Admin")
async def update_arenas(ctx: Context):
    await arena_system.update_arenas(bot)
    await ctx.send("Arenas updated successfully.")

@bot.command()
@decorators.is_admin()
@decorators.categories("Admin")
async def bully_maj(ctx:Context):
    async with database.new_session() as session:
        result = await session.execute(select(bully.Bully))
        bullies = result.scalars().all()
        for b in bullies:
            difference_points = bully.nb_points_tot_rarity(b.lvl, b.rarity) - b.stats.sum_stats()
            print(f"{b.name}- diff:{difference_points}")
            nb_points:int = round(b.lvl * (b.lvl + 1) / 2)
            val = difference_points/nb_points
            b.increase_stat_with_seed(nb_level_points=nb_points, valeur=val)
        await session.commit() 

@bot.command()
@decorators.is_admin()
@decorators.categories("Admin")
async def reset_bully_images(ctx: Context):
    """Reset all bully images to random ones based on their rarity"""
    user = ctx.author
    lock = PlayerLock(user.id)
    if not lock.check():
        await ctx.send(getText("already_in_action"))
        return
    
    await ctx.send("Starting image reset for all bullies...")
    count = 0
    
    with lock:
        async with database.new_session() as session:
            result = await session.execute(select(bully.Bully))
            bullies = result.scalars().all()
            
            for b in bullies:
                old_path = b.image_file_path
                new_path = b.new_possible_image_random()
                b.image_file_path = new_path
                count += 1
                
                if count % 50 == 0:  # Progress update every 50 bullies
                    await ctx.send(f"Reset {count} bully images so far...")
            
            await session.commit()
    
    await ctx.send(f"Successfully reset images for {count} bullies!")

bot.remove_command('help')

@bot.command(name='help')
@decorators.categories("Game")
async def custom_help(ctx: Context):
    dict_text:dict[str, str] = {}
    
    for command in bot.commands:
        if not command.hidden:
            categories:list[str] = getattr(command.callback, 'categories', ["Uncategorized"])
            if len(categories) == 0:
                continue  # Skip commands without categories
            description = command.help or "No description."
            aliases = "[" + "; ".join(command.aliases) + "]" if command.aliases else ""
            command_info = f"**{command.name}** {aliases}: {description}\n"
            for category in categories:
                if category not in dict_text:
                    dict_text[category] = ""
                dict_text[category] += command_info
    
    dict_text.pop("Admin", None)
    #all the key are organized in alphabetic order : 
    dict_text = dict(sorted(dict_text.items(), key=lambda item: item[0]))
    await paginate_dict(ctx, dict_text, max_chars=700)

if __name__ == "__main__":
    if os.getenv("TESTING"):
        asyncio.run(database.init_models())
    bot.run(TOKEN)
