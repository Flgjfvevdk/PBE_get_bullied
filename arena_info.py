
from utils.database import Base
from typing import List, Dict
from sqlalchemy.orm import Mapped, relationship, mapped_column
from sqlalchemy import Column, Integer, ForeignKey, String
import bully
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
import json
from discord.ext.commands import Bot
import utils.database as database
from player_info import Player

class Arena(Base):
    __tablename__ = "arena"

    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    teams: Mapped[Dict[int, List[int]]] = mapped_column(JSON, default=dict)

    def __init__(self, name: str):
        self.name = name

    def add_empty_team(self, player_id: int):
        if player_id not in self.teams:
            self.teams[player_id] = []
            flag_modified(self, "teams") 

    def add_bully_to_team(self, player_id: int, bully_id: int):
        if player_id in self.teams:
            self.teams[player_id].append(bully_id)
            flag_modified(self, "teams") 

    async def get_team(self, player_id: int, session) -> List[bully.Bully]:
        # Retrieve the bully IDs for the given player
        bully_ids = self.teams.get(player_id, [])
        if not bully_ids:
            return []  # If no bullies are assigned, return an empty list

        # Use async query to get the bullies associated with the player
        bullies = await session.execute(
            select(bully.Bully).filter(bully.Bully.id.in_(bully_ids))
        )

        # Return the list of bullies
        return bullies.scalars().all()

    def remove_bully_from_team(self, player_id: int, bully_id: int):
        if player_id in self.teams and bully_id in self.teams[player_id]:
            self.teams[player_id].remove(bully_id)

async def init_arena(bot_player: Player, arena:Arena, session: AsyncSession):
    default_bully = bully.Bully(name="Atalante, héroïne blessée", rarity= bully.Rarity.SUBLIME, max_pv=4, seed= bully.Seed(0.35, 0.4, 0.2, 0.05))
    default_bully.buff_fight_tag = "LastWhisper"
    for _ in range(5):
        default_bully.level_up_one()
    bot_player.bullies.append(default_bully)
    await session.flush() 
    arena.add_empty_team(bot_player.id)
    arena.add_bully_to_team(bot_player.id, default_bully.id)


async def update_arenas(bot : Bot):
    async with database.new_session() as session:
        try:
            with open('discord_servers.json', 'r') as file:
                server_ids = json.load(file)
        except FileNotFoundError:
            print("The 'discord_servers.json' file was not found.")
            return

        for server_id in server_ids:
            arena = await session.get(Arena, server_id)
            server = bot.get_guild(server_id)

            if arena is None and server is not None:
                new_arena = Arena(name=server.name)
                new_arena.id = server_id

                session.add(new_arena)
                await session.flush() 
                if bot.user is not None:    
                    bot_player = await session.get(Player, bot.user.id)
                    if bot_player is not None:
                        await init_arena(bot_player, new_arena, session)
                print(f"Created a new arena for server {server_id}")

        await session.commit()




