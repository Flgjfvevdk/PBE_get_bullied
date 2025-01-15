from __future__ import annotations # Replace type hints to their string form (Item => "Item"), which resolves circular dependencies
                                   # WARNING: Should only be used for type hints
from dataclasses import dataclass, replace, field
from bully import Bully, Stats, Rarity
from enum import Enum
import player_info

class CategoryBuff(Enum):
    NONE = 0
    LVL_1 = 1
    LVL_2 = 2
    LVL_3 = 3
    LVL_4 = 4
    LVL_5 = 5
    DEBUFF = -1
    TEAM = -2
    SPECIAL = -3
    UNIQUE = -4

class BuffFight():
    description:str = "No buff"
    description_en:str =""
    category:CategoryBuff = CategoryBuff.NONE
    def __init__(self, fighter:FightingBully):
        self.name:str = self.__class__.__name__
        # Ajouter variable si variables nécessaires
    def before_fight(self, fighter:FightingBully, opponent:FightingBully):
        """For buff that need an init with knowledge of the opponent"""
        return
    def apply_damage(self, fighter:FightingBully, opponent:FightingBully, recap_round:RecapRound) -> tuple[int, int]:
        """ For buff that could deal damage to a fighter.
        Return : 
            - damage_self, damage_opponent. damage_self = damage this buff done to self. damage_opponent = damage this buff done to opponent. Use to update recap_round
        """
        return 0, 0
    def apply_heal(self, fighter:FightingBully, opponent:FightingBully, recap_round:RecapRound) -> tuple[int, int]:
        """ For buff that could heal a fighter.
        Return : 
            - heal_self, heal_opponent. heal_self = heal this buff done to self. heal_opponent = heal this buff done to opponent. Use to update recap_round
        """
        return 0, 0
    def apply_effect(self, fighter:FightingBully, opponent:FightingBully, recap_round:RecapRound) -> None:
        """For buff that use damage infos as conditions."""
        return
    def on_death(self, fighter:FightingBully, opponent:FightingBully, recap_round:RecapRound) -> None:
        """For buff that use self death as conditions."""
        return
    
@dataclass
class FightingBully():
    bully: Bully
    pv: int
    base_stats: Stats
    stats: Stats
    buffs:list[BuffFight] = field(default_factory=lambda: [])

    @staticmethod
    def create_fighting_bully(b:Bully) -> "FightingBully":
        fighter = FightingBully(bully=b, pv=b.max_pv, base_stats=replace(b.stats), stats=replace(b.stats))#, buffs=create_buff_instance(b.buff_fight_tag))
        if (b.buff_fight_tag != "NoBuff"):
            fighter.buffs.append(create_buff_instance(b.buff_fight_tag, fighter=fighter))
        return fighter
    
    def set_buffs(self, buffs_tags:list[str] = []):
        self.buffs = []
        for b_tag in buffs_tags:
            self.buffs.append(create_buff_instance(b_tag, fighter=self))

    def reset_stats(self) -> None:
        self.stats = replace(self.base_stats)

    def copy(self)-> 'FightingBully':
        fb = FightingBully(bully=self.bully, pv = self.pv, base_stats=replace(self.base_stats), stats=replace(self.stats), buffs=(self.buffs).copy())
        return fb

    def get_print(self) -> str:
        text = ""
        hp_text = f"HP : {self.pv}/{self.bully.max_pv}"
        buff_text = self.buffs_str()
        def good_print_float(x:float) -> float|int:
            xf:float = float(x)
            return int(xf) if xf.is_integer() else round(xf, 1)
        text += self.bully.name + " | lvl : " + str(self.bully.lvl) + " | Rarity : " + self.bully.rarity.name + " | " + hp_text + " | " + buff_text + "\n\t" 
        text += " |S : "+ str(good_print_float(self.stats.strength))
        text += " |A : "+ str(good_print_float(self.stats.agility))
        text += " |L : "+ str(good_print_float(self.stats.lethality))
        text += " |V : "+ str(good_print_float(self.stats.viciousness))
        return text

    def buffs_str(self):
        text = ""
        if len(self.buffs) > 0:
            text +="Buff : "
        for b in self.buffs :
            text+= b.name
            text += " ; "
        return text

class RecapRound():
    def __init__(self, attacker:FightingBully, defender:FightingBully, is_success_agility:bool, is_success_block:bool, is_success_lethal:bool, is_success_vicious:bool
                 , damage_receive:int, malus_vicious:float = 0, damage_bonus_lethal:int = 0, vicious_target_str:str =""):
        self.attacker = attacker
        self.defender = defender

        self.is_success_agility = is_success_agility #Vrai si l'attaquant attaque car il a volé le tour du défenseur
        self.is_success_block = is_success_block
        self.is_success_lethal = is_success_lethal
        self.is_success_vicious = is_success_vicious

        self.damage_bonus_lethal = damage_bonus_lethal
        self.damage_receive_attacker = 0 
        self.damage_receive_defender = damage_receive

        self.malus_vicious = malus_vicious
        self.vicious_target_str:str = vicious_target_str
    
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

def get_player_team(player:player_info.Player, is_team_buff_active = True):
    fighters:list[FightingBully] = []
    compteur_rarity:dict[Rarity, int] = {r:0 for r in Rarity}
    for b in player.get_equipe():
        new_fighter = FightingBully.create_fighting_bully(b)
        fighters.append(new_fighter)
        compteur_rarity[b.rarity] += 1
    if is_team_buff_active:
        team_buff_tag:str|None = None
        if compteur_rarity[Rarity.TOXIC] >= 3:
            team_buff_tag = "ToxicTeam"
        elif compteur_rarity[Rarity.MONSTER] >= 3:
            team_buff_tag = "MonsterTeam"
        elif compteur_rarity[Rarity.DEVASTATOR] >= 3:
            team_buff_tag = "DevastatorTeam"
        elif compteur_rarity[Rarity.SUBLIME] >= 3:
            team_buff_tag = "SublimeTeam"
        if team_buff_tag is not None:
            for f in fighters:
                f.buffs.append(create_buff_instance(team_buff_tag, fighter=f))
    return fighters

def create_buff_instance(buff_name: str, fighter:FightingBully) -> BuffFight: 
    import buffs
    # Cherche la classe dans le module
    try:
        BuffClass = buffs.name_to_buffs_class[buff_name]
        return BuffClass(fighter=fighter)
    except KeyError as e :
        print(f"Le buff du bully est invalide [{buff_name}]")
        return BuffFight(fighter=fighter)
    except Exception as e:
        print(f"Erreur lors de l'init du buff [{buff_name}]")
        return BuffFight(fighter=fighter)
