import random
import discord
import asyncio
from typing import Dict, Tuple
from collections import OrderedDict
from bully import Rarity
from consumable import AlimentEnum, Consumable, ConsumableAliment, ConsumableElixirBuff, force_add_conso
from consumable import ConsumableWaterLvl as Water
from fighting_bully import CategoryBuff
from money import give_money
from player_info import Player
from datetime import datetime, timedelta, timezone
from discord.ext.commands import Bot
from all_texts import getText

from utils.discord_servers import load_servers

TEST_PHASE = True

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

    def compute_performance(self) -> OrderedDict[int, int]:
        performance: Dict[int, int] = {}
        for (player1_id, player2_id), winner_id in self.results.items():
            #On s'assure que les 2 players sont dans le dictionnaire performance
            if player1_id not in performance:
                performance[player1_id] = 0
            if player2_id not in performance:
                performance[player2_id] = 0

            loser_id:int = player1_id if winner_id == player2_id else player2_id
            performance[winner_id] += 2
            performance[loser_id] += 1

        # Order the performance dictionary by score in descending order
        ordered_performance = OrderedDict(sorted(performance.items(), key=lambda item: item[1], reverse=True))
        return ordered_performance


    async def end_tournament(self):
        saved_id_to_names:dict[int, str] = {}
        txt = ""

        performance = self.compute_performance()
        print("super")
        if performance:
            best_player_id, best_score = next(iter(performance.items()))
            best_player_name = (await self.bot.fetch_user(best_player_id)).name
            best_player = await self.bot.fetch_user(best_player_id)
            reward_function = get_reward(best_score)
            if reward_function is not None:
                await reward_function(best_player)
            txt += getText("tournament_winner").format(user=best_player_name, score=best_score) + "\n"
        print("non")
        for fight, winner in self.results.items():
            username1 = (await self.bot.fetch_user(fight[0])).name if fight[0] not in saved_id_to_names else saved_id_to_names[fight[0]]
            saved_id_to_names[fight[0]] = username1
            username2 = (await self.bot.fetch_user(fight[1])).name if fight[1] not in saved_id_to_names else saved_id_to_names[fight[1]]
            saved_id_to_names[fight[1]] = username2
            winnername = saved_id_to_names[winner]
            txt += getText("tournament_recap_fight").format(user1=username1, user2=username2, winner=winnername) + "\n"
        print("uhefggfye")
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
        if TEST_PHASE : seconds_until_next_day = 10
        print("ouais")
        await asyncio.sleep(seconds_until_next_day)
        print("non")
        await self.end_tournament()
    
def is_sunday_utc():
    if TEST_PHASE : 
        print("ici")
        return True
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
    
def create_random_snack(value:int)->ConsumableAliment:
    return random.choice(list(AlimentEnum)).new_conso(value)
def create_water(value:int, rarity:Rarity)->Water:
    return Water(getText("water_name").format(rarity=rarity.name, value = value), value, rarity)
def create_random_elixir(category_level:int)->ConsumableElixirBuff:
    from ruine import BuffsLVL
    Buff = random.choice(BuffsLVL[category_level])
    buff_tag = Buff.__name__
    return ConsumableElixirBuff(getText("elixir_of").format(elixir = buff_tag), buff_tag)
async def force_add_multiple(player:Player, consos:list[Consumable]):
    for conso in consos:
        await force_add_conso(player, conso)

REWARD_TABLE = {
    2: [lambda player: give_money(player, 200), lambda player: force_add_conso(player, create_random_elixir(1))],
    4: [lambda player: give_money(player, 750), lambda player: force_add_conso(player, create_random_elixir(2)), lambda player: force_add_conso(player, create_water(2, Rarity.SUBLIME))],
    6: [lambda player: force_add_conso(player, create_water(7, Rarity.TOXIC)), lambda player: force_add_conso(player, create_water(6, Rarity.MONSTER)), lambda player: give_money(player, 1000)],
    8: [lambda player: force_add_conso(player, create_random_elixir(3)), lambda player: force_add_conso(player, create_water(7, Rarity.DEVASTATOR)), lambda player: force_add_conso(player, create_water(5, Rarity.SUBLIME))],
    10: [lambda player: force_add_multiple(player, [create_water(10, Rarity.DEVASTATOR), create_water(10, Rarity.MONSTER)]), lambda player: force_add_multiple(player, [create_water(10, Rarity.SUBLIME), create_water(10, Rarity.TOXIC)])],
    12: [lambda player: force_add_conso(player, create_random_elixir(4)), lambda player: give_money(player, 5000), lambda player: force_add_conso(player, create_water(12, Rarity.SUBLIME))],
    14: [lambda player: force_add_conso(player, create_water(35, Rarity.TOXIC)), lambda player: force_add_conso(player, create_water(30, Rarity.MONSTER)), lambda player: force_add_conso(player, create_water(25, Rarity.DEVASTATOR)), lambda player: force_add_conso(player, create_water(20, Rarity.SUBLIME))],
    16: [lambda player: force_add_conso(player, create_random_elixir(5)), lambda player: force_add_conso(player, create_water(24, Rarity.SUBLIME)), lambda player: force_add_conso(player, create_water(36, Rarity.DEVASTATOR))],
    18: [lambda player: give_money(player, 10000), lambda player: force_add_conso(player, create_water(5, Rarity.DEVASTATOR)), lambda player: force_add_multiple(player, [create_water(10, Rarity.TOXIC), create_water(10, Rarity.MONSTER), create_water(10, Rarity.SUBLIME)]), lambda player: force_add_multiple(player, [create_random_elixir(5), create_random_snack(100)])],
    20: [lambda player: force_add_conso(player, create_water(50, Rarity.SUBLIME)), lambda player: force_add_multiple(player, [create_water(50, Rarity.DEVASTATOR), create_water(50, Rarity.MONSTER)]), lambda player: force_add_multiple(player, [create_water(25, Rarity.DEVASTATOR), create_water(25, Rarity.MONSTER), create_water(25, Rarity.TOXIC)]), lambda player: force_add_multiple(player, [create_random_elixir(5), create_water(15, Rarity.SUBLIME)])]
}


def get_reward(score: int):
    for score_threshold in sorted(REWARD_TABLE.keys(), reverse=True):
        if score >= score_threshold:
            return random.choice(REWARD_TABLE[score_threshold])
    return None
