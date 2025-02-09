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
    exp_coef:float = 1.0
    gold_coef:float = 1.0

    @staticmethod
    def create_fighting_bully(b:Bully, forbid_buffs_tags:list[str]=[]) -> "FightingBully":
        fighter = FightingBully(bully=b, pv=b.max_pv, base_stats=replace(b.stats), stats=replace(b.stats))#, buffs=create_buff_instance(b.buff_fight_tag))
        if (b.buff_fight_tag != "NoBuff" and b.buff_fight_tag not in forbid_buffs_tags):
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
        hp_text = f"HP : {round(self.pv, 1)}/{self.bully.max_pv}"
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

    def add_buff(self, buff_taf:str):
        self.buffs.append(create_buff_instance(buff_taf, fighter=self))

    def reset(self):
        self.pv = self.bully.max_pv
        self.reset_stats()
        for b in self.buffs:
            b.__init__(fighter=self)

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

def get_player_team(player:player_info.Player, is_team_buff_active = True, is_filter_unique_buffs = True):
    import buffs
    fighters:list[FightingBully] = []
    forbid_buffs_tags:list[str] = []
    for b in player.get_equipe():
        new_fighter = FightingBully.create_fighting_bully(b, forbid_buffs_tags=forbid_buffs_tags)
        fighters.append(new_fighter)
        BuffClass = buffs.name_to_buffs_class[b.buff_fight_tag]
        if is_filter_unique_buffs and b.buff_fight_tag not in forbid_buffs_tags and BuffClass.category == CategoryBuff.UNIQUE:
            forbid_buffs_tags.append(b.buff_fight_tag)
    
    setup_buffs_team(fighters, is_team_buff_active)
    
    return fighters

def setup_buffs_team(fighters:list[FightingBully], is_team_buff_active = True):
    if is_team_buff_active:
        add_team_buff(fighters)

    return fighters


def add_team_buff(fighters:list[FightingBully]):
    compteur_rarity:dict[Rarity, int] = {r:0 for r in Rarity}
    team_buff_rarity:Rarity|None = None

    for f in fighters:
        compteur_rarity[f.bully.rarity] += 1
    if compteur_rarity[Rarity.TOXIC] >= 3:
        team_buff_rarity = Rarity.TOXIC
    elif compteur_rarity[Rarity.MONSTER] >= 3:
        team_buff_rarity = Rarity.MONSTER
    elif compteur_rarity[Rarity.DEVASTATOR] >= 3:
        team_buff_rarity = Rarity.DEVASTATOR
    elif compteur_rarity[Rarity.SUBLIME] >= 3:
        team_buff_rarity = Rarity.SUBLIME
    if team_buff_rarity is not None:
        buff_team, buff_true = rarity_to_buff_tags(team_buff_rarity)
        for f in fighters:
            if f.bully.rarity == team_buff_rarity:
                f.add_buff(buff_true)
            else :
                f.add_buff(buff_team)

def filter_unique_buffs(fighters:list[FightingBully]):
    unique_buffs_name:list[str] = []
    for f in fighters:
        for b in f.buffs:
            if b.category == CategoryBuff.UNIQUE:
                if b.name not in unique_buffs_name:
                    unique_buffs_name.append(b.name)
                else:
                    f.buffs.remove(b)
    
            

def rarity_to_buff_tags(r:Rarity) -> tuple[str, str]:
    if r == Rarity.TOXIC:
        return ("ToxicTeam", "TrueToxic")
    elif r == Rarity.MONSTER:
        return ("MonsterTeam", "TrueMonster")
    elif r == Rarity.DEVASTATOR:
        return ("DevastatorTeam", "TrueDevastator")
    elif r == Rarity.SUBLIME:
        return ("SublimeTeam", "TrueSublime")
    else:
        return ("", "")

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
