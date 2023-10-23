
from dataclasses import dataclass, replace
from bully import Bully, Stats
from item import Item

@dataclass
class FightingBully():
    combattant: Bully
    pv: int
    base_stats: Stats
    stats: Stats

    equipped_item: Item|None = None

    @staticmethod
    def create_fighting_bully(b:Bully, item: Item|None = None) -> "FightingBully":
        fighter = FightingBully(combattant=b, pv=b.max_pv, base_stats=replace(b.stats), stats=replace(b.stats))
        return fighter