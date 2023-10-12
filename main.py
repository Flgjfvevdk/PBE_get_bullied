# bot.py
import os
import discord

import interract_game
import fight_manager
import donjon
import ruine
import money
import shop
import bully
import item


import asyncio

from discord.ext import commands

#Les 2 lignes en dessous permettent de lire le token qui est noté dans .env
from dotenv import load_dotenv
load_dotenv()


TOKEN = os.getenv('DISCORD_TOKEN')
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix = "!!", intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} is now running !')
    asyncio.create_task(shop.restock_shop_automatic())
    print("on est bien là")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return


# Command général ____________________________________________________________________________________
@bot.command()
async def join(ctx):
    path_player_data = "game_data/player_data"
    id = ctx.author.id
    user_player_path = path_player_data + "/" + str(id)
    await interract_game.join_game(ctx, user_player_path)

@bot.command(aliases=['py', 'pay'])
async def payday(ctx):
    # Vérifier si l'utilisateur a déjà fait la commande récemment
    cooldown_restant = await money.cooldown_restant_pay(ctx.author.id)
    if cooldown_restant > 0:
        await ctx.send(f"Vous devez attendre encore {money.format_temps(round(cooldown_restant))} avant de pouvoir utiliser cette commande à nouveau.")
        return

    # Donner de l'argent à l'utilisateur
    money.give_money(ctx.author.id, montant= money.payday_value)
    await ctx.send(f"Vous avez reçu des {money.icon_money} ! (+{money.payday_value}{money.icon_money})\nVous avez {money.get_money_user(ctx.author.id)} {money.icon_money}")

    # Enregistrer l'heure actuelle comme dernière utilisation de la commande
    money.enregistrer_cooldown_pay(ctx.author.id)

@bot.command(aliases=['money'])
async def bank(ctx):
    await ctx.send(f"Vous avez {money.get_money_user(ctx.author.id)} {money.icon_money}")

@bot.command(aliases=['patch', 'update'])
async def patchnote(ctx):
    await ctx.channel.send("```\n- leaderbord for dungeon ! Become the greatest coach by conquering the most powerful dungeons\n- Fun fight are live ! ($$fun_challenge @username)\n- new command : $$infos_dungeon ```")

@bot.command(aliases=['lb', 'leader'])
async def leaderboard(ctx):
    await ctx.channel.send(await donjon.str_leaderboard_donjon(ctx, bot))
    
@bot.command(aliases=['infdung'])
async def infos_dungeon(ctx):
    await ctx.channel.send("```\nYour bullies do not heal between fights\n- The first player to defeat the lvl 10 dungeon will receive a permanent trophy!\n- Dungeons give more xp ! (if you complete them)\n- After each season, the leaderboard is reset and the first one receives a permanent trophy```")

@bot.command()
async def commands_list(ctx):
    command_list = ""
    for command in bot.commands:
        if not command.name.startswith("admin_"):
            aliases = ", ".join(command.aliases) if command.aliases else "No aliases"
            command_list += f"**{command.name}**: {aliases}\n"
    await ctx.send(f"Available commands:\n{command_list}")

@bot.command(aliases=['shop', 'ps'])
async def print_shop(ctx):
    await shop.print_shop(ctx, bot)

@bot.command(aliases=['ty', 'sayty', 'credits'])
async def say_thanks(ctx):
    await ctx.send("Thanks to everyone who take part in my creation!")


# //////////////////////////////////////////////////////////////////////////////////////////////////////


# //////////////////////////////////////////////////////////////////////////////////////////////////////

#Les combats : ___________________________________________________________
@bot.command(aliases=['ch'])
async def challenge(ctx, user:discord.Member):
    user_1 = ctx.author
    if(ctx.author.id in donjon.ID_joueur_en_donjon):
        await ctx.channel.send("You can't, you are in a dungeon")
        return
    await fight_manager.proposition_fight(ctx, user_1, user, bot)
    return

@bot.command(aliases=['fch'])
async def fun_challenge(ctx, user:discord.Member):
    user_1 = ctx.author
    if(ctx.author.id in donjon.ID_joueur_en_donjon):
        await ctx.channel.send("You can't, you are in a dungeon")
        return
    await fight_manager.proposition_fight(ctx, user_1, user, bot, for_fun=True)
    return

@bot.command(aliases=['dungeon', 'donjon'])
async def explore_dungeon(ctx, level:int):
    user = ctx.author
    if(ctx.author.id in donjon.ID_joueur_en_donjon):
        await ctx.channel.send("You can't, you are in a dungeon")
        return
    if(level <= 0) :
        await ctx.channel.send("Dungeon level must be greater than 0")
        return
    if(level > 10) :
        await ctx.channel.send("Pour l'instant c'est limité jusqu'au lvl 10 le temps d'équilibrer.")
        return
    await donjon.enter_the_dungeon(ctx, user, level, bot)
    return

@bot.command(aliases=['ruin', 'ruine'])
async def explore_ruin(ctx, level:int):
    user = ctx.author
    if(ctx.author.id in donjon.ID_joueur_en_donjon):
        await ctx.channel.send("You can't, you are in a dungeon")
        return
    if(level <= 0) :
        await ctx.channel.send("Ruin level must be greater than 0")
        return
    if(level > 100) :
        await ctx.channel.send("Pour l'instant c'est limité jusqu'au lvl 100 le temps d'équilibrer.")
        return
    try :
        await ruine.enter_the_ruin(ctx, user, level, bot)
    except Exception as e:
        print(e)
    return
# //////////////////////////////////////////////////////////////////////////////////////////////////////

# Par rapport au club ____________________________
@bot.command(aliases=['print', 'pr'])
async def club(ctx, user:discord.Member = None):
    if(user is None):
        user = ctx.author
    path_player_data = "game_data/player_data"
    id = user.id
    user_player_path = path_player_data + "/" + str(id)
    if(not os.path.exists(user_player_path)):
        await ctx.channel.send("You can't use any commands until you have joined")
        return
    try:
        await interract_game.print_bullies(ctx, user_player_path, print_images = True)
    except Exception as e:
        print(e)

@bot.command(aliases=['h'])
async def hire(ctx):
    if(ctx.author.id in donjon.ID_joueur_en_donjon):
        await ctx.channel.send("You can't, you are in a dungeon")
        return
    path_player_data = "game_data/player_data"
    id = ctx.author.id
    user_player_path = path_player_data + "/" + str(id)
    if(not os.path.exists(user_player_path)):
        await ctx.channel.send("You can't use any commands until you have joined")
        return
    await interract_game.add_random_bully_to_player(ctx, id, interract_game.generate_name())

@bot.command(aliases=['item', 'items'])
async def show_item(ctx, user:discord.Member = None):
    if(user is None):
        user = ctx.author
    path_player_data = "game_data/player_data"
    id = user.id
    user_player_path = path_player_data + "/" + str(id)
    if(not os.path.exists(user_player_path)):
        await ctx.channel.send("You can't use any commands until you have joined")
        return
    try:
        await interract_game.print_items(ctx, user_player_path)
    except Exception as e:
        print(e)

# //////////////////////////////////////////////////////////////////////////////////////////////////////


#Command d'admin _____________________________________________________________________________________________________
@bot.command()
async def admin_give(ctx):
    if(ctx.author.id == ***REMOVED***):
        path_player_data = "game_data/player_data"
        id = ***REMOVED*** #Mon id
        #id = 1113183903319068692 #id du bot
        user_player_path = path_player_data + "/" + str(id)
        if(not os.path.exists(user_player_path)):
            await ctx.channel.send("You can't use any commands if the target doesn't have an account")
            return
        await interract_game.add_bully_custom(ctx, user_player_path, ["Balez", "EZ"], [99,99,99,99], bully.Rarity.DEVASTATOR)

@bot.command()
async def admin_bot_join(ctx):
    if(ctx.author.id == ***REMOVED***):
        path_player_data = "game_data/player_data"
        id = 1113183903319068692 #id du bot
        user_player_path = path_player_data + "/" + str(id)
        await interract_game.join_game(ctx, user_player_path)
        

@bot.command(aliases=['new_shop', 'ns'])
async def admin_new_shop(ctx):
    if(ctx.author.id == ***REMOVED***):
        await shop.restock_shop()
        try:
            await shop.print_shop(ctx, bot)
        except Exception as e:
            print(e)
    return


@bot.command()
async def get_item(ctx):
    if(ctx.author.id == ***REMOVED***):
        try :
            new_item = item.Item(name="Str - x0.5", is_bfr_fight= True, buff_self_start=[4,1,0,0,0], buff_self_start_multiplicatif_lvl=[0.5, 0, 0, 0])
            await interract_game.add_item_to_player(ctx= ctx, user_id= ctx.author.id, i= new_item)
        except Exception as e:
            print("on est la en fait")
            print(e)


# JUSTE POUR LE PBE JUSTE POUR LE PBE
@bot.command()
async def give_lvl(ctx):
    if(TOKEN != ***REMOVED***):
        return
    else :
        path_player_data = "game_data/player_data"
        user_player_path = path_player_data + "/" + str(ctx.author.id)
        print("ici")
        await interract_game.increase_all_lvl(ctx, player_path=user_player_path)
#


bot.run(TOKEN)



