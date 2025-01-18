
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

    #/!\ when save, the json convert the keys to string. Mais quand on lui donne des valeurs on utilise souvent des ids et donc des int 
    teams_ids: Mapped[Dict] = mapped_column(JSON, default=dict) 

    def __init__(self, name: str):
        self.name = name

    def add_empty_team(self, player_id: int):
        if player_id not in self.teams_ids:
            self.teams_ids[player_id] = []
            flag_modified(self, "teams_ids") 

    def add_bully_to_team(self, player_id: int, bully_id: int):
        if player_id in self.teams_ids:
            self.teams_ids[player_id].append(bully_id)
            flag_modified(self, "teams_ids") 

    def remove_bully_from_team(self, player_id: int, bully_id: int):
        if player_id in self.teams_ids and bully_id in self.teams_ids[player_id]:
            self.teams_ids[player_id].remove(bully_id)

    async def get_print(self, session: AsyncSession, bot: Bot) -> str:
        arena_info = f"Arena: {self.name}\n"
        for player_id, bully_ids in self.teams_ids.items():
            player = await session.get(Player, player_id)
            if player:
                user:discord.User = await bot.fetch_user(player_id)
                arena_info += f"\n________________________________________\n{user}'s Team:\n"
                bullies = await self.get_team(player_id, session)
                for b in bullies:
                    arena_info += f"{b.get_print(compact_print=True)}\n"
                    
        return arena_info

    async def get_team(self, player_id: int, session) -> List[bully.Bully]:
        bully_ids = self.teams_ids.get(player_id, [])
        if not bully_ids:
            return []  # If no bullies are assigned, return an empty list

        bullies = await session.execute(
            select(bully.Bully).filter(bully.Bully.id.in_(bully_ids))
        )

        return bullies.scalars().all()

    async def get_all_teams(self, session: AsyncSession) -> Dict[int, List[bully.Bully]]:
        all_teams = {}
        for player_id in self.teams_ids.keys():
            team = await self.get_team(player_id, session)
            all_teams[player_id] = team
        return all_teams


class ArenaFight:
    def __init__(self, arena: Arena, session: AsyncSession, bot: Bot, user:discord.abc.User, player: Player):
        self.arena = arena
        self.session = session
        self.bot = bot
        if (self.bot.user is None):
            raise Exception("The bot user is None")
        else :
            self.bot_user_id = self.bot.user.id
        self.user = user
        self.player = player
        self.player_teamfighters: List[FightingBully] = get_player_team(player)
        self.teams: Dict[int, List[bully.Bully]] = {}
        self.beaten_teams: Dict[int, List[bully.Bully]] = {}

    async def setup(self):
        self.teams = await self.arena.get_all_teams(self.session)

        bot_player = await self.session.get(Player, self.bot_user_id)
        if bot_player is None:
            raise Exception("The bot player is None")
        self.bot_player:Player = bot_player

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
        await ctx.send(f"{self.user.mention} has beaten these teams: {self.print_teams(self.beaten_teams)}")
        await self.session.refresh(self.arena)
        
        await self.update_arena_teams()
        await self.session.commit()
        print("end")
    
    async def update_arena_teams(self):
        arena_teams_ids = self.arena.teams_ids.copy()
        player_id_str = self.player.id.__str__()
        player_team = [f.bully for f in self.player_teamfighters]

        for i, (team_id, team_bullies_ids) in enumerate(arena_teams_ids.items()):
            if team_id in self.beaten_teams and self.is_team_equal_ids(team_id, team_id, team_bullies_ids, [b.id for b in self.beaten_teams[team_id]]):
                cloned_team_ids:list[int] = []
                for bully in player_team:
                    cloned_bully = bully.clone(self.bot_user_id)
                    self.bot_player.bullies.append(cloned_bully)
                    await self.session.flush() 
                    cloned_team_ids.append(cloned_bully.id)
                
                insert_index = i
                arena_teams_ids.pop(player_id_str, None) #type: ignore (it's because json keys are always strings)
                new_arena_teams_ids = list(arena_teams_ids.items())
                new_arena_teams_ids.insert(insert_index, (player_id_str, cloned_team_ids))
                self.arena.teams_ids = dict(new_arena_teams_ids)
                flag_modified(self.arena, "teams_ids")
                return
            elif player_id_str == team_id:
                #Dans ce cas, ça veut dire que le joueur n'a pas dépassé sa précedente équipe. Donc on ne fait rien
                return

    def is_team_equal_ids(self, player_id_1 : int, player_id_2:int, bullies_id_1:List[int], bullies_id_2:List[int]) -> bool:
        if player_id_1 != player_id_2:
            return False
        if len(bullies_id_1) != len(bullies_id_2):
            return False
        for id1, id2 in zip(bullies_id_1, bullies_id_2):
            if id1 != id2:
                return False
        return True

    def is_team_equal(self, player_id_1 : int, player_id_2:int, bullies_1:List[bully.Bully], bullies_2:List[bully.Bully]) -> bool:
        if player_id_1 != player_id_2:
            return False
        if len(bullies_1) != len(bullies_2):
            return False
        for b1, b2 in zip(bullies_1, bullies_2):
            if b1.id != b2.id:
                return False
        return True

    def print_teams(self, teams:Dict[int, List[bully.Bully]]) -> str:
        txt = ""
        for pid, fs in teams.items():
            txt += f"Player {pid}:\n"
            for f in fs :
                txt += f"{f.get_print(compact_print=True)}\n"
            txt += "\n"
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




