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
# import item
import database
from player_info import Player
import tuto_text
import lootbox
import consommable

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import configure_mappers

import asyncio

from discord.ext.commands import Bot, Context, CommandNotFound
from discord import Embed
import reserve

TOKEN = utils.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

TEXT_JOIN_THE_GAME:str = "Please join the game first ! (!!join)"

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
            await ctx.reply(TEXT_JOIN_THE_GAME)
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
            await ctx.reply(TEXT_JOIN_THE_GAME)
            return
        
        await ctx.send(f"You have {money.get_money_user(player)} {money.MONEY_ICON}")

@bot.command(aliases=['jeton', 'jetons', 'token', 'tokens', 'key', 'keys'])
async def print_key(ctx: Context):
    async with database.new_session() as session:
        player = await session.get(Player, ctx.author.id)
        if player is None:
            await ctx.reply(TEXT_JOIN_THE_GAME)
            return
        
        await ctx.send(f"You have {keys.get_keys_user(player)} {keys.KEYS_ICON}")

@bot.command(aliases=['patch', 'update'])
async def patchnote(ctx: Context):
    await ctx.channel.send(tuto_text.patchnote)

@bot.command(aliases=['leader', 'rank'])
async def leaderboard(ctx: Context):
    async with database.new_session() as session:
        lb = Embed(title="Leaderbord Donjon", description=await donjon.str_leaderboard_donjon(session))
        await ctx.channel.send(embed=lb)
    
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

@bot.command(aliases=['lootbox', 'lb'])
async def buy_lootbox(ctx: Context):
    user = ctx.author
    if user.id in utils.players_in_interaction:
        await ctx.reply(f"You are already in an interaction.")
        return
    await lootbox.shop_lootbox(ctx, user=user)

@bot.command(aliases=['ty', 'sayty', 'credits'])
async def say_thanks(ctx: Context):
    await ctx.send("Thanks to everyone who takes part in this game!")

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
                await ctx.reply(TEXT_JOIN_THE_GAME)
                return
            await interact_game.suicide_bully(ctx, user=user, player=p, bot=bot)
            await session.commit()
    finally:
        utils.players_in_interaction.discard(user.id)

    return

# @bot.command(aliases=['destroy', 'remove_item'])
# async def destroy_item(ctx: Context):
#     user = ctx.author
#     if user.id in utils.players_in_interaction:
#         await ctx.reply(f"You are already in an interaction.")
#         return
    
#     utils.players_in_interaction.add(user.id)
#     try:
#         async with database.new_session() as session:
#             p = await session.get(Player, user.id)
#             if p is None:
#                 await ctx.reply(TEXT_JOIN_THE_GAME)
#                 return
#             await interact_game.remove_item(ctx, user=user, player=p)
#             await session.commit()
#     finally:
#         utils.players_in_interaction.discard(user.id)

#     return
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
@bot.command(aliases=['tuto_s'])
async def tuto_shop(ctx: Context):
    await ctx.channel.send(tuto_text.tuto_shop)
@bot.command(aliases=['tuto_lb', 'tuto_l'])
async def tuto_lootbox(ctx: Context):
    await ctx.channel.send(tuto_text.tuto_lootbox)

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
                await ctx.reply(TEXT_JOIN_THE_GAME)
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
                await ctx.reply(TEXT_JOIN_THE_GAME)
                return
            if p2 is None:
                await ctx.reply(f"{opponent} has not joined the game.")
                return
            await fight_manager.proposition_fight(ctx, user_1, p1, opponent, p2, bot, for_fun=True)
    finally:
        utils.players_in_interaction.discard(opponent.id)
        utils.players_in_interaction.discard(user_1.id)

    return

@bot.command(aliases=['tch', 'teamfight', 'team_fight'])
async def team_challenge(ctx: Context, opponent:discord.Member):
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
                await ctx.reply(TEXT_JOIN_THE_GAME)
                return
            if p2 is None:
                await ctx.reply(f"{opponent} has not joined the game.")
                return
            await fight_manager.manager_start_team_fight(ctx, user_1, p1, opponent, p2, bot)
    finally:
        utils.players_in_interaction.discard(opponent.id)
        utils.players_in_interaction.discard(user_1.id)

    return


@challenge.error
@fun_challenge.error
async def challenge_error(ctx: Context, error: commands.CommandError):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Error: Missing required argument `{error.param.name}`.")

    
@bot.command(aliases=['dungeon', 'donjon', 'dj', 'dg'])
#@utils.author_is_free
async def explore_dungeon(ctx: Context, level:int):
    if(level <= 0) :
        await ctx.channel.send("Dungeon level must be greater than 0.")
        return
    if(level > 50) :
        await ctx.channel.send("Level max is 50.")
        return
    # if(level == 50) :
    #     await ctx.channel.send("The mysterious lvl 50 dungeon seems completly lock ... for now.")
    #     return
    
    user = ctx.author
    if user.id in utils.players_in_interaction:
        await ctx.reply(f"You are already in an interaction.")
        return

    utils.players_in_interaction.add(user.id)
    try:
        async with database.new_session() as session:
            player = await session.get(Player, user.id)
            if player is None:
                await ctx.reply(TEXT_JOIN_THE_GAME)
                return
            try :
                await donjon.Dungeon(ctx, bot, player, level).enter()
            except Exception as e:
                print(e)
                raise e
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
    if(level >= 50) :
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
                await ctx.reply(TEXT_JOIN_THE_GAME)
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
@bot.command(aliases=['print', 'pr', 'bullies', 'team'])
async def club(ctx: Context, user:Optional[discord.User |discord.Member] = None):
    if(user is None):
        user = ctx.author
    async with database.new_session() as session:
        player = await session.get(Player, user.id)
        if player is None:
            await ctx.reply(TEXT_JOIN_THE_GAME)
            return
        await interact_game.print_bullies(ctx, player, print_images = True)

@bot.command(aliases=['reserve'])
async def print_reserve(ctx: Context, user:Optional[discord.User |discord.Member] = None):
    if(user is None):
        user = ctx.author
    async with database.new_session() as session:
        player = await session.get(Player, user.id)
        if player is None:
            await ctx.reply(TEXT_JOIN_THE_GAME)
            return
        await reserve.print_reserve(ctx, user, player, bot, session=session, print_images = True)
        

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
                await ctx.reply(TEXT_JOIN_THE_GAME)
                return
            await interact_game.add_random_bully_to_player(ctx, player, interact_game.generate_name())
            await session.commit()
    finally:
        utils.players_in_interaction.discard(user.id)

# @bot.command(aliases=['item', 'items'])
# async def show_item(ctx: Context, user:Optional[discord.abc.User] = None):
#     if(user is None):
#         user = ctx.author
#     async with database.new_session() as session:
#         player = await session.get(Player, user.id)
#         if player is None:
#             await ctx.reply(TEXT_JOIN_THE_GAME)
#             return
#         await interact_game.print_items(ctx, player)

@bot.command()
async def kill_all(ctx: Context):
    user = ctx.author
    async with database.new_session() as session:
        player = await session.get(Player, user.id)
        if player is None:
            await ctx.reply(TEXT_JOIN_THE_GAME)
            return
        for b in player.bullies:
            if isinstance(b, bully.Bully):
                await b.kill()
        await session.commit()
    

@bot.command(aliases=['use_c', 'use_conso', 'use_consommables'])
async def use_consommable(ctx: Context):
    user = ctx.author
    if user.id in utils.players_in_interaction:
        await ctx.reply(f"You are already in an interaction.")
        return

    utils.players_in_interaction.add(user.id)
    try:
        async with database.new_session() as session:
            player = await session.get(Player, ctx.author.id)
            if player is None:
                await ctx.reply(TEXT_JOIN_THE_GAME)
                return
            await consommable.use_consommable(ctx=ctx, user=user, player=player, session=session, bot=bot)
            await session.commit()
    finally:
        utils.players_in_interaction.discard(user.id)

@bot.command(aliases=['show_consommable', 'consommable', 'print_consommable', 'consommables', 'print_consommables', 'print_c'])
async def show_consommables(ctx: Context):
    user = ctx.author

    async with database.new_session() as session:
        player = await session.get(Player, ctx.author.id)
        if player is None:
            await ctx.reply(TEXT_JOIN_THE_GAME)
            return
        await ctx.channel.send(consommable.str_consommables(player=player).str())
        # await consommable.print_consommables(ctx, player)

# //////////////////////////////////////////////////////////////////////////////////////////////////////


#Command d'admin _____________________________________________________________________________________________________
@bot.command()
@utils.is_admin()
async def admin_give(ctx: Context,user: discord.User, name: str, lvl:int, rarity:str , strength: float, agility: float, lethality: float, viciousness: float, path_image: str = "", seed_str:str = "", max_pv:int|None = None):
    # # Création de l'objet Stats
    stats = bully.Stats(strength, agility, lethality, viciousness)
    
    # Création de l'objet Bully
    b = bully.Bully(name=name, rarity= bully.Rarity[rarity], stats=stats)
    b.lvl = lvl
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

    if max_pv is not None:
        b.max_pv = max_pv
    
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


# @bot.command()
# @utils.is_admin()
# async def get_item(ctx: Context):
#     user = ctx.author
#     if user.id in utils.players_in_interaction:
#         await ctx.reply(f"You are already in an interaction.")
#         return

#     utils.players_in_interaction.add(user.id)
#     try:
#         async with database.new_session() as session:
#             player = await session.get(Player, ctx.author.id)
#             if player is None:
#                 await ctx.reply(TEXT_JOIN_THE_GAME)
#                 return
#             try:
#                 new_item = item.Item(name="Str - x0.5", is_bfr_fight=True, buff_start_self=item.ItemStats(1,0,0,0,pv=4), buff_start_self_mult_lvl=item.Stats(0.5, 0, 0, 0))
#                 await interact_game.add_item_to_player(ctx, player, new_item)
#                 await session.commit()
#             except Exception as e:
#                 print("on est la en fait")
#                 print(e)
#     finally:
#         utils.players_in_interaction.discard(user.id)

@bot.command()
@utils.is_admin()
async def py_admin(ctx: Context):
    async with database.new_session() as session:
        player = await session.get(Player, ctx.author.id)
        if player is None:
            await ctx.reply(TEXT_JOIN_THE_GAME)
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
                await ctx.reply(TEXT_JOIN_THE_GAME)
                return
            nb_level = 1 if nombre_lvl is None else nombre_lvl
            await interact_game.increase_all_lvl(ctx, player, nb_level = nb_level)
            await session.commit()
    finally:
        utils.players_in_interaction.discard(user.id)


@bot.command()
@utils.is_admin()
async def add_c(ctx: Context):
    user = ctx.author
    if user.id in utils.players_in_interaction:
        await ctx.reply(f"You are already in an interaction.")
        return

    async with database.new_session() as session:
        player = await session.get(Player, ctx.author.id)
        if player is None:
            await ctx.reply(TEXT_JOIN_THE_GAME)
            return
        c = consommable.AlimentEnum.Gigot.new_conso(2)
        print(c.get_print())
        player.consommables.append(c)
        print("player.consommables : ", player.consommables[0].get_print())
        await session.commit()

@bot.command()
@utils.is_admin()
async def del_c(ctx: Context):
    user = ctx.author
    if user.id in utils.players_in_interaction:
        await ctx.reply(f"You are already in an interaction.")
        return

    async with database.new_session() as session:
        player = await session.get(Player, ctx.author.id)
        if player is None:
            await ctx.reply(TEXT_JOIN_THE_GAME)
            return
        player.consommables = []
        await session.commit()

@bot.command()
@utils.is_admin()
async def bully_maj(ctx:Context):
    async with database.new_session() as session:
        result = await session.execute(select(bully.Bully))  # Remplace Bully par ta classe qui mappe la table BULLY
        bullies = result.scalars().all()
        for b in bullies:
            difference_points = bully.nb_points_tot_rarity(b.lvl, b.rarity) - b.stats.sum_stats()
            print(f"{b.name}- diff:{difference_points}")
            nb_points:int = round(b.lvl * (b.lvl + 1) / 2)
            val = difference_points/nb_points
            b.increase_stat_with_seed(nb_points=nb_points, valeur=val, talkative = False)
        await session.commit() 

if __name__ == "__main__":
    if os.getenv("TESTING"):
        asyncio.run(database.init_models())
    bot.run(TOKEN)
