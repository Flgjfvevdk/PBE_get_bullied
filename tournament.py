import discord
import asyncio
from typing import Dict, Tuple
from player_info import Player
from datetime import datetime, timedelta, timezone
from discord.ext.commands import Bot
from all_texts import getText
from utils.discord_servers import load_servers

class Tournament:
    def __init__(self, bot:Bot, channel_annonce : discord.abc.Messageable|None):
        self.bot:Bot = bot
        self.active:bool = False
        self.results: Dict[Tuple[int, int], int] = {}  # Stores results as {(player1_id, player2_id): winner_id}
        self.channel_annonce : discord.abc.Messageable|None = channel_annonce
        self._timer_task = None

    def activate(self):
        self.active = True
        self._start_timer()

    def deactivate(self):
        self.active = False
        self.channel_annonce = None

    def register_teamfight_result(self, player_id1: int, player_id2: int, winner_id: int, channel: discord.abc.Messageable):
        if not self.active:
            if is_sunday_utc():
                self.activate()
            else :
                return

        if self.channel_annonce is None:
            self.channel_annonce = channel

        # Ensure player1_id is always less than player2_id for consistency
        if player_id1 > player_id2:
            player_id1, player_id2 = player_id2, player_id1

        fight_key = (player_id1, player_id2)

        if fight_key not in self.results:
            self.results[fight_key] = winner_id
            return 
        else:
            return 

    def get_results(self):
        return self.results
    
    async def end_tournament(self):
        saved_id_to_names:dict[int, str] = {}
        txt = ""
        for fight, winner in self.results.items():
            username1 = (await self.bot.fetch_user(fight[0])).name if fight[0] not in saved_id_to_names else saved_id_to_names[fight[0]]
            saved_id_to_names[fight[0]] = username1
            username2 = (await self.bot.fetch_user(fight[1])).name if fight[1] not in saved_id_to_names else saved_id_to_names[fight[1]]
            saved_id_to_names[fight[1]] = username2
            winnername = saved_id_to_names[winner]
            txt += getText("tournament_recap_fight").format(user1=username1, user2=username2, winner=winnername) + "\n"

        if self.channel_annonce is not None:
            await self.channel_annonce.send(getText("tournament_end").format(results = txt))
        else : 
            print("Channel is None")

        self.results.clear()
        self.deactivate()

    def _start_timer(self):
        if self._timer_task is None or self._timer_task.done():
            self._timer_task = asyncio.create_task(self._monitor_sunday())

    async def _monitor_sunday(self):
        if not is_sunday_utc():
            await self.end_tournament()
            return

        # Calculate the number of seconds until the end of Sunday
        now_utc = datetime.now(timezone.utc)
        next_day = now_utc + timedelta(days=1)
        next_day_start = datetime(next_day.year, next_day.month, next_day.day, tzinfo=timezone.utc)
        seconds_until_next_day = (next_day_start - now_utc).total_seconds()
        # seconds_until_next_day = 40
        await asyncio.sleep(seconds_until_next_day)
        await self.end_tournament()
    
def is_sunday_utc():
    # return True
    # Get the current time in UTC
    now_utc = datetime.now(timezone.utc)
    # Check if the current day is Sunday (6 represents Sunday)
    return now_utc.weekday() == 6

tournaments:dict[int, Tournament] = {}

async def init_tournaments(bot:Bot):
    # channel_id = 1004117014358528063
    # channel = await bot.fetch_channel(channel_id)
    servers_ids = load_servers()
    for server_id in servers_ids:
        tournaments[server_id] = Tournament(bot, None)
    # if isinstance(channel, discord.abc.Messageable):
    #     tournaments[0] = Tournament(bot, channel)
    
    

