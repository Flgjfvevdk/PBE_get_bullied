
from dataclasses import dataclass, replace
from bully import Bully, Stats

@dataclass
class FightingBully():
    combattant: Bully
    pv: int
    base_stats: Stats
    stats: Stats

    @staticmethod
    def create_fighting_bully(b:Bully) -> "FightingBully":
        fighter = FightingBully(combattant=b, pv=b.max_pv, base_stats=replace(b.stats), stats=replace(b.stats))
        return fighter