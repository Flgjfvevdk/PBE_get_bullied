from fighting_bully import BuffFight, FightingBully, RecapRound
from bully import Bully

#Les buffs qui existe : /////////////////////////////////////////////////////////////////////////
class NoBuff(BuffFight):
    pass
    # def apply_aggresive(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) -> tuple[int, int]:
    #     return 0 ,0
    
class Rage(BuffFight):
    description:str = "When damaged, buff Strength"
    def __init__(self):
        super().__init__()
    def apply_defensive(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) :
        if fighter == recap_round.defender and recap_round.damage_receive_defender > 0:
            fighter.stats.strength += fighter.combattant.lvl * 0.15
        return 
    
class Frustration(BuffFight):
    description:str = "When attack fails, buff Lethality"
    def __init__(self):
        super().__init__()
    def apply_aggresive(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) -> tuple[int, int]:
        if fighter == recap_round.attacker and recap_round.is_success_block:
            fighter.stats.lethality += fighter.combattant.lvl * 0.1
        return 0, 0
    
class Brutal(BuffFight):
    description:str = "Critical damages are increase by one."
    def __init__(self):
        super().__init__()
    def apply_aggresive(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) -> tuple[int, int]:
        if fighter == recap_round.attacker and recap_round.is_success_lethal:
            opponent.pv -= 1
            return 0, 1
        return 0, 0
    
class Ironskin(BuffFight):
    description:str = "Reduce critical damage by one."
    def __init__(self):
        super().__init__()
    def apply_defensive(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) :
        if fighter == recap_round.defender and recap_round.is_success_lethal and recap_round.damage_receive_defender > 0:
            fighter.pv += 1
        return 
    
class SlimyPunch(BuffFight):
    description:str = "When the enemy is hit, their agility is reduced."
    def __init__(self):
        super().__init__()
    def apply_aggresive(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) -> tuple[int, int]:
        if fighter == recap_round.attacker and not recap_round.is_success_block:
            opponent.stats.agility *= 0.9
        return 0, 0
    
class SlimyBody(BuffFight):
    description:str = "When hit, reduces the enemy's agility."
    def __init__(self):
        super().__init__()
    def apply_aggresive(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) -> tuple[int, int]:
        if fighter == recap_round.defender and not recap_round.is_success_block:
            opponent.stats.agility *= 0.9
        return 0, 0
    
class RoyalSlimyBody(BuffFight):
    description:str = "When blocking an attack, reduces the enemy's agility."
    def __init__(self):
        super().__init__()
    def apply_aggresive(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) -> tuple[int, int]:
        if fighter == recap_round.defender and recap_round.is_success_block:
            opponent.stats.agility *= 0.96
        return 0, 0

class RootOfEvil(BuffFight):
    description:str = "When get vicious debuff, increase your Viciousness."
    def __init__(self):
        super().__init__()
    def apply_defensive(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) :
        if fighter == recap_round.defender and recap_round.is_success_vicious:
            fighter.stats.viciousness += recap_round.malus_vicious
        return 

class GoldenSkin(BuffFight):
    description:str = "Can't receive more than 2 damages at once."
    def __init__(self):
        super().__init__()
    def apply_defensive(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) :
        if recap_round.get_damage_receive(fighter) > 2:
            fighter.pv += recap_round.get_damage_receive(fighter) - 2
        return 
    
class ThornSkin(BuffFight):
    description:str = "Deals damage to the attacker when hit by a critical strike."
    def __init__(self):
        super().__init__()
    def apply_defensive(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) :
        if recap_round.get_damage_receive(fighter) > 2:
            fighter.pv += recap_round.get_damage_receive(fighter) - 2
        return 
    
class Lycanthropy(BuffFight):
    description:str = "Swap Lethality and Viciousness depending on enemy's HP."
    def __init__(self):
        super().__init__()
    def apply_defensive(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) :
        best_s = max(fighter.stats.lethality, fighter.stats.viciousness)
        worst_s = min(fighter.stats.lethality, fighter.stats.viciousness)
        if opponent.pv < opponent.combattant.max_pv / 2:
            fighter.stats.lethality = best_s
            fighter.stats.viciousness = worst_s
        else:
            fighter.stats.lethality = worst_s
            fighter.stats.viciousness = best_s
        return 

class VampireCharm(BuffFight):
    description:str = "When deal vicious damage on the enemy, regen HP."
    def __init__(self):
        super().__init__()
    def apply_defensive(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound):
        if fighter == recap_round.attacker and not recap_round.is_success_block and recap_round.is_success_vicious:
            fighter.pv = min(fighter.combattant.max_pv, fighter.pv + 1)
        return

class Venomous(BuffFight):
    description:str = "Poison enemy on critical strikes."
    def __init__(self):
        super().__init__()
    def apply_defensive(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound):
        if fighter == recap_round.attacker and recap_round.is_success_lethal :
            not_poisoned = len([b for b in opponent.buffs if isinstance(b, Poisoned)]) == 0
            if not_poisoned:
                opponent.buffs.append(Poisoned(difficulty=fighter.stats.lethality))
            
        return
    
class Poisoned(BuffFight):
    description:str = "Take damage every round. Can get rid of it with Strength."
    def __init__(self, difficulty = 1.0 ):
        super().__init__()
        self.difficulty = difficulty
    def apply_aggresive(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) -> tuple[int, int]:
        if Bully.clash_stat(st_actif = opponent.stats.strength, st_passif = self.difficulty) :
            fighter.buffs.remove(self)
        else :
            fighter.pv -= 1
        return 1, 0
    
