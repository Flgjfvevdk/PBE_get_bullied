from __future__ import annotations # Replace type hints to their string form (Item => "Item"), which resolves circular dependencies
                                   # WARNING: Should only be used for type hints
from dataclasses import dataclass, replace
from bully import Bully, Stats
        
class BuffFight():
    def __init__(self):
        self.name:str = self.__class__.__name__
        self.description:str = "No buff"
        # Ajouter variable si variables nécessaires
    def apply_aggresive(self, fighter:FightingBully, opponent:FightingBully, recap_round:RecapRound) -> tuple[int, int]:
        """ For buff that could deal damage to a fighter.
        Return : 
            - damage_self, damage_opponent. damage_self = damage this buff done to self. damage_opponent = damage this buff done to opponent. Use to update recap_round
        """
        return 0, 0
    def apply_defensive(self, fighter:FightingBully, opponent:FightingBully, recap_round:RecapRound) -> None:
        """For buff that use damage infos as conditions."""
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
        fighter = FightingBully(combattant=b, pv=b.max_pv, base_stats=replace(b.stats), stats=replace(b.stats), buff=create_buff_instance(b.buff_fight_tag))
        return fighter
    
    def reset_stats(self) -> None:
        self.stats = replace(self.base_stats)


class RecapRound():
    def __init__(self, attacker:FightingBully, defender:FightingBully, is_success_agility:bool, is_success_block:bool, is_success_lethal:bool, is_success_vicious:bool
                 , damage_receive:int, malus_vicious:float = 0):
        self.attacker = attacker
        self.defender = defender

        self.is_success_agility = is_success_agility #Vrai si l'attaquant attaque car il a volé le tour du défenseur
        self.is_success_block = is_success_block
        self.is_success_lethal = is_success_lethal
        self.is_success_vicious = is_success_vicious

        self.damage_receive_attacker = 0 #Les dégâts reçus.
        self.damage_receive_defender = damage_receive #Les dégâts reçus.

        self.malus_vicious = malus_vicious
    
    def add_damage_receive(self, fighter:FightingBully, added_value:int):
        if fighter == self.attacker:
            self.damage_receive_attacker += added_value
        elif fighter == self.defender:
            self.damage_receive_defender += added_value

    def get_damage_receive(self, fighter:FightingBully) -> int:
        if fighter == self.attacker:
            return self.damage_receive_attacker
        elif fighter == self.defender:
            return self.damage_receive_defender
        else : 
            raise Warning("Input fighter is neither attacker nor defender")
            return 0

def create_buff_instance(class_name: str):
    import buffs
    # Cherche la classe dans le module
    try:
        buff_class = getattr(buffs, class_name)
        return buff_class()  # Crée une instance de la classe
    except AttributeError:
        raise ValueError(f"La classe {class_name} n'existe pas dans le module.")
