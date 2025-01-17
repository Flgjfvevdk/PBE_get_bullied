
import asyncio
from pathlib import Path
import discord
from fight_manager import TeamFight
from fighting_bully import FightingBully, get_player_team
import interact_game
from utils.database import Base
from typing import List, Dict
from sqlalchemy.orm import Mapped, relationship, mapped_column
from sqlalchemy import String
import bully
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
import json
from discord.ext.commands import Bot, Context
import utils.database as database
from player_info import Player

CHOICE_TIMEOUT = 30

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

    def remove_bully_from_team(self, player_id: int, bully_id: int):
        if player_id in self.teams and bully_id in self.teams[player_id]:
            self.teams[player_id].remove(bully_id)

    async def get_print(self, session: AsyncSession, bot: Bot) -> str:
        arena_info = f"Arena: {self.name}\n"
        for player_id, bully_ids in self.teams.items():
            player = await session.get(Player, player_id)
            if player:
                user:discord.User = await bot.fetch_user(player_id)
                arena_info += f"{user}'s Team:\n"
                bullies = await self.get_team(player_id, session)
                for b in bullies:
                    arena_info += f"{b.get_print(compact_print=True)}\n"
                    
        return arena_info

    async def get_team(self, player_id: int, session) -> List[bully.Bully]:
        bully_ids = self.teams.get(player_id, [])
        if not bully_ids:
            return []  # If no bullies are assigned, return an empty list

        bullies = await session.execute(
            select(bully.Bully).filter(bully.Bully.id.in_(bully_ids))
        )

        return bullies.scalars().all()

    async def get_all_teams(self, session: AsyncSession) -> Dict[int, List[bully.Bully]]:
        all_teams = {}
        for player_id in self.teams.keys():
            team = await self.get_team(player_id, session)
            all_teams[player_id] = team
        return all_teams


class ArenaFight:
    def __init__(self, arena: Arena, session: AsyncSession, bot: Bot, user:discord.abc.User, player: Player):
        self.arena = arena
        self.session = session
        self.bot = bot
        self.user = user
        self.player = player
        self.player_teamfighters: List[FightingBully] = get_player_team(player)
        self.teams: Dict[int, List[bully.Bully]] = {}
        self.beaten_teams: Dict[int, List[bully.Bully]] = {}

    async def setup(self):
        self.teams = await self.arena.get_all_teams(self.session)

    async def enter_hall(self, ctx:Context):
        txt_arena = await self.arena.get_print(self.session, self.bot)
        event = asyncio.Event()
        txt_arena += f"\n{self.user.mention}, voulez-vous entrer dans l'arène ?"
        message = await ctx.channel.send(content=txt_arena, view=interact_game.ViewClickBool(user=self.user, event=event, label="Enter The Arena", emoji="⚔️"))
        try:
            await asyncio.wait_for(event.wait(), timeout=CHOICE_TIMEOUT)
        except asyncio.exceptions.TimeoutError as e:
            await message.delete()
            return
        
        await ctx.send(f"{self.user.mention} has entered the arena!")
        await self.start_fight(ctx)

    async def start_fight(self, ctx:Context):
        while len(self.teams) > 0:
            enemy_player_team = self.teams.popitem()
            enemy_teamfighters:list[FightingBully] = [FightingBully.create_fighting_bully(b) for b in enemy_player_team[1]]
            teamfight = TeamFight(ctx=ctx, user_1=self.user, user_2=None, player_1=self.player, player_2=None, can_swap=True)
            teamfight.setup_teams(team_1=self.player_teamfighters, team_2=enemy_teamfighters)
            player_won = await teamfight.start_teamfight()
            if player_won:
                self.beaten_teams[enemy_player_team[0]] = enemy_player_team[1]
            else:
                await self.end_arena(ctx)
                return
        await self.end_arena(ctx)

    async def end_arena(self, ctx:Context):
        await ctx.send(f"{self.user.mention} has beaten these teams: {self.beaten_teams}")

    def print_team(self, team:List[FightingBully]) -> str:
        txt = ""
        for f in team:
            txt += f"{f.get_print()}\n"
        return txt
## ____________________________________________________________________________________________ ##
async def init_arena(bot_player: Player, arena:Arena, session: AsyncSession):
    default_bully = bully.Bully(name="Atalante, héroïne blessée", rarity= bully.Rarity.SUBLIME, max_pv=4, seed= bully.Seed(0.35, 0.4, 0.2, 0.05))
    default_bully.buff_fight_tag = "LastWhisper"
    default_bully.image_file_path=Path("game_data/bully_images/SUBLIME/2023-06-14-14-14-31-005-1368011394-scale7.00-k_euler_a-DreamShaper_6_BakedV.png")
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




