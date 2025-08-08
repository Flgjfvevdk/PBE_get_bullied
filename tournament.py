import random
import discord
import asyncio
from typing import Callable, Dict, Tuple, Optional
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

from utils import database
from utils.discord_servers import load_servers
from utils.language_manager import language_manager_instance

TEST_PHASE = False

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
        
        guild_id = None
        if self.channel_annonce is not None:
            if isinstance(self.channel_annonce, (discord.TextChannel, discord.Thread, discord.VoiceChannel, discord.StageChannel, discord.ForumChannel)):
                guild_id = self.channel_annonce.guild.id
        lang = language_manager_instance.get_server_language(guild_id)

        performance = self.compute_performance()
        
        if performance:
            async with database.new_session() as session:
                ranking_txt = ""
                previous_score_index = float('inf')
                for player_id, score in performance.items():
                    score:int = round(min(score, previous_score_index - 1))
                    if score > 0 :
                        player = await session.get(Player, player_id)
                        if player is not None:
                            score_index = get_reward(score, player, lang)
                            previous_score_index = score_index
                    else : 
                        break
                    ranking_txt += getText("tournament_player_score", lang=lang).format(user=(await self.bot.fetch_user(player_id)).name, score=score) + "\n"
                    
                await session.commit()
                
            best_player_id, best_score = next(iter(performance.items()))
            best_player_name = (await self.bot.fetch_user(best_player_id)).name
            txt += getText("tournament_winner", lang=lang).format(user=best_player_name, score=best_score) + "\n"
            txt += ranking_txt
        
        if self.channel_annonce is not None:
            await self.channel_annonce.send(getText("tournament_end", lang=lang).format(results = txt))
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
        if TEST_PHASE : seconds_until_next_day = 2
        await asyncio.sleep(seconds_until_next_day)
        await self.end_tournament()
    
def is_sunday_utc():
    if TEST_PHASE : 
        return True
    # Get the current time in UTC
    now_utc = datetime.now(timezone.utc)
    # Check if the current day is Sunday (6 represents Sunday)
    return now_utc.weekday() == 6

tournaments:dict[int, Tournament] = {}

async def init_tournaments(bot:Bot):
    servers_ids = load_servers()
    for server_id in servers_ids:
        tournaments[server_id] = Tournament(bot, None)
    
def create_random_snack(value:int)->ConsumableAliment:
    return random.choice(list(AlimentEnum)).new_conso(value)
def create_water(value:int, rarity:Rarity, lang: Optional[str] = None)->Water:
    return Water(getText("water_name", lang=lang).format(rarity=rarity.name, value = value), value, rarity)
def create_random_elixir(category_level:int, lang: Optional[str] = None)->ConsumableElixirBuff:
    from buffs import BuffsLVL
    Buff = random.choice(BuffsLVL[category_level-1])
    buff_tag = Buff.__name__
    return ConsumableElixirBuff(getText("elixir_of", lang=lang).format(elixir = buff_tag), buff_tag)
async def force_add_multiple(player:Player, consos:list[Consumable]):
    for conso in consos:
        await force_add_conso(player, conso)


from abc import ABC, abstractmethod

class Reward(ABC):
    @abstractmethod
    def grant(self, player: Player) -> None:
        pass

class RewardMoney(Reward):
    amount: int
    def __init__(self, amount: int) -> None:
        self.amount = amount 
    def grant(self, player: Player) -> None:
        give_money(player, montant=self.amount)

class RewardConsumable(Reward):
    lambda_consumable: Callable[[Optional[str]],Consumable]
    def __init__(self, lambda_consumable: Callable[[Optional[str]],Consumable]) -> None:
        self.lambda_consumable = lambda_consumable 
    def grant(self, player: Player, lang: Optional[str] = None) -> None:
        player.consumables.append(self.lambda_consumable(lang))

class RewardMultipleConsumables(Reward):
    lambdas_consumables: Callable[[Optional[str]], list[Consumable]]
    def __init__(self, lambdas_consumables: Callable[[Optional[str]], list[Consumable]] ) -> None:
        self.lambdas_consumables = lambdas_consumables
    def grant(self, player: Player, lang: Optional[str] = None) -> None:
        for consumable in self.lambdas_consumables(lang):
            player.consumables.append(consumable)

REWARD_TABLE:dict[int, list[Reward]] = {
    2: [RewardMoney(200), RewardConsumable(lambda lang=None: create_random_elixir(1, lang))],
    4: [RewardMoney(750), RewardConsumable(lambda lang=None: create_random_elixir(2, lang)), RewardConsumable(lambda lang=None: create_water(2, Rarity.SUBLIME, lang))],
    6: [RewardConsumable(lambda lang=None: create_water(7, Rarity.TOXIC, lang)), RewardConsumable(lambda lang=None: create_water(6, Rarity.MONSTER, lang)), RewardMoney(1000)],
    8: [RewardConsumable(lambda lang=None: create_random_elixir(3, lang)), RewardConsumable(lambda lang=None: create_water(7, Rarity.DEVASTATOR, lang)), RewardConsumable(lambda lang=None: create_water(5, Rarity.SUBLIME, lang))],
    10: [RewardMultipleConsumables(lambda lang=None: [create_water(10, Rarity.DEVASTATOR, lang), create_water(10, Rarity.MONSTER, lang)]), RewardMultipleConsumables(lambda lang=None: [create_water(10, Rarity.SUBLIME, lang), create_water(10, Rarity.TOXIC, lang)])],
    12: [RewardConsumable(lambda lang=None: create_random_elixir(4, lang)), RewardMoney(5000), RewardConsumable(lambda lang=None: create_water(12, Rarity.SUBLIME, lang))],
    14: [RewardConsumable(lambda lang=None: create_water(35, Rarity.TOXIC, lang)), RewardConsumable(lambda lang=None: create_water(30, Rarity.MONSTER, lang)), RewardConsumable(lambda lang=None: create_water(25, Rarity.DEVASTATOR, lang)), RewardConsumable(lambda lang=None: create_water(20, Rarity.SUBLIME, lang))],
    16: [RewardConsumable(lambda lang=None: create_random_elixir(5, lang)), RewardConsumable(lambda lang=None: create_water(24, Rarity.SUBLIME, lang)), RewardConsumable(lambda lang=None: create_water(36, Rarity.DEVASTATOR, lang))],
    18: [RewardMoney(10000), RewardConsumable(lambda lang=None: create_water(5, Rarity.DEVASTATOR, lang)), RewardMultipleConsumables(lambda lang=None: [create_water(10, Rarity.TOXIC, lang), create_water(10, Rarity.MONSTER, lang), create_water(10, Rarity.SUBLIME, lang)]), RewardMultipleConsumables(lambda lang=None: [create_random_elixir(5, lang), create_random_snack(100)])],
    20: [RewardConsumable(lambda lang=None: create_water(50, Rarity.SUBLIME, lang)), RewardMultipleConsumables(lambda lang=None: [create_water(50, Rarity.DEVASTATOR, lang), create_water(50, Rarity.MONSTER, lang)]), RewardMultipleConsumables(lambda lang=None: [create_water(25, Rarity.DEVASTATOR, lang), create_water(25, Rarity.MONSTER, lang), create_water(25, Rarity.TOXIC, lang)]), RewardMultipleConsumables(lambda lang=None: [create_random_elixir(5, lang), create_water(15, Rarity.SUBLIME, lang)])]
}


def get_reward(score: int, player: Player, lang: Optional[str] = None) -> int:
    score_index = max((k for k in REWARD_TABLE.keys() if k <= score), default = None)
    if score_index is not None:
        reward = random.choice(REWARD_TABLE[score_index])
        if isinstance(reward, (RewardConsumable, RewardMultipleConsumables)):
            reward.grant(player, lang)
        else:
            reward.grant(player)
        return score_index
    return 0

async def setup_tournament_for_server(bot: Bot, server_id: int):
    """Setup tournament for a specific server"""
    if server_id not in tournaments:
        tournaments[server_id] = Tournament(bot, None)
