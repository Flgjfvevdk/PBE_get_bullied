from fighting_bully import BuffFight, FightingBully, RecapRound, CategoryBuff
from bully import Bully
import random
import math

#Les buffs qui existe : /////////////////////////////////////////////////////////////////////////
class NoBuff(BuffFight):
    category:CategoryBuff = CategoryBuff.NONE
    pass

#1-10 
class Rage(BuffFight):
    description:str = "À chaque dégât subit, augmente sa Strength."
    description_en:str = "When damaged, increase Strength."
    def __init__(self, fighter:FightingBully|None = None):
        super().__init__()
    def apply_defensive(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) :
        if fighter == recap_round.defender and recap_round.damage_receive_defender > 0:
            fighter.stats.strength += fighter.combattant.lvl * 0.15
        return 
    
class DislocatedParts(BuffFight):
    description:str = "À chaque dégât subit, augmente sa Agility."
    description_en:str = "When damaged, increase Agility."
    def __init__(self, fighter:FightingBully|None = None):
        super().__init__()
    def apply_defensive(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) :
        if fighter == recap_round.defender and recap_round.damage_receive_defender > 0:
            fighter.stats.agility += fighter.combattant.lvl * 0.15
        return 
    
class AngerIssue(BuffFight):
    description:str = "À chaque dégât subit, augmente sa Lethality."
    description_en:str = "When damaged, increase Lethality."
    def __init__(self, fighter:FightingBully|None = None):
        super().__init__()
    def apply_defensive(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) :
        if fighter == recap_round.defender and recap_round.damage_receive_defender > 0:
            fighter.stats.lethality += fighter.combattant.lvl * 0.15
        return 

class Brutal(BuffFight):
    description:str = "Augmente de 1 les dégâts de ses coups critiques."
    description_en:str = "Deals one more critical damage."
    def __init__(self, fighter:FightingBully|None = None):
        super().__init__()
    def apply_aggresive(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) -> tuple[int, int]:
        if fighter == recap_round.attacker and recap_round.is_success_lethal:
            opponent.pv -= 1
            return 0, 1
        return 0, 0
    
class Ironskin(BuffFight):
    description:str = "Reçoit 1 dégât de moins des coups critiques."
    description_en:str = "Take one less critical damage."
    def __init__(self, fighter:FightingBully|None = None):
        super().__init__()
    def apply_defensive(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) :
        if fighter == recap_round.defender and recap_round.damage_bonus_lethal > 0 and recap_round.damage_receive_defender > 0:
            fighter.pv += 1
            recap_round.damage_bonus_lethal -= 1
        return 

#11-20   
class SlimyPunch(BuffFight):
    description:str = "À chaque frappe réussit, réduit l'Agility de l'adversaire."
    description_en:str = "When the enemy is hit, their Agility is reduced."
    def __init__(self, fighter:FightingBully|None = None):
        super().__init__()
    def apply_aggresive(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) -> tuple[int, int]:
        if fighter == recap_round.attacker and not recap_round.is_success_block:
            opponent.stats.agility *= 0.92
        return 0, 0
    
class SlimyBody(BuffFight):
    description:str = "À chaque coup subit, réduit l'Agility de l'adversaire."
    description_en:str = "When hit, reduce the enemy's Agility."
    def __init__(self, fighter:FightingBully|None = None):
        super().__init__()
    def apply_defensive(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound):
        if fighter == recap_round.defender and not recap_round.is_success_block:
            opponent.stats.agility *= 0.9
        return

class ThornSkin(BuffFight):
    description:str = "À chaque coup critique subit, renvoie 1 dégât à l'attaquant."
    description_en:str = "Deals damage to the attacker when hit by a critical strike."
    def __init__(self, fighter:FightingBully|None = None):
        super().__init__()
    def apply_aggresive(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) :
        if fighter == recap_round.defender and recap_round.is_success_lethal:
            opponent.pv -= 1
            return 0, 1
        return 0, 0
  
class Frustration(BuffFight):
    description:str = "À chaque attaque raté, augmente sa Lethality."
    description_en:str = "When attack fails, increase Lethality."
    def __init__(self, fighter:FightingBully|None = None):
        super().__init__()
    def apply_aggresive(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) -> tuple[int, int]:
        if fighter == recap_round.attacker and recap_round.is_success_block:
            fighter.stats.lethality += fighter.combattant.lvl * 0.1
        return 0, 0

class DragonSkin(BuffFight):
    description:str = "Ne reçoit pas de dégât des attaques non critiques."
    description_en:str = ""
    def __init__(self, fighter:FightingBully|None = None):
        super().__init__()
    def apply_defensive(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) :
        if recap_round.defender == fighter and not recap_round.is_success_lethal and recap_round.get_damage_receive(fighter) > 0:
            fighter.pv += 1
        return 
    

#21-30  
class RoyalSlimyBody(BuffFight):
    description:str = "À chaque attaque bloqué, réduit l'Agility de l'attaquant."
    description_en:str = "When blocking an attack, reduce the enemy's Agility."
    def __init__(self, fighter:FightingBully|None = None):
        super().__init__()
    def apply_aggresive(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) -> tuple[int, int]:
        if fighter == recap_round.defender and recap_round.is_success_block:
            opponent.stats.agility *= 0.96
        return 0, 0

class RootOfEvil(BuffFight):
    description:str = "À chaque fois attaque vicieuse subit, augmente sa Viciousness."
    description_en:str = "When get vicious debuff, increase your Viciousness."
    def __init__(self, fighter:FightingBully|None = None):
        super().__init__()
    def apply_defensive(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) :
        if fighter == recap_round.defender and recap_round.is_success_vicious:
            fighter.stats.viciousness += recap_round.malus_vicious
        return 

class GoldenSkin(BuffFight):
    description:str = "Ne peut pas recevoir plus de 2 dégâts en 1 round."
    description_en:str = "Can't receive more than 2 damages at once."
    def __init__(self, fighter:FightingBully|None = None):
        super().__init__()
    def apply_defensive(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) :
        if recap_round.get_damage_receive(fighter) > 2:
            fighter.pv += recap_round.get_damage_receive(fighter) - 2
        return 
    
class SharpTeeth(BuffFight):
    description:str = "Ses coups critiques diminuent la Strength de l'adversaire."
    description_en:str = ""
    def __init__(self, fighter:FightingBully|None = None):
        super().__init__()
    def apply_aggresive(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) -> tuple[int, int]:
        if fighter == recap_round.attacker and recap_round.is_success_lethal:
            opponent.stats.strength *= 0.9
        return 0, 0

class DragonResilience(BuffFight):
    description:str = "À chaque fois attaque vicieuse subit, augmente sa Strength."
    description_en:str = ""
    def __init__(self, fighter:FightingBully|None = None):
        super().__init__()
    def apply_defensive(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound):
        if fighter == recap_round.defender and recap_round.is_success_vicious:
            fighter.stats.strength += recap_round.malus_vicious*0.5
        return

#31-40
class Lycanthropy(BuffFight):
    description:str = "Échange la Lethality et la Viciousness selon les HP de l'adversaire."
    description_en:str = "Swap Lethality and Viciousness depending on enemy's HP."
    def __init__(self, fighter:FightingBully|None = None):
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
    description:str = "À chaque coup vicieux blessant l'adversaire, régénère 1 HP."
    description_en:str = "When deal vicious damage on the enemy, regen HP."
    def __init__(self, fighter:FightingBully|None = None):
        super().__init__()
    def apply_defensive(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound):
        if fighter == recap_round.attacker and not recap_round.is_success_block and recap_round.is_success_vicious:
            fighter.pv = min(fighter.combattant.max_pv, fighter.pv + 1)
        return

class BossStage(BuffFight):
    description:str = "Augmente toutes ses stats après avoir perdu la moitié de ses HP."
    description_en:str = "Increase stats when below half HP."
    def __init__(self, fighter:FightingBully|None = None):
        super().__init__()
        self.first_stage = True
    def apply_defensive(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound):
        if self.first_stage and fighter.pv < fighter.combattant.max_pv / 2:
            fighter.stats.strength += fighter.combattant.lvl * 1.5
            fighter.stats.agility += fighter.combattant.lvl * 1.5
            self.first_stage = False
        return

class Overdrive(BuffFight):
    description:str = "Commence avec des gros buffs de stats mais s'essouffle peu à peu."
    description_en:str = ""
    def __init__(self, fighter:FightingBully|None = None):
        super().__init__()
        if fighter is not None : 
            bonus = fighter.combattant.lvl * 2
            fighter.stats.strength += bonus
            fighter.stats.agility += bonus
            fighter.stats.lethality += bonus
            fighter.stats.viciousness += bonus
    def apply_defensive(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound):
        malus = fighter.combattant.lvl * 0.2
        fighter.stats.strength = max(1, fighter.stats.strength - malus)
        fighter.stats.agility = max(1, fighter.stats.agility - malus)
        fighter.stats.lethality = max(1, fighter.stats.lethality - malus)
        fighter.stats.viciousness = max(1, fighter.stats.viciousness - malus)
        return

class WarmUp(BuffFight):
    description:str = "Après 10 round, augmente toutes ses stats."
    description_en:str = ""
    def __init__(self, fighter:FightingBully|None = None):
        super().__init__()
        self.countdown = 10
        self.done = False
    def apply_defensive(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound):
        if not self.done : 
            if self.countdown > 0 :
                self.countdown -= 1
            else : 
                self.done = True
                fighter.stats.strength *= 2
                fighter.stats.agility *= 2
                fighter.stats.lethality *= 2
                fighter.stats.viciousness *= 2
        return

#41-50
class Venomous(BuffFight):
    description:str = "Ses coups critiques empoisonne son adversaire."
    description_en:str = "Poison enemy on critical strikes."
    def __init__(self, fighter:FightingBully|None = None):
        super().__init__()
    def apply_defensive(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound):
        if fighter == recap_round.attacker and recap_round.is_success_lethal :
            not_poisoned = len([b for b in opponent.buffs if isinstance(b, Poisoned)]) == 0
            if not_poisoned:
                opponent.buffs.append(Poisoned(difficulty=fighter.stats.lethality))
        return

class Scary(BuffFight):
    description:str = "Ses coups vicieux, même raté, peuvent hanter l'ennemi (Haunted Debuff)."
    description_en:str = "Vicious debuff can haunt the enemy."
    def __init__(self, fighter:FightingBully|None = None):
        super().__init__()
        self.proba = 0.3
    def apply_defensive(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound):
        if fighter == recap_round.attacker and recap_round.is_success_vicious and random.random() < self.proba:
            not_haunted = len([b for b in opponent.buffs if isinstance(b, Haunted)]) == 0
            if not_haunted:
                opponent.buffs.append(Haunted(fighter=opponent))
        return

class CrystalSkin(BuffFight):
    description:str = "Annule les dégâts supplémentaires des coups critiques."
    description_en:str = "Cancel bonus damage from critical strikes."
    def __init__(self, fighter:FightingBully|None = None):
        super().__init__()
    def apply_aggresive(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound)-> tuple[int, int] :
        if recap_round.damage_bonus_lethal > 0:
            dmg_bonus = recap_round.damage_bonus_lethal
            if recap_round.attacker == fighter :
                opponent.pv += dmg_bonus
                recap_round.damage_bonus_lethal = 0
                return -dmg_bonus, 0 
            if recap_round.attacker == opponent :
                fighter.pv += dmg_bonus
                recap_round.damage_bonus_lethal = 0
                return 0, -dmg_bonus
        return 0, 0

class ProtectiveShadow(BuffFight):
    description:str = "Au lieu de prendre des dégâts, diminue sa Viciousness. Ce buff disparait quand la Viciousness atteint 1."
    description_en:str = ""
    def __init__(self, fighter:FightingBully|None = None):
        super().__init__()
    def apply_defensive(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) :
        if recap_round.get_damage_receive(fighter) > 0:
            dmg = recap_round.get_damage_receive(fighter)
            fighter.pv += dmg
            fighter.stats.viciousness -= fighter.combattant.lvl
            if fighter.stats.viciousness <= 1 :
                fighter.stats.viciousness = 1
                fighter.buffs.remove(self)
        return

class DragonAscension(BuffFight):
    description:str = "Devient de plus en plus fort."
    description_en:str = ""
    def __init__(self, fighter:FightingBully|None = None):
        super().__init__()
    def apply_defensive(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound):
        bonus = fighter.combattant.lvl * 0.2
        fighter.stats.strength += bonus
        fighter.stats.agility += bonus
        fighter.stats.lethality += bonus
        fighter.stats.viciousness += bonus
        return

#Buff Negatif
class Poisoned(BuffFight):
    description:str = "Reçoit 1 dégât à chaque round. Peut disparaitre avec de la Strength."
    description_en:str = "Take damage every round. Can get rid of it with Strength."
    category:CategoryBuff = CategoryBuff.DEBUFF
    def __init__(self, fighter:FightingBully|None = None, difficulty = 1.0):
        super().__init__()
        self.difficulty = difficulty
    def apply_aggresive(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) -> tuple[int, int]:
        if Bully.clash_stat(st_actif = opponent.stats.strength, st_passif = self.difficulty) :
            fighter.buffs.remove(self)
        else :
            fighter.pv -= 1
        return 1, 0
    
class Haunted(BuffFight):
    description:str = "Les buffs sont désactivés jusqu'à la prochaine attaque réussit contre un ennemi."
    description_en:str = "Deactivate buffs until successfully hitting an enemy."
    category:CategoryBuff = CategoryBuff.DEBUFF
    def __init__(self, fighter:FightingBully|None = None):
        super().__init__()
        self.saved_buffs:list[BuffFight] = []
        if fighter is not None:
            for b in fighter.buffs:
                if not isinstance(b, Haunted):
                    self.saved_buffs.append(b)
            fighter.buffs = [self]
    def apply_defensive(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) :
        if fighter == recap_round.attacker and not recap_round.is_success_block:
            fighter.buffs = self.saved_buffs.copy()

#Special Buff (for special occasion)
class Friendship(BuffFight):
    description:str = "Tous tes amis t'adorent."
    description_en:str = "All your friends love you."
    category:CategoryBuff = CategoryBuff.SPECIAL

class Dragon(BuffFight):
    description:str = "Obtient tous les buffs Dragons"
    description_en:str = ""
    def __init__(self, fighter:FightingBully|None = None):
        super().__init__()
        if fighter is not None : 
            fighter.buffs = [DragonSkin(fighter=fighter), DragonResilience(fighter=fighter), DragonAscension(fighter=fighter)]
        else : 
            print("Fighter devrait être init")
    


#Unique Buff (for Unique character)
class Cat(BuffFight):
    description:str = "9 vies!"
    description_en:str = "Cats have 9 lives!"
    category:CategoryBuff = CategoryBuff.UNIQUE
    def __init__(self, fighter:FightingBully|None = None):
        super().__init__()
        self.vies = 9
    def apply_defensive(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound):
        if fighter.pv <= 0 and self.vies > 0:
            self.vies -= 1
            fighter.pv = fighter.combattant.max_pv
        return
class Vilain(BuffFight):
    description:str = "Augmente sa Viciousness quand l'ennemi subit un malus vicieux."
    description_en:str = "Increase Viciousness when the enemy suffers from a vicious attack."
    category:CategoryBuff = CategoryBuff.UNIQUE
    def __init__(self, fighter:FightingBully|None = None):
        super().__init__()
    def apply_defensive(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound):
        if fighter == recap_round.attacker and recap_round.is_success_vicious:
            fighter.stats.viciousness += recap_round.malus_vicious
        return
class SpaceCake(BuffFight):
    description:str = "Quand l'adversaire reçoit un coup, échange 2 de ses stats."
    description_en:str = "When striking an enemy, swap two of their stats."
    category:CategoryBuff = CategoryBuff.UNIQUE
    def __init__(self, fighter:FightingBully|None = None):
        super().__init__()
    def apply_defensive(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound):
        if fighter == recap_round.attacker and not recap_round.is_success_block:
            s1, s2 = random.sample(["strength", "agility", "viciousness", "lethality"], 2)
            v1, v2 = getattr(opponent.stats, s1), getattr(opponent.stats, s2)
            setattr(opponent.stats, s1, v2)
            setattr(opponent.stats, s2, v1)
        return
class SuppaFastAndFurious(BuffFight):
    description:str = "Attaque rapide = + de dégât."
    description_en:str = "Fast attacks = more damage."
    category:CategoryBuff = CategoryBuff.UNIQUE
    def __init__(self, fighter:FightingBully|None = None):
        super().__init__()
    def apply_aggresive(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) :
        if fighter == recap_round.attacker and recap_round.is_success_agility and not recap_round.is_success_block:
            opponent.pv -= 1
            return 0, 1
        return 0, 0
class StrangeGift(BuffFight):
    description:str = "Remplace les buffs de l'ennemi par du poison en mourrant."
    description_en:str = "On death, replace the enemy's buffs with a debuff."
    category:CategoryBuff = CategoryBuff.UNIQUE
    def __init__(self, fighter:FightingBully|None = None):
        super().__init__()
    def apply_defensive(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) :
        if fighter.pv <= 0:
            opponent.buffs = [Poisoned(difficulty=fighter.stats.viciousness)]
        return 
class Bombe(BuffFight):
    description:str = "Les coups qui l'achève le font exploser en infligeant 5 dégâts à son adversaire."
    description_en:str = "When struck to death, deal 5 damage to the enemy."
    category:CategoryBuff = CategoryBuff.UNIQUE
    def __init__(self, fighter:FightingBully|None = None):
        super().__init__()
    def apply_aggresive(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) :
        if fighter.pv <= 0:
            opponent.pv -= 5
            return 0, 5
        return 0, 0
    
