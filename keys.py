from pathlib import Path
from bully import Bully
import bully
import interact_game
import money
import donjon
import utils
import database
from player_info import Player


import os
import random 
import json
import asyncio

from typing import Optional, Dict
from typing import List

from sqlalchemy.orm import exc

import discord
from discord.ext import tasks
from discord.ext.commands import Context, Bot

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# Var payday
KEYS_MAX = 15
NB_KEYS_RESTOCK = 1
GET_KEYS_COOLDOWN = 10 * 60

KEYS_ICON = "🔑"

async def init_keys_restock():
    restock_keys_loop.start()

async def restock_keys() -> None:
    async with database.new_session() as session:
        joueurs = (await session.scalars(select(Player))).all()
        
        for j in joueurs:
            j.keys = min(j.keys + NB_KEYS_RESTOCK, KEYS_MAX)

        await session.commit()

@tasks.loop(seconds=GET_KEYS_COOLDOWN)
async def restock_keys_loop():
    await restock_keys()


def get_keys_user(player: Player) -> int:
    return player.keys