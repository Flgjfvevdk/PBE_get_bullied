from __future__ import annotations # Replace type hints to their string form (Item => "Item"), which resolves circular dependencies
                                   # WARNING: Should only be used for type hints
from dataclasses import dataclass, replace
from bully import Bully, Stats
import item

@dataclass
class FightingBully():
    combattant: Bully
    pv: int
    base_stats: Stats
    stats: Stats

    equipped_item: item.Item|None = None

    @staticmethod
    def create_fighting_bully(b:Bully, i: item.Item|None = None) -> "FightingBully":
        fighter = FightingBully(combattant=b, pv=b.max_pv, base_stats=replace(b.stats), stats=replace(b.stats))
        fighter.equipped_item = i
        return fighter
    
    def reset_stats(self) -> None:
        self.stats = replace(self.base_stats)