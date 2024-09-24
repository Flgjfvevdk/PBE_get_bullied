from __future__ import annotations # Replace type hints to their string form (Item => "Item"), which resolves circular dependencies
                                   # WARNING: Should only be used for type hints
from dataclasses import dataclass, replace
from bully import Bully, Stats
        
class BuffFight():
    def __init__(self):
        self.name:str = self.__class__.__name__
        self.description:str = "No buff"
        # Ajouter variable si variables nécessaires
    def apply_buff(self, fighter:FightingBully, opponent:FightingBully, recap_round:RecapRound) -> None:
        return

    
@dataclass
class FightingBully():
    combattant: Bully
    pv: int
    base_stats: Stats
    stats: Stats
    buff:BuffFight = BuffFight()

    @staticmethod
    def create_fighting_bully(b:Bully) -> "FightingBully":
        fighter = FightingBully(combattant=b, pv=b.max_pv, base_stats=replace(b.stats), stats=replace(b.stats))
        return fighter
    
    def reset_stats(self) -> None:
        self.stats = replace(self.base_stats)


class RecapRound():
    def __init__(self, attacker:FightingBully, defender:FightingBully, is_success_agility:bool, is_success_block:bool, is_success_vicious:bool, damage_receive:int):
        self.attacker = attacker
        self.defender = defender

        self.is_success_agility = is_success_agility #Vrai si l'attaquant attaque car il a volé le tour du défenseur
        self.is_success_block = is_success_block
        self.is_success_vicious = is_success_vicious

        self.damage_receive = damage_receive #Ce sont les dégâts reçu SANS prendre en compte les buffs et effets.


#Les buffs qui existe : 
class NoBuff(BuffFight):
    def apply_buff(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound):
        return
    
class Rage(BuffFight):
    def __init__(self):
        super().__init__()
        self.description:str = "When damaged, buff Strength"
    def apply_buff(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound):
        if fighter == recap_round.defender and recap_round.damage_receive > 0:
            fighter.stats.strength += fighter.combattant.lvl * 0.15
        return 

class Frustration(BuffFight):
    def __init__(self):
        super().__init__()
        self.description:str = "When attack fails, buff Lethality"
    def apply_buff(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound):
        if fighter == recap_round.attacker and recap_round.damage_receive == 0:
            fighter.stats.lethality += fighter.combattant.lvl * 0.1
        return 
