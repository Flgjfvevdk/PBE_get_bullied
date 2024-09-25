from pathlib import Path
from discord import User
from functools import wraps
from discord.ext import commands
from .locks import PlayerLock
import os
import json

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

def author_is_free(f):
    async def predicate(ctx: commands.Context):
        plock = PlayerLock(ctx.author.id)
        if not plock.check():
            await ctx.reply("You are already in an action.")
            return
        with plock:
            await f(ctx)
    return predicate

def pbe_only():
    async def predicate(ctx: commands.Context):
        return os.getenv("TESTING") or ctx.me.display_name.startswith("PBE")
    return commands.check(predicate)
        

            