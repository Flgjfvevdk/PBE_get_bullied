from pathlib import Path
from discord import User
from functools import wraps
from discord.ext import commands
import json

def get_player_path(user_id: int) -> Path:
    path_player_data = Path("game_data/player_data")
    user_player_path = path_player_data / str(user_id)
    return user_player_path

def _user_has_joined(user_id: int):
    path = get_player_path(user_id)
    return path.exists()

def has_joined():
    """ Command decorator to check if the message author has joined the game.
    """
    async def predicate(ctx: commands.Context):
        return _user_has_joined(ctx.author.id)
    return commands.check(predicate)

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