import os
from fighting_bully import FightingBully
from database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship, composite
from sqlalchemy import ForeignKey, String
import player_info
from dataclasses import KW_ONLY, replace, dataclass

from bully import Stats, Seed

@dataclass
class ItemStats(Stats):
    pv: int


class Item(Base):
    __tablename__ = "item"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    player_id: Mapped[int] = mapped_column(ForeignKey("player.id"),init=False) 
    player: Mapped["player_info.Player"] = relationship(back_populates="items", init=False, lazy="selectin")

    name: Mapped[str] = mapped_column(String(50))

    _: KW_ONLY #Marks all following fields as kw_only=true, which means that they must be explicitly specified in the init.
    description: Mapped[str] = mapped_column(String(255), default="a mysterious item")

    is_end_round: Mapped[bool] = mapped_column(default=False)
    """Est ce que y'a un effet qui doit s'appliquer a la fin de chaque round
                - TODO"""

    is_bfr_fight: Mapped[bool] = mapped_column(default=False)
    """Est ce que y'a un effet qui doit s'appliquer avant le début du combat
                - buff_self = [buff_pv, buff_force, buff_agility, buff_lethality, buff_viciousness]
                - buff_enemy = [buff_pv, buff_force, buff_agility, buff_lethality, buff_viciousness]
    """


    is_aft_fight: Mapped[bool] = mapped_column(default=False)
    """Est ce que y'a un effet qui doit s'appliquer après la fin du combat
                - TODO"""

    buff_start_self: Mapped[ItemStats] = composite(
        mapped_column(name="buff_self_start_strength"),
        mapped_column(name="buff_self_start_agility"),
        mapped_column(name="buff_self_start_lethality"),
        mapped_column(name="buff_self_start_viciousness"),
        mapped_column(name="buff_self_start_pv"),
        default_factory=lambda: ItemStats(0,0,0,0,0)
    )

    buff_start_adv: Mapped[ItemStats] = composite(
        mapped_column(name="buff_adv_start_strength"),
        mapped_column(name="buff_adv_start_agility"),
        mapped_column(name="buff_adv_start_lethality"),
        mapped_column(name="buff_adv_start_viciousness"),
        mapped_column(name="buff_adv_start_pv"),
        default_factory=lambda: ItemStats(0,0,0,0,0)
    )
    buff_start_self_mult_lvl: Mapped[Seed] = composite(
        mapped_column(name="buff_self_start_multiplicatif_lvl_strength"),
        mapped_column(name="buff_self_start_multiplicatif_lvl_agility"),
        mapped_column(name="buff_self_start_multiplicatif_lvl_lethality"),
        mapped_column(name="buff_self_start_multiplicatif_lvl_viciousness"),
        default_factory=lambda: Seed(0,0,0,0)
    )
    buff_start_adv_mult_lvl: Mapped[Seed] = composite(
        mapped_column(name="buff_adv_start_multiplicatif_lvl_strength"),
        mapped_column(name="buff_adv_start_multiplicatif_lvl_agility"),
        mapped_column(name="buff_adv_start_multiplicatif_lvl_lethality"),
        mapped_column(name="buff_adv_start_multiplicatif_lvl_viciousness"),
        default_factory=lambda: Seed(0,0,0,0)
    )

    def effect_before_fight(self, fighting_bully_self:FightingBully, fighting_bully_adv:FightingBully) -> None:
        if(self.is_bfr_fight) :
            stat_self = replace(fighting_bully_self.base_stats)
            fighting_bully_self.pv += self.buff_start_self.pv
            lvl_self = fighting_bully_self.combattant.lvl
            stat_self.strength += self.buff_start_self.strength + round(lvl_self * self.buff_start_self_mult_lvl.strength)
            stat_self.agility += self.buff_start_self.agility + round(lvl_self * self.buff_start_self_mult_lvl.agility)
            stat_self.lethality += self.buff_start_self.lethality + round(lvl_self * self.buff_start_self_mult_lvl.lethality)
            stat_self.viciousness += self.buff_start_self.viciousness + round(lvl_self * self.buff_start_self_mult_lvl.viciousness)
            
            fighting_bully_self.base_stats = stat_self
            fighting_bully_self.stats = stat_self

            stat_adv = replace(fighting_bully_adv.base_stats)
            fighting_bully_adv.pv += self.buff_start_adv.pv
            lvl_adv = fighting_bully_adv.combattant.lvl
            stat_adv.strength = self.buff_start_adv.strength + round(lvl_adv * self.buff_start_adv_mult_lvl.strength)
            stat_adv.agility = self.buff_start_adv.agility + round(lvl_adv * self.buff_start_adv_mult_lvl.agility)
            stat_adv.lethality = self.buff_start_adv.lethality + round(lvl_adv * self.buff_start_adv_mult_lvl.lethality)
            stat_adv.viciousness = self.buff_start_adv.viciousness + round(lvl_adv * self.buff_start_adv_mult_lvl.viciousness)
            
            fighting_bully_adv.base_stats = stat_adv
            fighting_bully_adv.stats = stat_adv

        return

    def effect_end_round(self, pv_self, stat_self, pv_adv, stat_adv, 
                        my_turn:bool = False, hit_success:bool = False, letha_success:bool = False, 
                        agi_success:bool = False, vicious_success:bool = False, vicious_victim:bool = False) -> None:
        #IL FAUDRAIT MIEUX CREER UNE CLASS ETAT LAST ROUND QUI RECAPITULE TT CES PARamETRES PARCE QUE LA C4EST DLA MERDE
        
        #Modification
        return

    def effect_after_fight(self, gold_earned, xp_earned) -> tuple[int, float]:
        #Modification
        return (gold_earned, xp_earned)


    # __
    def set_file_path(self, new_file_path) -> None:
        self.associated_file_path = new_file_path
        self.associated_number = os.path.splitext(os.path.basename(new_file_path))[0]

    def get_print(self, compact_print = False) -> str:
        return str_print_item(self, compact_print)


# Pour gérer les print ______________________________________________
def str_print_item(i:Item, compact_print = False) -> str:
    text = ""
    if(compact_print) :
        text += i.name
    else :
        text += i.name
        text += "\nDescription : " + i.description
        if(i.is_bfr_fight) :
            if i.buff_start_self.pv != 0:
                text += "\nBonus HP : " + str(i.buff_start_self.pv)
            if (i.buff_start_self.strength != 0 or i.buff_start_self_mult_lvl.strength != 0):
                text += f"\nBonus Strength : {i.buff_start_self.strength} + {i.buff_start_self_mult_lvl.strength}*[LVL]"

            if (i.buff_start_self.agility != 0 or i.buff_start_self_mult_lvl.agility != 0):
                text += f"\nBonus Agility : {i.buff_start_self.agility} + {i.buff_start_self_mult_lvl.agility}*[LVL]"

            if (i.buff_start_self.lethality != 0 or i.buff_start_self_mult_lvl.lethality != 0):
                text += f"\nBonus Lethality : {i.buff_start_self.lethality} + {i.buff_start_self_mult_lvl.lethality}*[LVL]"

            if (i.buff_start_self.viciousness != 0 or i.buff_start_self_mult_lvl.viciousness != 0):
                text += f"\nBonus Viciousness : {i.buff_start_self.viciousness} + {i.buff_start_self_mult_lvl.viciousness}*[LVL]"
        

    return text

def mise_en_forme_str(text) -> str:
    new_text = "```" + text + "```"
    return new_text


"""
Ici on va mettre quelques exemples d'items par niveau de puissance, comme ça on garde une idéée pour l'équilibrage.
Le niveau de l'item en référence correspond à un item qui pourrait être trouvé dans une ruine de ce lvl. PS : on peut imaginer que la récompense de l'item de boss soit un niveau au dessus.

/!\\ Il vaut mieux donner des buff_self_start_multiplicatif_lvl plutot que buff_self_start, car les +3 en force est beaucoup plus puissant pour les bully low-level. 
Et donc si tu obtient un item très puissant qui fait +10 force, alors ça rend les bully lvl 1 beaucoup trop puissant. 
Il vaut mieux qu'un item ultra puissant soit par exemple +2*LVL Force, du coup ça donne +2 Force pour un lvl 1, et +10 pour un lvl 5, c'est très puissant.

1 PV <-> 0.2*lvl Stat ???

Niveau 1 : 
+1 Stat
+1 PV

Niveau 5 : 
+1 Stat + 0.2*lvl Stat
+1 PV ?

Niveau 10 : 
+2 Stat + 0.4*lvl Stat
+3 PV 

Niveau 50 : 
+1 Stat + 2*Lvl Stat
+7 PV
"""

