# bot.py
import os
from typing import Optional
from pathlib import Path
import discord
from discord.ext import commands

import utils
import interact_game
import fight_manager
import donjon
import ruine
import money
import keys
import shop
import bully
import item
import database
from player_info import Player
import tuto_text

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

import asyncio

from discord.ext.commands import Bot, Context, CommandNotFound
from discord import Embed

TOKEN = utils.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

class GetBulliedBot(Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def session(self) -> AsyncSession:
        return database.new_session()

bot = GetBulliedBot(command_prefix = "!!", intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} is now running !')
    await shop.init_shop()
    await keys.init_keys_restock()
    
    print("on est bien là")

@bot.event
async def on_command_error(ctx: Context, error):
    print(error)
    if isinstance(error, CommandNotFound):
        return
    


# Command général ____________________________________________________________________________________
@bot.command()
async def join(ctx: Context):
    async with database.new_session() as session:
        await interact_game.join_game(ctx, session)
        

@bot.command(aliases=['py', 'pay'])
async def payday(ctx: Context):
    async with database.new_session() as session:
        player = await session.get(Player, ctx.author.id)
        if player is None:
            await ctx.reply("Please join the game first !")
            return
        
        # Vérifier si l'utilisateur a déjà fait la commande récemment
        cooldown_restant = await money.cooldown_restant_pay(player)
        if cooldown_restant > 0:
            await ctx.send(f"Vous devez attendre encore {money.format_temps(round(cooldown_restant))} avant de pouvoir utiliser cette commande à nouveau.")
            return

        # Donner de l'argent à l'utilisateur
        money.give_money(player, montant=money.PAYDAY_VALUE)
        await ctx.send(
            f"Vous avez reçu des {money.MONEY_ICON} ! (+{money.PAYDAY_VALUE}{money.MONEY_ICON})\n"
            f"Vous avez {money.get_money_user(player)} {money.MONEY_ICON}"
        )

        # Enregistrer l'heure actuelle comme dernière utilisation de la commande
        money.enregistrer_cooldown_pay(player)
        await session.commit()

@bot.command(aliases=['money'])
async def bank(ctx: Context):
    async with database.new_session() as session:
        player = await session.get(Player, ctx.author.id)
        if player is None:
            await ctx.reply("Please join the game first !")
            return
        
        await ctx.send(f"You have {money.get_money_user(player)} {money.MONEY_ICON}")

@bot.command(aliases=['jeton', 'jetons', 'token', 'tokens', 'key', 'keys'])
async def print_key(ctx: Context):
    async with database.new_session() as session:
        player = await session.get(Player, ctx.author.id)
        if player is None:
            await ctx.reply("Please join the game first !")
            return
        
        await ctx.send(f"You have {keys.get_keys_user(player)} {keys.KEYS_ICON}")

@bot.command(aliases=['patch', 'update'])
async def patchnote(ctx: Context):
    await ctx.channel.send(
        "```\n"
        "- Get bullied est (enfin) là !\n"
        "- La commande !!tuto a été mise à jour\n"
        "- Apparition des raretés pour les bullies"
        "- Les nobodies débloquent leur potentiel au lvl 10 ...\n"
        "- Le shop est là."
        "- Apparition des items"
        "- Ouverture des ruines"
        "- Mise à jour du système de combat"
        "```"
    )

@bot.command(aliases=['lb', 'leader'])
async def leaderboard(ctx: Context):
    async with database.new_session() as session:
        lb = Embed(title="Leaderbord Donjon", description=await donjon.str_leaderboard_donjon(session))
        await ctx.channel.send(embed=lb)
    
@bot.command(aliases=['infdung'])
async def infos_dungeon(ctx: Context):
    await ctx.channel.send(
        "```\n"
        "Your bullies do not heal between fights\n"
        "- The first player to defeat the lvl 10 dungeon will receive a permanent trophy!\n"
        "- Dungeons give more xp ! (if you complete them)\n"
        "- After each season, the leaderboard is reset and the first one receives a permanent trophy\n"
        "```"
    )

@bot.command()
async def commands_list(ctx: Context):
    command_list = ""
    for command in bot.commands:
        if utils.is_admin in command.checks:
        #if command.name.startswith("admin_"):
            continue
        aliases = ", ".join(command.aliases) if command.aliases else "No aliases"
        command_list += f"**{command.name}**: {aliases}\n"
    await ctx.send(f"Available commands:\n{command_list}")

@bot.command(aliases=['shop', 'ps'])
async def print_shop(ctx: Context):
    await shop.print_shop(ctx, bot)

@bot.command(aliases=['ty', 'sayty', 'credits'])
async def say_thanks(ctx: Context):
    await ctx.send("Thanks to everyone who takes part in my creation!")

@bot.command(aliases=['sacrifice', 'kill'])
async def suicide(ctx: Context):
    user = ctx.author
    if user.id in utils.players_in_interaction:
        await ctx.reply(f"You are already in an interaction.")
        return
    
    utils.players_in_interaction.add(user.id)
    try:
        async with database.new_session() as session:
            p = await session.get(Player, user.id)
            if p is None:
                await ctx.reply("Please join the game first !")
                return
            await interact_game.suicide_bully(ctx, user=user, player=p, bot=bot)
            await session.commit()
    finally:
        utils.players_in_interaction.discard(user.id)

    return

@bot.command(aliases=['destroy', 'remove_item'])
async def destroy_item(ctx: Context):
    user = ctx.author
    if user.id in utils.players_in_interaction:
        await ctx.reply(f"You are already in an interaction.")
        return
    
    utils.players_in_interaction.add(user.id)
    try:
        async with database.new_session() as session:
            p = await session.get(Player, user.id)
            if p is None:
                await ctx.reply("Please join the game first !")
                return
            await interact_game.remove_item(ctx, user=user, player=p)
            await session.commit()
    finally:
        utils.players_in_interaction.discard(user.id)

    return
# //////////////////////////////////////////////////////////////////////////////////////////////////////

# //////////////////////////////////////////////////////////////////////////////////////////////////////

#Les tutos : ___________________________________________________________
@bot.command()
async def tuto(ctx: Context):
    await ctx.channel.send(tuto_text.tuto)
@bot.command(aliases=['tuto_b'])
async def tuto_bully(ctx: Context):
    await ctx.channel.send(tuto_text.tuto_bully)
@bot.command(aliases=['tuto_f'])
async def tuto_fight(ctx: Context):
    await ctx.channel.send(tuto_text.tuto_fight)
@bot.command(aliases=['tuto_d', 'tuto_donjon'])
async def tuto_dungeon(ctx: Context):
    await ctx.channel.send(tuto_text.tuto_dungeon)
@bot.command(aliases=['tuto_r', 'tuto_ruine'])
async def tuto_ruin(ctx: Context):
    await ctx.channel.send(tuto_text.tuto_ruin)


# //////////////////////////////////////////////////////////////////////////////////////////////////////

#Les combats : ___________________________________________________________
@bot.command(aliases=['ch', 'fight'])
#@utils.author_is_free
async def challenge(ctx: Context, opponent:discord.Member):
    user_1 = ctx.author
    if user_1.id in utils.players_in_interaction:
        await ctx.reply(f"You are already in an interaction.")
        return
    if opponent.id in utils.players_in_interaction:
        await ctx.channel.send(f"Sorry, but {opponent} is already busy!")
        return

    utils.players_in_interaction.add(user_1.id)
    utils.players_in_interaction.add(opponent.id)
    try:
        async with database.new_session() as session:
            p1 = await session.get(Player, user_1.id)
            p2 = await session.get(Player, opponent.id)
            if p1 is None:
                await ctx.reply("Please join the game first !")
                return
            if p2 is None:
                await ctx.reply(f"{opponent} has not joined the game.")
                return
            await fight_manager.proposition_fight(ctx, user_1, p1, opponent, p2, bot)
            await session.commit()
    finally:
        utils.players_in_interaction.discard(opponent.id)
        utils.players_in_interaction.discard(user_1.id)

    return

@bot.command(aliases=['fch', 'fun_fight'])
async def fun_challenge(ctx: Context, opponent:discord.Member):
    user_1 = ctx.author
    if user_1.id in utils.players_in_interaction:
        await ctx.reply(f"You are already in an interaction.")
        return
    if opponent.id in utils.players_in_interaction:
        await ctx.channel.send(f"Sorry, but {opponent} is already busy!")
        return

    utils.players_in_interaction.add(user_1.id)
    utils.players_in_interaction.add(opponent.id)
    try:
        async with database.new_session() as session:
            p1 = await session.get(Player, user_1.id)
            p2 = await session.get(Player, opponent.id)
            if p1 is None:
                await ctx.reply("Please join the game first !")
                return
            if p2 is None:
                await ctx.reply(f"{opponent} has not joined the game.")
                return
            await fight_manager.proposition_fight(ctx, user_1, p1, opponent, p2, bot, for_fun=True)
    finally:
        utils.players_in_interaction.discard(opponent.id)
        utils.players_in_interaction.discard(user_1.id)

    return

@challenge.error
@fun_challenge.error
async def challenge_error(ctx: Context, error: commands.CommandError):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Error: Missing required argument `{error.param.name}`.")

    
@bot.command(aliases=['dungeon', 'donjon'])
#@utils.author_is_free
async def explore_dungeon(ctx: Context, level:int):
    if(level <= 0) :
        await ctx.channel.send("Dungeon level must be greater than 0.")
        return
    if(level > 50) :
        await ctx.channel.send("Level max is 50.")
        return
    if(level == 50) :
        await ctx.channel.send("The mysterious lvl 50 dungeon seems completly lock ... for now.")
        return
    
    user = ctx.author
    if user.id in utils.players_in_interaction:
        await ctx.reply(f"You are already in an interaction.")
        return

    utils.players_in_interaction.add(user.id)
    try:
        async with database.new_session() as session:
            player = await session.get(Player, user.id)
            if player is None:
                await ctx.reply("Please join the game first !")
                return
            await donjon.Dungeon(ctx, bot, player, level).enter()
            await session.commit()
            print("on a commit les changes du donjon !")
    finally:
        utils.players_in_interaction.discard(user.id)
    
@explore_dungeon.error
async def explore_dungeon_error(ctx: Context, error: commands.CommandError):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Error: Missing required argument `{error.param.name}`. Please provide a dungeon level. Example : dungeon 10")

@bot.command(aliases=['ruin', 'ruine'])
#@utils.author_is_free
async def explore_ruin(ctx: Context, level:int):
    if(level <= 0) :
        await ctx.channel.send("Ruin level must be greater than 0")
        return
    if(level > 50) :
        await ctx.channel.send("50 is the maximum")
        return
    
    user = ctx.author
    if user.id in utils.players_in_interaction:
        await ctx.reply(f"You are already in an interaction.")
        return

    utils.players_in_interaction.add(user.id)
    try:
        async with database.new_session() as session:
            player = await session.get(Player, user.id)
            if player is None:
                await ctx.reply("Please join the game first !")
                return
            try:
                await ruine.Ruin(ctx, bot, player, level).enter()
            except Exception as e :
                print("on est ici : ", e)
                raise e
            await session.commit()
            print("on a commit les changes de la ruin!")
    finally:
        utils.players_in_interaction.discard(user.id)

@explore_ruin.error
async def explore_ruin_error(ctx: Context, error: commands.CommandError):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Error: Missing required argument `{error.param.name}`. Please provide a ruin level. Example : ruin 10")
 
# //////////////////////////////////////////////////////////////////////////////////////////////////////

# Par rapport au club ____________________________
@bot.command(aliases=['print', 'pr', 'bullies'])
async def club(ctx: Context, user:Optional[discord.User |discord.Member] = None):
    if(user is None):
        user = ctx.author
    async with database.new_session() as session:
        player = await session.get(Player, user.id)
        if player is None:
            await ctx.reply("Please join the game first !")
            return
        await interact_game.print_bullies(ctx, player, print_images = True)

@bot.command(aliases=['h'])
#@utils.author_is_free
async def hire(ctx: Context):
    user = ctx.author
    if user.id in utils.players_in_interaction:
        await ctx.reply(f"You are already in an interaction.")
        return

    utils.players_in_interaction.add(user.id)
    try:
        async with database.new_session() as session:
            player = await session.get(Player, ctx.author.id)
            if player is None:
                await ctx.reply("Please join the game first !")
                return
            await interact_game.add_random_bully_to_player(ctx, player, interact_game.generate_name())
            await session.commit()
    finally:
        utils.players_in_interaction.discard(user.id)

@bot.command(aliases=['item', 'items'])
async def show_item(ctx: Context, user:Optional[discord.abc.User] = None):
    if(user is None):
        user = ctx.author
    async with database.new_session() as session:
        player = await session.get(Player, user.id)
        if player is None:
            await ctx.reply("Please join the game first !")
            return
        await interact_game.print_items(ctx, player)

@bot.command()
async def kill_all(ctx: Context):
    user = ctx.author
    async with database.new_session() as session:
        player = await session.get(Player, user.id)
        if player is None:
            await ctx.reply("Please join the game first !")
            return
        for b in player.bullies:
            if isinstance(b, bully.Bully):
                await b.kill()
        await session.commit()
    

# //////////////////////////////////////////////////////////////////////////////////////////////////////


#Command d'admin _____________________________________________________________________________________________________
@bot.command()
@utils.is_admin()
async def admin_give(ctx: Context,user: discord.User, name: str, lvl:int , strength: float, agility: float, lethality: float, viciousness: float, path_image: str = ""):
    # # Création de l'objet Stats
    stats = bully.Stats(strength, agility, lethality, viciousness)
    
    # Création de l'objet Bully
    b = bully.Bully(name=name, rarity= bully.Rarity.NOBODY, stats=stats)
    b.lvl = lvl
    sum_stats = stats.sum_stats()
    b.seed = bully.Seed(stats.strength/sum_stats, stats.agility/sum_stats, stats.lethality/sum_stats, stats.viciousness/sum_stats)
    if path_image != "":
        b.image_file_path=Path(path_image)
    
    async with database.new_session() as session:
        player = await session.get(Player, user.id)
        if player is None:
            await ctx.reply("You can't use any commands if the target didn't join")
            return
        await interact_game.add_bully_to_player(ctx, player, b)
        await session.commit()

    # Message de confirmation
    await ctx.send(f"{user.mention}, vous avez reçu {b.name}")
    

@bot.command(aliases=['new_shop', 'ns'])
@utils.is_admin()
async def admin_new_shop(ctx: Context):
    try:
        await shop.restock_shop()
        await shop.print_shop(ctx, bot)
    except Exception as e:
        print(e)

@bot.command()
@utils.is_admin()
async def admin_open_shop(ctx: Context):
    if ctx.guild is None:
        await ctx.send('This command can only be used in a server, not in a DM.')
        return
    
    shop_servers_id = shop.load_shop_servers()
    server_id = ctx.guild.id
    if server_id not in shop_servers_id:
        shop_servers_id.append(server_id)
        shop.save_shop_server(shop_servers_id)
        await ctx.send(f'Server {ctx.guild.name} has been saved!')
    else:
        await ctx.send(f'Server {ctx.guild.name} is already saved.')


@bot.command()
@utils.is_admin()
#@utils.author_is_free
async def get_item(ctx: Context):
    user = ctx.author
    if user.id in utils.players_in_interaction:
        await ctx.reply(f"You are already in an interaction.")
        return

    utils.players_in_interaction.add(user.id)
    try:
        async with database.new_session() as session:
            player = await session.get(Player, ctx.author.id)
            if player is None:
                await ctx.reply("Please join the game first !")
                return
            try:
                new_item = item.Item(name="Str - x0.5", is_bfr_fight=True, buff_start_self=item.ItemStats(1,0,0,0,pv=4), buff_start_self_mult_lvl=item.Stats(0.5, 0, 0, 0))
                await interact_game.add_item_to_player(ctx, player, new_item)
                await session.commit()
            except Exception as e:
                print("on est la en fait")
                print(e)
    finally:
        utils.players_in_interaction.discard(user.id)

@bot.command()
@utils.is_admin()
async def py_admin(ctx: Context):
    async with database.new_session() as session:
        player = await session.get(Player, ctx.author.id)
        if player is None:
            await ctx.reply("Please join the game first !")
            return
        
        # Donner de l'argent à l'utilisateur
        money.give_money(player, montant=10000)
        await ctx.send(
            f"Vous avez reçu des {money.MONEY_ICON} ! (+{money.PAYDAY_VALUE}{money.MONEY_ICON})\n"
            f"Vous avez {money.get_money_user(player)} {money.MONEY_ICON}"
        )

        # Enregistrer l'heure actuelle comme dernière utilisation de la commande
        await session.commit()
    

# JUSTE POUR LE PBE JUSTE POUR LE PBE
@bot.command()
@utils.is_admin()
#@utils.author_is_free
async def give_lvl(ctx: Context, nombre_lvl : Optional[int] = None ):
    if not ctx.me.display_name.startswith("PBE"):
        return
    
    user = ctx.author
    if user.id in utils.players_in_interaction:
        await ctx.reply(f"You are already in an interaction.")
        return

    utils.players_in_interaction.add(user.id)
    try:
        async with database.new_session() as session:
            player = await session.get(Player, ctx.author.id)
            if player is None:
                await ctx.reply("Please join the game first !")
                return
            nb_level = 1 if nombre_lvl is None else nombre_lvl
            await interact_game.increase_all_lvl(ctx, player, nb_level = nb_level)
            await session.commit()
    finally:
        utils.players_in_interaction.discard(user.id)

bot.run(TOKEN)
#asyncio.run(database.init_models())


