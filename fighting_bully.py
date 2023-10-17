
from dataclasses import dataclass
from bully import Bully

@dataclass
class fightingBully():
    combattant: Bully
    name: str
    lvl: int
    pv: int
    base_stat:list
    stat: list

    def create_fighting_bully(b:Bully):
        stat = [b.strength, b.agility, b.lethality, b.viciousness]
        fighter = fightingBully(combattant= b, name= b.name, lvl= b.lvl, pv= b.max_pv, base_stat= stat.copy(), stat= stat.copy())
        return fighter