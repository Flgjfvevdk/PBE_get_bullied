
from dataclasses import dataclass
from bully import Bully

@dataclass
class FightingBully():
    combattant: Bully
    pv: int
    base_stat:list
    stat: list

    @staticmethod
    def create_fighting_bully(b:Bully) -> "FightingBully":
        stat = [b.strength, b.agility, b.lethality, b.viciousness]
        fighter = FightingBully(combattant= b, pv= b.max_pv, base_stat= stat.copy(), stat= stat.copy())
        return fighter