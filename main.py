# bot.py
import os
from typing import Optional
from pathlib import Path
import discord

import utils
import interact_game
import fight_manager
import donjon
import ruine
import money
import shop
import bully
import item
import database
from player_info import Player

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

import asyncio

from discord.ext.commands import Bot, Context, CommandNotFound

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
    asyncio.create_task(shop.restock_shop_automatic())
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
@utils.author_is_free
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
        
        await ctx.send(f"Vous avez {money.get_money_user(player)} {money.MONEY_ICON}")

@bot.command(aliases=['patch', 'update'])
async def patchnote(ctx: Context):
    await ctx.channel.send(
        "```\n"
        "- leaderbord for dungeon ! Become the greatest coach by conquering the most powerful dungeons\n"
        "- Fun fight are live ! ($$fun_challenge @username)\n"
        "- new command : $$infos_dungeon\n"
        "```"
    )

@bot.command(aliases=['lb', 'leader'])
async def leaderboard(ctx: Context):
    await ctx.channel.send(await donjon.str_leaderboard_donjon(ctx, bot))
    
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


# //////////////////////////////////////////////////////////////////////////////////////////////////////


# //////////////////////////////////////////////////////////////////////////////////////////////////////

#Les combats : ___________________________________________________________
@bot.command(aliases=['ch'])
#@utils.author_is_free
async def challenge(ctx: Context, user_2:discord.Member):
    user_1 = ctx.author
    if user_1.id in utils.players_in_interaction:
        await ctx.reply(f"You are already in an interaction.")
    if user_2.id in utils.players_in_interaction:
        await ctx.channel.send(f"Sorry, but {user_2} is already busy!")

    utils.players_in_interaction.add(user_1.id)
    utils.players_in_interaction.add(user_2.id)
    try:
        async with database.new_session() as session:
            p1 = await session.get(Player, user_1.id)
            p2 = await session.get(Player, user_2.id)
            if p1 is None:
                await ctx.reply("Please join the game first !")
                return
            if p2 is None:
                await ctx.reply(f"{user_2} has not joined the game.")
                return
            await fight_manager.proposition_fight(ctx, user_1, p1, user_2, p2, bot)
            await session.commit()
    finally:
        utils.players_in_interaction.discard(user_2.id)
        utils.players_in_interaction.discard(user_1.id)

    return

@bot.command(aliases=['fch'])
async def fun_challenge(ctx: Context, user_2:discord.Member):
    user_1 = ctx.author
    if user_1.id in utils.players_in_interaction:
        await ctx.reply(f"You are already in an interaction.")
    if user_2.id in utils.players_in_interaction:
        await ctx.channel.send(f"Sorry, but {user_2} is already busy!")

    utils.players_in_interaction.add(user_1.id)
    utils.players_in_interaction.add(user_2.id)
    try:
        async with database.new_session() as session:
            p1 = await session.get(Player, user_1.id)
            p2 = await session.get(Player, user_2.id)
            if p1 is None:
                await ctx.reply("Please join the game first !")
                return
            if p2 is None:
                await ctx.reply(f"{user_2} has not joined the game.")
                return
            await fight_manager.proposition_fight(ctx, user_1, p1, user_2, p2, bot, for_fun=True)
    finally:
        utils.players_in_interaction.discard(user_2.id)
        utils.players_in_interaction.discard(user_1.id)

    return

@bot.command(aliases=['dungeon', 'donjon'])
#@utils.author_is_free
async def explore_dungeon(ctx: Context, level:int):
    if(level <= 0) :
        await ctx.channel.send("Dungeon level must be greater than 0.")
        return
    if(level > 10) :
        await ctx.channel.send("Pour l'instant c'est limité jusqu'au lvl 10 le temps d'équilibrer.")
        return
    
    user = ctx.author
    if user.id in utils.players_in_interaction:
        await ctx.reply(f"You are already in an interaction.")

    utils.players_in_interaction.add(user.id)
    try:
        async with database.new_session() as session:
            player = await session.get(Player, user.id)
            if player is None:
                await ctx.reply("Please join the game first !")
                return
            await donjon.enter_the_dungeon(ctx, player, level, bot)
            await session.commit()
    finally:
        utils.players_in_interaction.discard(user.id)
    return

@bot.command(aliases=['ruin', 'ruine'])
#@utils.author_is_free
async def explore_ruin(ctx: Context, level:int):
    if(level <= 0) :
        await ctx.channel.send("Ruin level must be greater than 0")
        return
    if(level > 100) :
        await ctx.channel.send("Pour l'instant c'est limité jusqu'au lvl 100 le temps d'équilibrer.")
        return
    
    user = ctx.author
    if user.id in utils.players_in_interaction:
        await ctx.reply(f"You are already in an interaction.")

    utils.players_in_interaction.add(user.id)
    try:
    
        async with database.new_session() as session:
            player = await session.get(Player, user.id)
            if player is None:
                await ctx.reply("Please join the game first !")
                return
            await ruine.enter_the_ruin(ctx, user, player, level, bot)
            await session.commit()
    finally:
        utils.players_in_interaction.discard(user.id)
    return
# //////////////////////////////////////////////////////////////////////////////////////////////////////

# Par rapport au club ____________________________
@bot.command(aliases=['print', 'pr'])
async def club(ctx: Context, user:Optional[discord.abc.User] = None):
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
    

# //////////////////////////////////////////////////////////////////////////////////////////////////////


#Command d'admin _____________________________________________________________________________________________________
@bot.command()
@utils.is_admin()
#@utils.author_is_free
async def admin_give(ctx: Context):
    user = ctx.author
    if user.id in utils.players_in_interaction:
        await ctx.reply(f"You are already in an interaction.")

    utils.players_in_interaction.add(user.id)
    try:
        async with database.new_session() as session:
            
            player = await session.get(Player, ctx.author.id)
            if player is None:
                await ctx.reply("You can't use any commands if the target doesn't have an account")
                return
            await interact_game.add_bully_custom(ctx, player, ["Balez", "EZ"], [99,99,99,99], bully.Rarity.DEVASTATOR)
            await session.commit()
    finally:
        utils.players_in_interaction.discard(user.id)

@bot.command(aliases=['new_shop', 'ns'])
@utils.is_admin()
async def admin_new_shop(ctx: Context):
    try:
        shop.restock_shop()
        await shop.print_shop(ctx, bot)
    except Exception as e:
        print(e)


@bot.command()
@utils.is_admin()
#@utils.author_is_free
async def get_item(ctx: Context):
    user = ctx.author
    if user.id in utils.players_in_interaction:
        await ctx.reply(f"You are already in an interaction.")

    utils.players_in_interaction.add(user.id)
    try:
        async with database.new_session() as session:
            player = await session.get(Player, ctx.author.id)
            if player is None:
                await ctx.reply("Please join the game first !")
                return
            try:
                new_item = item.Item(name="Str - x0.5", is_bfr_fight=True, buff_start_self=item.ItemStats(1,0,0,0,pv=4), buff_start_self_mult_lvl=item.Seed(0.5, 0, 0, 0))
                await interact_game.add_item_to_player(ctx, player, new_item)
                await session.commit()
            except Exception as e:
                print("on est la en fait")
                print(e)
    finally:
        utils.players_in_interaction.discard(user.id)

# JUSTE POUR LE PBE JUSTE POUR LE PBE
@bot.command()
@utils.is_admin()
#@utils.author_is_free
async def give_lvl(ctx: Context):
    if not ctx.me.display_name.startswith("PBE"):
        return
    
    user = ctx.author
    if user.id in utils.players_in_interaction:
        await ctx.reply(f"You are already in an interaction.")

    utils.players_in_interaction.add(user.id)
    try:

        async with database.new_session() as session:
            player = await session.get(Player, ctx.author.id)
            if player is None:
                await ctx.reply("Please join the game first !")
                return
            await interact_game.increase_all_lvl(ctx, player)
            await session.commit()
    finally:
        utils.players_in_interaction.discard(user.id)

bot.run(TOKEN)



