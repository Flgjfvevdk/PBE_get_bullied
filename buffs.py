from fighting_bully import BuffFight, FightingBully, RecapRound, CategoryBuff
from bully import Bully, Stats
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
    category:CategoryBuff = CategoryBuff.LVL_1
    def __init__(self, fighter:FightingBully):
        super().__init__(fighter)
    def apply_effect(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) :
        if fighter == recap_round.defender and recap_round.damage_receive_defender > 0:
            fighter.stats.strength += fighter.bully.lvl * 0.4
        return 
    
class LosingWeight(BuffFight):
    description:str = "À chaque dégât subit, augmente sa Agility."
    description_en:str = "When damaged, increase Agility."
    category:CategoryBuff = CategoryBuff.LVL_1
    def __init__(self, fighter:FightingBully):
        super().__init__(fighter)
    def apply_effect(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) :
        if fighter == recap_round.defender and recap_round.damage_receive_defender > 0:
            fighter.stats.agility += fighter.bully.lvl * 0.4
        return 
    
class AngerIssue(BuffFight):
    description:str = "À chaque dégât subit, augmente sa Lethality."
    description_en:str = "When damaged, increase Lethality."
    category:CategoryBuff = CategoryBuff.LVL_1
    def __init__(self, fighter:FightingBully):
        super().__init__(fighter)
    def apply_effect(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) :
        if fighter == recap_round.defender and recap_round.damage_receive_defender > 0:
            fighter.stats.lethality += fighter.bully.lvl * 0.4
        return 

class Brutal(BuffFight):
    description:str = "Augmente de 1 les dégâts de ses coups critiques."
    description_en:str = "Deals one more critical damage."
    category:CategoryBuff = CategoryBuff.LVL_1
    def __init__(self, fighter:FightingBully):
        super().__init__(fighter)
    def apply_damage(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) -> tuple[int, int]:
        if fighter == recap_round.attacker and recap_round.is_success_lethal:
            opponent.pv -= 1
            return 0, 1
        return 0, 0
    
class IronSkin(BuffFight):
    description:str = "Reçoit 1 dégât de moins des coups critiques."
    description_en:str = "Take one less critical damage."
    category:CategoryBuff = CategoryBuff.LVL_1
    def __init__(self, fighter:FightingBully):
        super().__init__(fighter)
    def apply_heal(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) -> tuple[int, int]:
        if fighter == recap_round.defender and recap_round.damage_bonus_lethal > 0 and recap_round.get_damage_receive(fighter) > 0:
            fighter.pv += 1
            recap_round.damage_bonus_lethal -= 1
            return 1, 0
        return 0,0

#11-20   
class SlimyPunch(BuffFight):
    description:str = "À chaque frappe réussie, réduit l'Agility de l'adversaire."
    description_en:str = "When the enemy is hit, their Agility is reduced."
    category:CategoryBuff = CategoryBuff.LVL_2
    def __init__(self, fighter:FightingBully):
        super().__init__(fighter)
    def apply_effect(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound):
        if fighter == recap_round.attacker and not recap_round.is_success_block:
            opponent.stats.agility *= 0.92
        return 
    
class SlimyBody(BuffFight):
    description:str = "À chaque coup subit, réduit l'Agility de l'adversaire."
    description_en:str = "When hit, reduce the enemy's Agility."
    category:CategoryBuff = CategoryBuff.LVL_2
    def __init__(self, fighter:FightingBully):
        super().__init__(fighter)
    def apply_effect(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound):
        if fighter == recap_round.defender and not recap_round.is_success_block:
            if (opponent.stats.agility > 1):
                opponent.stats.agility -= fighter.bully.lvl
                if opponent.stats.agility <= 1 :
                    opponent.stats.agility = 1
        return

class ThornSkin(BuffFight):
    description:str = "À chaque coup critique subit, renvoie 1 dégât à l'attaquant."
    description_en:str = "Deals damage to the attacker when hit by a critical strike."
    category:CategoryBuff = CategoryBuff.LVL_2
    def __init__(self, fighter:FightingBully):
        super().__init__(fighter)
    def apply_damage(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) :
        if fighter == recap_round.defender and recap_round.is_success_lethal:
            opponent.pv -= 1
            return 0, 1
        return 0, 0
  
class Frustration(BuffFight):
    description:str = "À chaque attaque raté, augmente sa Lethality."
    description_en:str = "When attack fails, increase Lethality."
    category:CategoryBuff = CategoryBuff.LVL_2
    def __init__(self, fighter:FightingBully):
        super().__init__(fighter)
    def apply_effect(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) :
        if fighter == recap_round.attacker and recap_round.is_success_block:
            fighter.stats.lethality += fighter.bully.lvl * 0.15
        return

class DragonSkin(BuffFight):
    description:str = "Peut bloquer 1 dégât. Augmente la probabilité à chaque coup donné."
    description_en:str = ""
    category:CategoryBuff = CategoryBuff.LVL_2
    def __init__(self, fighter:FightingBully):
        super().__init__(fighter)
        self.proba = 0.0
        self.description = f"{round(self.proba*100)}% de bloquer 1 dégât. Augmente la proba à chaque coup donné."
    def apply_heal(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) -> tuple[float, float] :
        if recap_round.attacker == fighter and not recap_round.is_success_block:
            self.proba = min(1.0, self.proba + 0.2)
            self.description = f"{round(self.proba*100)}% de bloquer 1 dégât. Augmente la proba à chaque coup donné."

        elif recap_round.defender == fighter and not recap_round.is_success_block and recap_round.get_damage_receive(fighter) > 0 and random.random() < self.proba:
            fighter.pv += 1
            self.proba = 0
            self.description = f"{round(self.proba*100)}% de bloquer 1 dégât. Augmente la proba à chaque coup donné."
            return 1, 0
        return 0,0
    
class ShadowEater(BuffFight):
    description:str = "Ses attaques réussies augmente sa Viciousness."
    description_en:str = ""
    category:CategoryBuff = CategoryBuff.LVL_2
    def __init__(self, fighter:FightingBully):
        super().__init__(fighter)
    def apply_effect(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) :
        if recap_round.attacker == fighter and not recap_round.is_success_block:
            fighter.stats.viciousness += fighter.bully.lvl * 0.25
        return 
    

#21-30  
class RoyalSlimyBody(BuffFight):
    description:str = "À chaque attaque bloqué, réduit l'Agility de l'attaquant."
    description_en:str = "When blocking an attack, reduce the enemy's Agility."
    category:CategoryBuff = CategoryBuff.LVL_3
    def __init__(self, fighter:FightingBully):
        super().__init__(fighter)
    def apply_effect(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound):
        if fighter == recap_round.defender and recap_round.is_success_block:
            opponent.stats.agility *= 0.96
        return 

class RootOfEvil(BuffFight):
    description:str = "Attaque vicieuse subit => augmentation Viciousness."
    description_en:str = "When get vicious debuff, increase your Viciousness."
    category:CategoryBuff = CategoryBuff.LVL_3
    def __init__(self, fighter:FightingBully):
        super().__init__(fighter)
    def apply_effect(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) :
        if fighter == recap_round.defender and recap_round.is_success_vicious:
            fighter.stats.viciousness += recap_round.malus_vicious
        return 

class GoldenSkin(BuffFight):
    description:str = "Ne peut pas recevoir plus de 2 dégâts en 1 round."
    description_en:str = "Can't receive more than 2 damages at once."
    category:CategoryBuff = CategoryBuff.LVL_3
    def __init__(self, fighter:FightingBully):
        super().__init__(fighter)
    def apply_heal(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) -> tuple[float, float]:
        if recap_round.get_damage_receive(fighter) > 2:
            heal = recap_round.get_damage_receive(fighter) - 2
            fighter.pv += heal
            return heal, 0
        return 0,0
    
class SharpTeeth(BuffFight):
    description:str = "Ses coups critiques diminuent la Strength de l'adversaire."
    description_en:str = ""
    category:CategoryBuff = CategoryBuff.LVL_3
    def __init__(self, fighter:FightingBully):
        super().__init__(fighter)
    def apply_effect(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound):
        if fighter == recap_round.attacker and recap_round.is_success_lethal:
            opponent.stats.strength *= 0.9
        return 

class DragonResilience(BuffFight):
    description:str = "Attaque vicieuse subit => augmentation Strength."
    description_en:str = ""
    category:CategoryBuff = CategoryBuff.LVL_3
    def __init__(self, fighter:FightingBully):
        super().__init__(fighter)
    def apply_effect(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound):
        if fighter == recap_round.defender and recap_round.is_success_vicious:
            fighter.stats.strength += recap_round.malus_vicious*0.6
        return

#31-40
class Lycanthropy(BuffFight):
    description:str = "Échange la Lethality et la Viciousness selon les HP de l'adversaire. Buff la Lethality"
    description_en:str = "Swap Lethality and Viciousness depending on enemy's HP."
    category:CategoryBuff = CategoryBuff.LVL_4
    def __init__(self, fighter:FightingBully):
        super().__init__(fighter)
        fighter.stats.lethality += fighter.bully.lvl * 2
    def before_fight(self, fighter: FightingBully, opponent: FightingBully):
        self.swap_stat_if_needed(fighter, opponent)
    def apply_effect(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) :
        self.swap_stat_if_needed(fighter, opponent)
        return 
    
    def swap_stat_if_needed(self, fighter: FightingBully, opponent: FightingBully):
        best_s = max(fighter.stats.lethality, fighter.stats.viciousness)
        worst_s = min(fighter.stats.lethality, fighter.stats.viciousness)
        if opponent.pv < opponent.bully.max_pv / 2:
            fighter.stats.lethality = best_s
            fighter.stats.viciousness = worst_s
        else:
            fighter.stats.lethality = worst_s
            fighter.stats.viciousness = best_s

class Vampire(BuffFight):
    description:str = "À chaque coup vicieux blessant l'adversaire, régénère 1 HP. Buff la Viciousness"
    description_en:str = "When deal vicious damage on the enemy, regen HP."
    category:CategoryBuff = CategoryBuff.LVL_4
    def __init__(self, fighter:FightingBully):
        super().__init__(fighter)
        fighter.stats.viciousness += fighter.bully.lvl * 1.5
    def apply_heal(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) -> tuple[int, int]:
        if fighter == recap_round.attacker and not recap_round.is_success_block and recap_round.is_success_vicious:
            heal = 1 if fighter.pv + 1 <= fighter.bully.max_pv else 0
            fighter.pv += heal
            return heal, 0
        return 0,0

class LastWhisper(BuffFight):
    description:str = "Augmente toutes ses stats après avoir perdu la moitié de ses HP."
    description_en:str = "Increase stats when below half HP."
    category:CategoryBuff = CategoryBuff.LVL_4
    def __init__(self, fighter:FightingBully):
        super().__init__(fighter)
        self.first_stage = True
    def apply_effect(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound):
        if self.first_stage and fighter.pv <= fighter.bully.max_pv / 2:
            fighter.stats.strength += fighter.bully.lvl * 1.5
            fighter.stats.agility += fighter.bully.lvl * 1.5
            self.first_stage = False
        return

class Overdrive(BuffFight):
    description:str = "Commence avec des gros buffs de stats mais s'essouffle peu à peu."
    description_en:str = ""
    category:CategoryBuff = CategoryBuff.LVL_4
    def __init__(self, fighter:FightingBully):
        super().__init__(fighter)
        bonus = fighter.bully.lvl * 3
        fighter.stats.strength += bonus
        fighter.stats.agility += bonus
        fighter.stats.lethality += bonus
        fighter.stats.viciousness += bonus
    def apply_effect(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound):
        malus = fighter.bully.lvl * 0.2
        fighter.stats.strength = max(1, fighter.stats.strength - malus)
        fighter.stats.agility = max(1, fighter.stats.agility - malus)
        fighter.stats.lethality = max(1, fighter.stats.lethality - malus)
        fighter.stats.viciousness = max(1, fighter.stats.viciousness - malus)
        return

class WarmUp(BuffFight):
    description:str = "Après 10 round, augmente toutes ses stats."
    description_en:str = ""
    category:CategoryBuff = CategoryBuff.LVL_4
    def __init__(self, fighter:FightingBully):
        super().__init__(fighter)
        self.countdown = 10
        self.done = False
    def apply_effect(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound):
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
    category:CategoryBuff = CategoryBuff.LVL_5
    def __init__(self, fighter:FightingBully):
        super().__init__(fighter)
    def apply_effect(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound):
        if fighter == recap_round.attacker and recap_round.is_success_lethal :
            not_poisoned = len([b for b in opponent.buffs if isinstance(b, Poisoned)]) == 0
            if not_poisoned:
                opponent.buffs.append(Poisoned(fighter= opponent, difficulty=fighter.stats.lethality))
        return

# class Scary(BuffFight):
#     description:str = "Ses coups vicieux, même raté, peuvent hanter l'ennemi (Haunted Debuff)."
#     description_en:str = "Vicious debuff can haunt the enemy."
#     category:CategoryBuff = CategoryBuff.LVL_5
#     def __init__(self, fighter:FightingBully):
#         super().__init__(fighter)
#         self.proba = 0.3
#     def apply_effect(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound):
#         if fighter == recap_round.attacker and recap_round.is_success_vicious and random.random() < self.proba:
#             not_haunted = len([b for b in opponent.buffs if isinstance(b, Haunted)]) == 0
#             if not_haunted:
#                 opponent.buffs.append(Haunted(fighter=opponent))
#         return

class CrystalSkin(BuffFight):
    description:str = "Annule les dégâts supplémentaires des coups critiques."
    description_en:str = "Cancel bonus damage from critical strikes."
    category:CategoryBuff = CategoryBuff.LVL_5
    def __init__(self, fighter:FightingBully):
        super().__init__(fighter)
    def apply_damage(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound)-> tuple[int, int] :
        if recap_round.damage_bonus_lethal > 0:
            dmg_bonus = recap_round.damage_bonus_lethal
            if recap_round.attacker == fighter :
                heal = min(dmg_bonus, max(0, recap_round.get_damage_receive(opponent)))
                opponent.pv += heal
                recap_round.damage_bonus_lethal = 0
                return -heal, 0 
            if recap_round.attacker == opponent :
                heal = min(dmg_bonus, recap_round.get_damage_receive(fighter))
                fighter.pv += heal
                recap_round.damage_bonus_lethal = 0
                return 0, -heal
        return 0, 0

class ProtectiveShadow(BuffFight):
    description:str = "Au lieu de prendre des dégâts, diminue sa Viciousness. Ce buff disparait quand la Viciousness atteint 1."
    description_en:str = ""
    category:CategoryBuff = CategoryBuff.LVL_5
    def __init__(self, fighter:FightingBully):
        super().__init__(fighter)
    def apply_effect(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) :
        if recap_round.get_damage_receive(fighter) > 0:
            dmg = recap_round.get_damage_receive(fighter)
            fighter.pv += dmg
            fighter.stats.viciousness -= fighter.bully.lvl
            if fighter.stats.viciousness <= 1 :
                fighter.stats.viciousness = 1
                fighter.buffs.remove(self)
        return

class DragonAscension(BuffFight):
    description:str = "Devient de plus en plus fort."
    description_en:str = ""
    category:CategoryBuff = CategoryBuff.LVL_5
    def __init__(self, fighter:FightingBully):
        super().__init__(fighter)
    def apply_effect(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound):
        bonus = fighter.bully.lvl * 0.15
        fighter.stats.strength += bonus
        fighter.stats.agility += bonus
        fighter.stats.lethality += bonus
        fighter.stats.viciousness += bonus
        return

#Team Buffs
class ToxicTeam(BuffFight):
    description:str = "Les coups vicieux bloqués font 1 dégât."
    description_en:str = ""
    category:CategoryBuff = CategoryBuff.TEAM
    def __init__(self, fighter:FightingBully):
        super().__init__(fighter)
    def apply_damage(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) -> tuple[int, int]:
        if fighter == recap_round.attacker and recap_round.is_success_vicious and recap_round.is_success_block:
            opponent.pv -= 1
            return 0, 1
        return 0, 0

class MonsterTeam(BuffFight):
    description:str = "Se soigne de 1 HP en faisant un coup critique."
    description_en:str = ""
    category:CategoryBuff = CategoryBuff.TEAM
    def __init__(self, fighter:FightingBully):
        super().__init__(fighter)
    def apply_heal(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) -> tuple[int, int]:
        if fighter == recap_round.attacker and recap_round.is_success_lethal and fighter.pv + 1 <= fighter.bully.max_pv:
            fighter.pv += 1
            return 1, 0
        return 0, 0

class DevastatorTeam(BuffFight):
    description:str = "Les coups non critiques font 1 dégât supplémentaire."
    description_en:str = ""
    category:CategoryBuff = CategoryBuff.TEAM
    def __init__(self, fighter:FightingBully):
        super().__init__(fighter)
    def apply_damage(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) -> tuple[int, int]:
        if fighter == recap_round.attacker and not recap_round.is_success_lethal and not recap_round.is_success_block:
            opponent.pv -= 1
            return 0, 1
        return 0, 0
    
class SublimeTeam(BuffFight):
    description:str = "Commence les combats avec 2 pv supplémentaire."
    description_en:str = ""
    category:CategoryBuff = CategoryBuff.TEAM
    def __init__(self, fighter:FightingBully):
        super().__init__(fighter)
        fighter.pv += 2

#Buff Negatif
class Poisoned(BuffFight):
    description:str = "Reçoit 1 dégât à chaque round. Peut disparaitre avec de la Strength."
    description_en:str = "Take damage every round. Can get rid of it with Strength."
    category:CategoryBuff = CategoryBuff.DEBUFF
    def __init__(self, fighter:FightingBully, difficulty = 1.0):
        super().__init__(fighter)
        self.difficulty = difficulty
    def apply_damage(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) -> tuple[int, int]:
        if Bully.clash_stat(st_actif = opponent.stats.strength, st_passif = self.difficulty) :
            fighter.buffs.remove(self)
        else :
            fighter.pv -= 1
            return 1, 0
        return 0, 0
    
# class Haunted(BuffFight):
#     description:str = "Les buffs sont désactivés jusqu'à la prochaine attaque réussie contre un ennemi."
#     description_en:str = "Deactivate buffs until successfully hitting an enemy."
#     category:CategoryBuff = CategoryBuff.DEBUFF
#     def __init__(self, fighter:FightingBully):
#         super().__init__(fighter)
#         self.saved_buffs:list[BuffFight] = []
#         for b in fighter.buffs:
#             if not isinstance(b, Haunted):
#                 self.saved_buffs.append(b)
#         fighter.buffs = [self]
#     def apply_effect(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) :
#         if fighter == recap_round.attacker and not recap_round.is_success_block:
#             fighter.buffs = self.saved_buffs.copy()

class Dizzy(BuffFight):
    description:str = "Agility divisé par 2 pendant 1 round."
    description_en:str = ""
    category:CategoryBuff = CategoryBuff.DEBUFF
    def __init__(self, fighter:FightingBully):
        super().__init__(fighter)
        self.malus = fighter.stats.agility*0.5
        fighter.stats.agility -= self.malus
    def apply_effect(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) :
        fighter.stats.agility += self.malus
        fighter.buffs.remove(self)
        return 
 
class Burning(BuffFight):
    description:str = "Reçoit X dégât à chaque round. Diminue le compteur à chaque tour."
    category:CategoryBuff = CategoryBuff.DEBUFF
    def __init__(self, fighter:FightingBully, compteur = 1):
        super().__init__(fighter)
        self.compteur:int = compteur
        self.update_description()
    def apply_damage(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) -> tuple[int, int]:
        if self.compteur > 0 : 
            damage = self.compteur
            fighter.pv -= damage

            self.compteur -= 1
            self.update_description()
            # if self.compteur <= 0 : 
            #     fighter.buffs.remove(self)
            return damage, 0
        return 0, 0
    
    def update_description(self):
        self.description = f"Reçoit {self.compteur} dégâts à chaque round et diminue cette valeur."

    def add_compteur(self, val:int):
        self.compteur += val
        self.update_description()


#Special Buff (for special occasion)
class Friendship(BuffFight):
    description:str = "Tous tes amis t'adorent."
    description_en:str = "All your friends love you."
    category:CategoryBuff = CategoryBuff.SPECIAL

class Dragon(BuffFight):
    description:str = "Obtient tous les buffs Dragons"
    description_en:str = ""
    category:CategoryBuff = CategoryBuff.SPECIAL
    def __init__(self, fighter:FightingBully):
        super().__init__(fighter)
        fighter.buffs = [DragonSkin(fighter=fighter), DragonResilience(fighter=fighter), DragonAscension(fighter=fighter)]

class ShadowMaster(BuffFight):
    description:str = "Obtient tous les buffs Shadows"
    description_en:str = ""
    category:CategoryBuff = CategoryBuff.SPECIAL
    def __init__(self, fighter:FightingBully):
        super().__init__(fighter)
        fighter.buffs = [ShadowEater(fighter=fighter), ProtectiveShadow(fighter=fighter)]

class Adaptation(BuffFight):
    description:str = "Level up jusqu'à atteindre le level de son adversaire."
    category:CategoryBuff = CategoryBuff.SPECIAL
    # def __init__(self, fighter:FightingBully):
    #     super().__init__(fighter)
    def before_fight(self, fighter: FightingBully, opponent: FightingBully):
        for l in range(fighter.bully.lvl, opponent.bully.lvl):
            old_base_stat = fighter.base_stats
            fighter.bully.level_up_one()
            added_stats = fighter.bully.stats - old_base_stat
            fighter.base_stats += added_stats
            fighter.stats += added_stats



#Unique Buff (for Unique character)
class Cat(BuffFight):
    description:str = "9 vies !"
    description_en:str = "Cats have 9 lives!"
    category:CategoryBuff = CategoryBuff.UNIQUE
    def __init__(self, fighter:FightingBully):
        super().__init__(fighter)
        self.description:str = "9 vies !"
        self.vies = 9
    def on_death(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound):
        if fighter.pv <= 0 and self.vies > 0:
            self.vies -= 1
            self.description = f"{self.vies} vie{'s' if self.vies>1 else ''} !"
            fighter.pv = fighter.bully.max_pv
        return
class Vilain(BuffFight):
    description:str = "Augmente sa Viciousness quand l'ennemi subit un malus vicieux."
    description_en:str = "Increase Viciousness when the enemy suffers from a vicious attack."
    category:CategoryBuff = CategoryBuff.UNIQUE
    def __init__(self, fighter:FightingBully):
        super().__init__(fighter)
    def apply_effect(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound):
        if fighter == recap_round.attacker and recap_round.is_success_vicious:
            fighter.stats.viciousness += recap_round.malus_vicious
        return
class SpaceCake(BuffFight):
    description:str = "Quand l'adversaire reçoit un coup, échange 2 de ses stats."
    description_en:str = "When striking an enemy, swap two of their stats."
    category:CategoryBuff = CategoryBuff.UNIQUE
    def __init__(self, fighter:FightingBully):
        super().__init__(fighter)
    def apply_effect(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound):
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
    def __init__(self, fighter:FightingBully):
        super().__init__(fighter)
    def apply_damage(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) :
        if fighter == recap_round.attacker and recap_round.is_success_agility and not recap_round.is_success_block:
            opponent.pv -= 1
            return 0, 1
        return 0, 0
class StrangeGift(BuffFight):
    description:str = "Remplace les buffs de l'ennemi par du poison en mourrant."
    description_en:str = "On death, replace the enemy's buffs with a debuff."
    category:CategoryBuff = CategoryBuff.UNIQUE
    def __init__(self, fighter:FightingBully):
        super().__init__(fighter)
    def on_death(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) :
        if fighter.pv <= 0:
            opponent.buffs = [Poisoned(fighter=opponent, difficulty=fighter.stats.viciousness)]
        return 
class ExplosiveTouch(BuffFight):
    description:str = "Les blocages et attaques réussient inflige 1 dégât à tous."
    description_en:str = ""
    category:CategoryBuff = CategoryBuff.UNIQUE
    def apply_damage(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) :
        if fighter == recap_round.defender and recap_round.is_success_block:
            fighter.pv -= 1
            opponent.pv -= 1
            return 1, 1
        elif fighter == recap_round.attacker and not recap_round.is_success_block:
            fighter.pv -= 1
            opponent.pv -= 1
            return 1, 1
        return 0, 0
class Parrain(BuffFight):
    description:str = "Ses coups critiques rendent l'ennemi Dizzy (malus Agility pendant 1 tour)."
    description_en:str = ""
    category:CategoryBuff = CategoryBuff.UNIQUE
    def apply_effect(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound):
        if fighter == recap_round.attacker and recap_round.is_success_lethal :
            opponent.buffs.append(Dizzy(fighter = opponent))
        return

#Pour le phoenix
class FireAura(BuffFight):
    description:str = "Inflige 1 dégât à l'adversaire."
    category:CategoryBuff = CategoryBuff.UNIQUE
    def __init__(self, fighter:FightingBully, tour_restant=math.inf):
        super().__init__(fighter)
        self.tour = tour_restant
        if self.tour < math.inf:
            self.description = f"Inflige 1 dégât à l'adversaire [{self.tour} tours restants]"
    def apply_damage(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) :
        opponent.pv -= 1
        self.tour -= 1
        if self.tour < math.inf:
            self.description = f"Inflige 1 dégât à l'adversaire [{self.tour} tours restants]"
        if self.tour <= 0 :
            fighter.buffs.remove(self)
        return 0, 1
class FirePunch(BuffFight) :
    description:str = "Ses coups critiques brulent l'adversaire."
    category:CategoryBuff = CategoryBuff.UNIQUE
    def apply_effect(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound):
        if fighter == recap_round.attacker and recap_round.is_success_lethal :
            burn_defuffs = [b for b in opponent.buffs if isinstance(b, Burning)]
            if len(burn_defuffs) == 0:
                opponent.buffs.append(Burning(fighter= opponent, compteur=2))
            else :
                burn_defuffs[0].add_compteur(2)

            if recap_round.damage_bonus_lethal > 0:
                dmg_bonus = recap_round.damage_bonus_lethal
                heal = min(dmg_bonus, recap_round.get_damage_receive(opponent))
                opponent.pv += heal
                recap_round.damage_bonus_lethal = 0
                    
        return
class Phoenix(BuffFight):
    description:str = "Renaît de ses cendres dans une aura de feu."
    category:CategoryBuff = CategoryBuff.SPECIAL
    def on_death(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound):
        if fighter.pv <= 0 :
            fighter.pv = 5
            fighter.buffs.remove(self)
            fighter.buffs.append(FireAura(fighter, 3))
        return
    
#Pour le Diable
class DevilDeal(BuffFight):
    description:str = "Force l'adversaire a vendre son âme."
    category:CategoryBuff = CategoryBuff.UNIQUE
    def __init__(self, fighter:FightingBully):
        super().__init__(fighter)
        self.name = "Devil's Deal"
        self.deal_done = False
    def before_fight(self, fighter: FightingBully, opponent: FightingBully):
        if not self.deal_done and len([b for b in opponent.buffs if isinstance(b, YourSoulIsMine)]) == 0:
            self.description:str = "DEAL !"
            opponent.buffs.append(YourSoulIsMine(opponent))
            # fighter.buffs.remove(self)
            self.deal_done = True
    def on_death(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) -> None:
        if not self.deal_done : fighter.pv = 1
class YourSoulIsMine(BuffFight):
    description:str = "N'a plus d'âme. Meurt dans quelques rounds."
    category:CategoryBuff = CategoryBuff.UNIQUE
    max_round = 10
    def __init__(self, fighter:FightingBully):
        super().__init__(fighter)
        self.round = self.max_round
        self.description:str = f"N'a plus d'âme. Meurt dans {self.round} rounds."
    def apply_effect(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) -> None:
        if self.round <= 0 :
            fighter.pv = 0
        else : 
            self.round -= 1
            self.description:str = f"Meurt dans {self.round} rounds."
class FinalCountdown(BuffFight):
    description:str = "Tue l'adversaire dans quelques rounds."
    category:CategoryBuff = CategoryBuff.UNIQUE
    max_round = 10
    def __init__(self, fighter:FightingBully):
        super().__init__(fighter)
        self.round = self.max_round
        self.description:str = f"Tue l'adversaire dans {self.round} rounds."
    def apply_effect(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) -> None:
        if self.round <= 0 :
            opponent.pv = 0
            self.round = self.max_round
        else : 
            self.round -= 1
            self.description:str = f"Tue l'adversaire dans {self.round} rounds."
class DevilMinion(BuffFight):
    description:str = "Vole des stats aux adversaires avec un âme."
    category:CategoryBuff = CategoryBuff.UNIQUE
    def __init__(self, fighter:FightingBully):
        super().__init__(fighter)
        self.name = "Devil's Minion"
    def apply_effect(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound):
        if len([b for b in opponent.buffs if isinstance(b, YourSoulIsMine)]) == 0:
            drain_val = fighter.bully.lvl * 0.15
            fighter.stats.strength += drain_val
            fighter.stats.agility += drain_val
            fighter.stats.lethality += drain_val
            fighter.stats.viciousness += drain_val

            opponent.stats.strength = max(1, opponent.stats.strength - drain_val)
            opponent.stats.agility = max(1, opponent.stats.agility - drain_val)
            opponent.stats.lethality = max(1, opponent.stats.lethality - drain_val)
            opponent.stats.viciousness = max(1, opponent.stats.viciousness - drain_val)

class DevilPocketWatch(BuffFight):
    description:str = "Inflige régulièrement des dégâts à l'adversaire."
    category:CategoryBuff = CategoryBuff.UNIQUE
    max_round = 3
    base_damage = 1
    buffed_damage = 2
    def __init__(self, fighter:FightingBully):
        super().__init__(fighter)
        self.name = "Devil's Pocket Watch"
        self.round = self.max_round
        self.description:str = f"Inflige entre {self.base_damage} et {self.buffed_damage} dégâts dans {self.round} rounds."
    def apply_damage(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) :
        if self.round <= 0 :
            dmg = self.compute_damage(fighter.stats.viciousness, opponent.stats.viciousness)
            opponent.pv -= dmg
            self.round = self.max_round
            return 0, dmg
        else : 
            self.round -= 1
            self.description:str = f"Inflige {self.compute_damage(fighter.stats.viciousness, opponent.stats.viciousness)} dégâts dans {self.round} rounds."
        return 0, 0
    def compute_damage(self, viciousness:float, opponent_viciousness:float) -> int:
        if viciousness > opponent_viciousness :
            return self.buffed_damage
        else : 
            return self.base_damage

class OriginalSin(BuffFight):
    description:str = "Se transforme en serpent à la place de mourir."
    category:CategoryBuff = CategoryBuff.UNIQUE

    def on_death(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) -> None:
        if fighter.pv <= 0 :
            fighter.buffs.remove(self)
            fighter.pv = 5
            coef = fighter.bully.lvl * (fighter.bully.lvl + 1) / 2
            fighter.base_stats = Stats(1, 10 + 1.6*coef, 1, 10 + 2*coef)
            fighter.stats = Stats(1, 10 + 1.6*coef, 1, 10 + 2*coef)

            snake_buff = BuffFight(fighter)
            snake_buff.name = "Shapeshifter"
            snake_buff.description = "Sous forme de serpent."
            fighter.buffs.append(snake_buff)

#Pour le BG
class TooPerfect(BuffFight):
    description:str = "Annule les attaques vicieuses."
    category:CategoryBuff = CategoryBuff.UNIQUE
    def apply_effect(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) :
        if recap_round.is_success_vicious:
            if opponent == recap_round.attacker:
                if hasattr(fighter.stats, recap_round.vicious_target_str):
                    current_value = getattr(fighter.stats, recap_round.vicious_target_str)
                    new_value = current_value + recap_round.malus_vicious
                    setattr(fighter.stats, recap_round.vicious_target_str, new_value)
            else : 
                if hasattr(opponent.stats, recap_round.vicious_target_str):
                    current_value = getattr(opponent.stats, recap_round.vicious_target_str)
                    new_value = current_value + recap_round.malus_vicious
                    setattr(opponent.stats, recap_round.vicious_target_str, new_value)
        return
    
class PerfectSkin(BuffFight):
    description:str = "Annule buffs négatifs à chaque round."
    category:CategoryBuff = CategoryBuff.UNIQUE
    def apply_effect(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound) :
        for b in fighter.buffs:
            if isinstance(b, BuffFight) and b.category == CategoryBuff.DEBUFF:
                fighter.buffs.remove(b)
        return
    



import inspect, buffs
classes = [member[1] for member in inspect.getmembers(buffs) if inspect.isclass(member[1])]
name_to_buffs_class:dict[str, type[BuffFight]] = {}
for buffClass in classes :
    if issubclass(buffClass, BuffFight):
        if buffClass != BuffFight:
            name_to_buffs_class[buffClass.__name__] = buffClass







