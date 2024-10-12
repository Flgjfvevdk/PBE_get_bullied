from fighting_bully import BuffFight, FightingBully, RecapRound
from bully import Bully
import random

#Les buffs qui existe : /////////////////////////////////////////////////////////////////////////
class NoBuff(BuffFight):
    pass

#1-10 
class Rage(BuffFight):
    description:str = "When damaged, increase Strength."
    def __init__(self):
        super().__init__()
    def apply_defensive(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) :
        if fighter == recap_round.defender and recap_round.damage_receive_defender > 0:
            fighter.stats.strength += fighter.combattant.lvl * 0.15
        return 
    
class DislocatedParts(BuffFight):
    description:str = "When damaged, increase Agility."
    def __init__(self):
        super().__init__()
    def apply_defensive(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) :
        if fighter == recap_round.defender and recap_round.damage_receive_defender > 0:
            fighter.stats.agility += fighter.combattant.lvl * 0.15
        return 
    
class AngerIssue(BuffFight):
    description:str = "When damaged, increase Lethality."
    def __init__(self):
        super().__init__()
    def apply_defensive(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) :
        if fighter == recap_round.defender and recap_round.damage_receive_defender > 0:
            fighter.stats.lethality += fighter.combattant.lvl * 0.15
        return 

class Brutal(BuffFight):
    description:str = "Deals one more critical damage."
    def __init__(self):
        super().__init__()
    def apply_aggresive(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) -> tuple[int, int]:
        if fighter == recap_round.attacker and recap_round.is_success_lethal:
            opponent.pv -= 1
            return 0, 1
        return 0, 0
    
class Ironskin(BuffFight):
    description:str = "Take one less critical damage."
    def __init__(self):
        super().__init__()
    def apply_defensive(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) :
        if fighter == recap_round.defender and recap_round.is_success_lethal and recap_round.damage_receive_defender > 0:
            fighter.pv += 1
        return 

#11-20   
class SlimyPunch(BuffFight):
    description:str = "When the enemy is hit, their Agility is reduced."
    def __init__(self):
        super().__init__()
    def apply_aggresive(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) -> tuple[int, int]:
        if fighter == recap_round.attacker and not recap_round.is_success_block:
            opponent.stats.agility *= 0.9
        return 0, 0
    
class SlimyBody(BuffFight):
    description:str = "When hit, reduce the enemy's Agility."
    def __init__(self):
        super().__init__()
    def apply_aggresive(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) -> tuple[int, int]:
        if fighter == recap_round.defender and not recap_round.is_success_block:
            opponent.stats.agility *= 0.9
        return 0, 0

class ThornSkin(BuffFight):
    description:str = "Deals damage to the attacker when hit by a critical strike."
    def __init__(self):
        super().__init__()
    def apply_aggresive(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) :
        if fighter == recap_round.defender and recap_round.is_success_lethal:
            opponent.pv -= 1
            return 0, 1
        return 0, 0
  
class Frustration(BuffFight):
    description:str = "When attack fails, increase Lethality."
    def __init__(self):
        super().__init__()
    def apply_aggresive(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) -> tuple[int, int]:
        if fighter == recap_round.attacker and recap_round.is_success_block:
            fighter.stats.lethality += fighter.combattant.lvl * 0.1
        return 0, 0

#21-30  
class RoyalSlimyBody(BuffFight):
    description:str = "When blocking an attack, reduce the enemy's Agility."
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
    

#31-40
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

class BossStage(BuffFight):
    description:str = "Increase stats when below half HP."
    def __init__(self):
        super().__init__()
        self.first_stage = True
    def apply_defensive(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound):
        if self.first_stage and fighter.pv < fighter.combattant.max_pv / 2:
            fighter.stats.strength += fighter.combattant.lvl * 0.7
            fighter.stats.agility += fighter.combattant.lvl * 0.7
            self.first_stage = False
        return

#41-50
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

class DeathFrenzy(BuffFight):
    description:str = "Heal HP upon striking an enemy to death."
    def __init__(self):
        super().__init__()
    def apply_aggresive(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) -> tuple[int, int]:
        if fighter == recap_round.attacker and not recap_round.is_success_block and opponent.pv <= 0 :
            fighter.pv += 4
            return -4, 0
        return 0, 0

class Scary(BuffFight):
    description:str = "Vicious debuff can haunt the enemy."
    def __init__(self):
        super().__init__()
        self.proba = 0.3
    def apply_defensive(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound):
        if fighter == recap_round.attacker and recap_round.is_success_vicious and random.random() < self.proba:
            not_haunted = len([b for b in opponent.buffs if isinstance(b, Haunted)]) == 0
            if not_haunted:
                opponent.buffs.append(Haunted())
        return

#Buff Negatif
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
    
class Haunted(BuffFight):
    description:str = "Deactivate buffs until successfully hitting an enemy."
    def __init__(self):
        super().__init__()
        self.saved_buffs:list[BuffFight] = []
        self.is_active = False
    def apply_defensive(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) :
        if not self.is_active :
            for b in fighter.buffs:
                if not isinstance(b, Haunted):
                    self.saved_buffs.append(b)
            self.is_active = True
            fighter.buffs = []
        elif fighter == recap_round.attacker and not recap_round.is_success_block:
            fighter.buffs = self.saved_buffs.copy()

        

#Special Buff (for special occasion)
class Friendship(BuffFight):
    description:str = "All your friends love you."

#Unique Buff (for Unique character)
class Cat(BuffFight):
    description:str = "Cats have 9 lives!"
    def __init__(self):
        super().__init__()
        self.vies = 9
    def apply_defensive(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound):
        if fighter.pv <= 0 and self.vies > 0:
            self.vies -= 1
            fighter.pv = fighter.combattant.max_pv
        return
class Vilain(BuffFight):
    description:str = "Increase Viciousness when the enemy suffers from a vicious attack."
    def __init__(self):
        super().__init__()
    def apply_defensive(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound):
        if fighter == recap_round.attacker and recap_round.is_success_vicious:
            fighter.stats.viciousness += recap_round.malus_vicious
        return
class SpaceCake(BuffFight):
    description:str = "When striking an enemy, swap two of their stats."
    def __init__(self):
        super().__init__()
    def apply_defensive(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound):
        if fighter == recap_round.attacker and not recap_round.is_success_block:
            s1, s2 = random.sample(["strength", "agility", "viciousness", "lethality"], 2)
            v1, v2 = getattr(opponent.stats, s1), getattr(opponent.stats, s2)
            setattr(opponent.stats, s1, v2)
            setattr(opponent.stats, s2, v1)
        return
class SuppaFastAndFurious(BuffFight):
    description:str = "Fast attacks = more damage."
    def __init__(self):
        super().__init__()
    def apply_aggresive(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) :
        if fighter == recap_round.attacker and recap_round.is_success_agility and not recap_round.is_success_block:
            opponent.pv -= 1
            return 0, 1
        return 0, 0
class StrangeGift(BuffFight):
    description:str = "On death, replace the enemy's buffs with a debuff."
    def __init__(self):
        super().__init__()
    def apply_defensive(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) :
        if fighter.pv <= 0:
            opponent.buffs = [Poisoned(difficulty=fighter.stats.viciousness)]
        return 
class Bombe(BuffFight):
    description:str = "When struck to death, deal 5 damage to the enemy."
    def __init__(self):
        super().__init__()
    def apply_aggresive(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) :
        if fighter.pv <= 0:
            opponent.pv -= 5
            return 0, 5
        return 0, 0