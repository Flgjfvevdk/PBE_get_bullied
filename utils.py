from pathlib import Path
from discord import User
from functools import wraps
from discord.ext import commands
import json
from dotenv import load_dotenv
import os

load_dotenv()

try:
    with Path("config/admins.txt").open("r") as f:
        ADMIN_LIST = set(int(id.strip()) for id in f.readlines())
except Exception as e:
    print("Exception found parsing admin list !")
    print(e)
    print("Admin commands are disabled !")
    ADMIN_LIST = set()

def is_admin():
    """ Command decorator to check if the message author is an admin.
    """
    async def predicate(ctx: commands.Context):
        return ctx.author.id in ADMIN_LIST
    return commands.check(predicate)


def getenv(name:str) -> str:
    val = os.getenv(name)
    if val is None:
        raise Exception("ENV variable {name} is not set!")
    return val

players_in_interaction: set[int] = set()

def author_is_free(f):
    async def predicate(ctx: commands.Context):
        if ctx.author.id in players_in_interaction:
            await ctx.reply("You are already in an action.")
            return
        players_in_interaction.add(ctx.author.id)
        try:
            await f(ctx)
        finally:
            players_in_interaction.discard(ctx.author.id)
        return
    return predicate