
import asyncio
from pathlib import Path
import discord
from fight_manager import TeamFight
from fighting_bully import FightingBully, get_player_team, setup_buffs_team
import interact_game, money
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
from utils.locks import ArenaLock, PlayerLock
from all_texts import getText

CHOICE_TIMEOUT = 40
MAX_ARENA_TEAMS = 3
PRICE_ENTER = 100
REWARD_WIN_RANK = [300, 200, 120] #Il gagne une proportion de cette somme en fonction de son rang
BONUS_PAYDAY_CHAMPION = [2, 1.5, 1.2]

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
        rank = 1
        for player_id, bully_ids in self.teams_ids.items():
            player = await session.get(Player, player_id)
            if player:
                arena_team_str = ""
                user:discord.abc.User = await bot.fetch_user(player_id)
                bullies = await self.get_team(player_id, session)
                arena_team_str = str_team_short(user, bullies)
                arena_info += f"\nRang : {rank}{'er' if rank==1 else 'ème'}\n{arena_team_str}"
                rank +=1
        return (arena_info)

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
    def __init__(self, arena: Arena, ctx:Context, session: AsyncSession, bot: Bot, user:discord.abc.User, player: Player):
        self.arena = arena
        self.ctx = ctx
        self.session = session
        self.bot = bot
        if (self.bot.user is None):
            raise Exception("The bot user is None")
        else :
            self.bot_user_id = self.bot.user.id
        self.user = user
        self.player = player
        
        self.teams: Dict[int, List[bully.Bully]] = {}
        self.beaten_teams: Dict[int, List[bully.Bully]] = {}

    async def setup(self):
        await self.session.refresh(self.player)
        self.player_teamfighters: List[FightingBully] = get_player_team(self.player)
        self.teams = await self.arena.get_all_teams(self.session)

        bot_player = await self.session.get(Player, self.bot_user_id)
        if bot_player is None:
            raise Exception("The bot player is None")
        self.bot_player:Player = bot_player

        message_thread = await self.ctx.send(content=getText("arena_enter").format(user = self.user.mention))
        # message_thread = await self.ctx.send(content=f"{self.user.mention} has entered the arena!")
        self.thread:discord.Thread = await self.ctx.channel.create_thread(name=f"{self.user.name} est dans l'arene", message=message_thread) #type: ignore

    async def enter_hall(self):
        txt_arena = await self.arena.get_print(self.session, self.bot)
        event = asyncio.Event()
        txt_demande = "\n" + getText("arena_ask_enter").format(user=self.user.mention, price = PRICE_ENTER, money_emoji = money.MONEY_EMOJI) + "\n"
        # txt_demande = f"\n{self.user.mention}, voulez-vous entrer dans l'arène ? (Prix = {PRICE_ENTER} {money.MONEY_EMOJI})\n"
        message = await self.ctx.channel.send(content=txt_arena+txt_demande, 
                                view=interact_game.ViewClickBool(user=self.user, event=event, label=getText("arena_label").format(price = PRICE_ENTER), emoji="⚔️"))
        # message = await self.ctx.channel.send(content=txt_arena+txt_demande, view=interact_game.ViewClickBool(user=self.user, event=event, label=f"Enter The Arena (and pay {PRICE_ENTER})", emoji="⚔️"))
        try:
            await asyncio.wait_for(event.wait(), timeout=CHOICE_TIMEOUT)
        except asyncio.exceptions.TimeoutError as e:
            await message.edit(content = txt_arena, view=None)
            return
        
        lock = PlayerLock(self.user.id)
        if not lock.check():
            await self.ctx.send(getText("already_in_action"))
            # await self.ctx.send("You are already in an action.")
            return
        
        with lock :
            if self.player.money < PRICE_ENTER:
                await self.ctx.send(getText("arena_no_money").format(user=self.user.name, price = PRICE_ENTER, money_emoji = money.MONEY_EMOJI))
                # await self.ctx.send(f"{self.user.name}, you do not have enough {money.MONEY_EMOJI} to enter the arena (Price = {PRICE_ENTER})")
                await message.edit(content = txt_arena, view=None)
                return
            
            await self.setup()
            await self.fight()

    async def fight(self):
        while len(self.teams) > 0:
            enemy_player_team = self.teams.popitem()
            enemy_teamfighters:list[FightingBully] = [FightingBully.create_fighting_bully(b) for b in enemy_player_team[1]]
            self.add_champion_buff(enemy_teamfighters)
            setup_buffs_team(enemy_teamfighters, is_team_buff_active=True)
            await self.thread.send(getText("arena_next_teamfight").format(teamfighters=str_teamfighters_complete(self.user, enemy_teamfighters)))
            # await self.thread.send(f"Next teamfight against : \n{str_teamfighters_complete(self.user, enemy_teamfighters)}")

            teamfight = TeamFight(ctx=self.ctx, user_1=self.user, user_2=None, player_1=self.player, player_2=None, can_swap=True, channel_cible=self.thread)
            teamfight.setup_teams(team_1=self.player_teamfighters, team_2=enemy_teamfighters)
            try :
                player_won = await teamfight.start_teamfight()
            except interact_game.CancelChoiceException as e:
                await self.end_arena()
                return
            if player_won:
                self.beaten_teams[enemy_player_team[0]] = enemy_player_team[1]
                for b in self.player_teamfighters:
                    b.reset()
            else:
                await self.end_arena()
                return
        await self.end_arena()

    async def end_arena(self):
        async with ArenaLock(self.arena.id):
            await self.session.refresh(self.arena)
            
            rank = await self.update_arena_teams()
            if rank > 0:
                reward = REWARD_WIN_RANK[rank - 1] if rank <= len(REWARD_WIN_RANK) else 0
                money.give_money(self.player, reward)
                await self.ctx.send(getText("arena_reached_rank").format(user=self.user.mention, rank=rank, reward=reward, money_emoji = money.MONEY_EMOJI))
                # await self.ctx.send(f"{self.user.mention}, you have reached rank {rank} in the arena! (reward : {reward} {money.MONEY_EMOJI})")
            else:
                await self.ctx.send(getText("arena_no_improve_rank").format(user=self.user.mention))
                # await self.ctx.send(f"{self.user.mention}, you did not improve your rank in the arena.")
            await self.thread.delete()
            money.give_money(self.player, -PRICE_ENTER)
            await self.session.commit()
    

    async def update_arena_teams(self) -> int:
        arena_teams_ids = self.arena.teams_ids.copy()
        player_id_str = self.player.id.__str__()
        player_team = [f.bully for f in self.player_teamfighters]

        for i, (team_id, team_bullies_ids) in enumerate(arena_teams_ids.items()):
            if team_id in self.beaten_teams and is_team_equal_ids(team_id, team_id, team_bullies_ids, [b.id for b in self.beaten_teams[team_id]]):
                cloned_team_ids:list[int] = []
                for bully in player_team:
                    cloned_bully = bully.clone(self.bot_user_id)
                    self.session.add(cloned_bully)
                    await self.session.flush() 
                    self.bot_player.bullies.append(cloned_bully)
                    cloned_team_ids.append(cloned_bully.id)
                insert_index = i
                arena_teams_ids.pop(player_id_str, None) #type: ignore (it's because json keys are always strings)
                new_arena_teams_ids = list(arena_teams_ids.items())
                new_arena_teams_ids.insert(insert_index, (player_id_str, cloned_team_ids))
                new_arena_teams_ids = new_arena_teams_ids[:MAX_ARENA_TEAMS]
                self.arena.teams_ids = dict(new_arena_teams_ids)
                
                flag_modified(self.arena, "teams_ids")
                return insert_index + 1
            elif player_id_str == team_id:
                #Dans ce cas, ça veut dire que le joueur n'a pas dépassé sa précedente équipe. Donc on ne fait rien
                return -1
        return -1

    def add_champion_buff(self, fighters: List[FightingBully]):
        for fighter in fighters:
            fighter.add_buff("Champion")

def is_team_equal_ids(player_id_1 : int, player_id_2:int, bullies_id_1:List[int], bullies_id_2:List[int]) -> bool:
    if player_id_1 != player_id_2:
        return False
    if len(bullies_id_1) != len(bullies_id_2):
        return False
    for id1, id2 in zip(bullies_id_1, bullies_id_2):
        if id1 != id2:
            return False
    return True

def is_team_equal(player_id_1 : int, player_id_2:int, bullies_1:List[bully.Bully], bullies_2:List[bully.Bully]) -> bool:
    if player_id_1 != player_id_2:
        return False
    if len(bullies_1) != len(bullies_2):
        return False
    for b1, b2 in zip(bullies_1, bullies_2):
        if b1.id != b2.id:
            return False
    return True

def str_team_short(user:discord.User,  bullies: List[bully.Bully]) -> str:
    team_str = ""
    team_str += f"{user.display_name}'s Team:\n"
    infos_str = "Infos bullies : \n| "
    for b in bullies:
        infos_str += f"{b.lvl} - {b.rarity.name} | "
    team_str += infos_str
    
    return bully.mise_en_forme_str(team_str)

def str_teamfighters_complete(user:discord.abc.User,  teamfighters: List[FightingBully]) -> str:
    team_str = ""
    team_str += f"{user.display_name}'s Team:\n"
    for f in teamfighters:
        team_str += f"{f.get_print()}\n\n"
    return bully.mise_en_forme_str(team_str)

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

async def get_bonus_payday(session: AsyncSession, server_id:int,  player_id_str: str) -> int:
    arena = await session.get(Arena, server_id)
    if arena is None:
        return 1
    if arena.teams_ids.get(player_id_str, None) is not None:
        keys = list(arena.teams_ids.keys())
        index = keys.index(player_id_str)
        if index < len(BONUS_PAYDAY_CHAMPION):
            return BONUS_PAYDAY_CHAMPION[index]
    return 1


