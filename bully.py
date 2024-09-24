import os
import random
import shutil
from typing import Any, List, Optional, Tuple
from dataclasses import dataclass, replace, InitVar, KW_ONLY, fields
from pathlib import Path
import utils.color_str

import player_info

from enum import Enum
from sqlalchemy.orm import Mapped, mapped_column, MappedAsDataclass, relationship, composite
from sqlalchemy import String, select, ForeignKey
from sqlalchemy.ext.asyncio.session import async_object_session
from utils.database import Base, new_session, DBPath
from sqlalchemy.ext.mutable import MutableComposite


BULLY_RARITY_BASE_POINTS = [15, 17, 19, 21, 23]
BULLY_RARITY_LEVEL = [1, 1.1, 1.25, 1.5, 2]
BULLY_RARITY_DEATH_EXP_COEFF = [0.5, 1, 1.25, 1.5, 2, 2]
BULLY_RARITY_DEATH_MIN_GOLD = [0, 10, 20, 100, 200, 0]
BULLY_RARITY_DEATH_MAX_GOLD = [0, 40, 100, 300, 500, 0]

NOBODY_LEVEL_EVOLUTION = 15
NOBODY_RARITY_EVOLUTION_CHANCES = [0, 30, 30, 30, 10, 0] #Mettre 0 en proba d'avoir unique

BULLY_MAX_LEVEL = 50
BULLY_MAX_BASE_HP = 10
BULLY_ASCENDED_MAX_BASE_HP = 13


BULLY_DEFAULT_PATH_IMAGE = Path("bully_not_found.png")

class Rarity(Enum):
    #self.rarity.name pour avoir le nom du truc
    NOBODY = 0
    TOXIC = 1
    MONSTER = 2
    DEVASTATOR = 3
    SUBLIME = 4
    UNIQUE = 5

    @property
    def base_points(self) -> int:
        return BULLY_RARITY_BASE_POINTS[self.value]
    
    @property
    def coef_level_points(self) -> float:
        return BULLY_RARITY_LEVEL[self.value]
    
    @property
    def death_exp_coeff(self) -> float:
        return BULLY_RARITY_DEATH_EXP_COEFF[self.value]
    
    @property
    def death_min_gold(self):
        return BULLY_RARITY_DEATH_MIN_GOLD[self.value]

    @property
    def death_max_gold(self):
        return BULLY_RARITY_DEATH_MAX_GOLD[self.value]
    
@dataclass
class Stats(MutableComposite):
    strength: float
    agility: float
    lethality: float
    viciousness: float

    def __setattr__(self, __name: str, __value: Any) -> None:
        super().__setattr__(__name, __value)
        self.changed()

    def increase_with_seed(self, seed:"Seed", *, talkative = False, valeur:float=1.0) -> None:
        # Get a random stat
        random_num = random.uniform(0.0, 0.999999) # Not 1 to account for possible float calculation errors.
        cum_prob = seed.cumulative_probs()
        stats = self.__dataclass_fields__
        for i, field_name in enumerate(stats):
            if random_num <= cum_prob[i]:
                break
        else:
            print("ERREUR ON NE DEVRAIT PAS ARRIVER ICI ")
            return
        
        # Increase the value of the attribute
        setattr(self, field_name, getattr(self,field_name) + valeur)
        if(talkative):
            print(f"{field_name.capitalize()} +{valeur}!")
        return
    
    def max_stat(self) -> str:
        stats = self.__dataclass_fields__.keys()
        max_stat = max(stats, key=lambda stat: getattr(self, stat))
        return max_stat
    
    def sum_stats(self) -> float:
        return self.strength + self.agility + self.lethality + self.viciousness
    
    def to_str_color(self)-> str:
        import math
        txt_s = f"{color_str.blue(str(round(self.strength, max(0,2-round(math.log10(self.strength))))))}"
        txt_a = f"{color_str.yellow(str(round(self.agility, max(0,2-round(math.log10(self.agility))))))}"
        txt_l = f"{color_str.red(str(round(self.lethality, max(0,2-round(math.log10(self.lethality))))))}"
        txt_v = f"{color_str.green(str(round(self.viciousness, max(0,2-round(math.log10(self.viciousness))))))}"
        
        return f"|{txt_s}|{txt_a}|{txt_l}|{txt_v}|"
    
@dataclass
class Seed(MutableComposite):
    strength: float
    agility: float
    lethality: float
    viciousness: float

    def __setattr__(self, __name: str, __value: Any) -> None:
        super().__setattr__(__name, __value)
        self.changed()

    @staticmethod
    def generate_seed_stat() -> "Seed":
        seed = []
        for _ in range(len(Seed.__dataclass_fields__)):
            r = random.random()
            seed.append(r)
        total = sum(seed)
        seed = [val/total for val in seed]

        return Seed(*seed)
    
    def extremization(self) -> "Seed":
        seed_extreme = replace(self)
        seed_names = seed_extreme.__dataclass_fields__
        for name in seed_names:
            setattr(seed_extreme, name, getattr(seed_extreme,name) ** 1.5)
        total = sum(getattr(seed_extreme,name) for name in seed_names)
        for name in seed_names:
            setattr(seed_extreme, name, getattr(seed_extreme,name) / total)
        return seed_extreme

    def cumulative_probs(self) -> List[float]:
        cumulative_sum: float = 0
        cumulative_probs = []

        # Calculate the cumulative sum of the probabilities
        for name in self.__dataclass_fields__:
            cumulative_sum += getattr(self, name)
            cumulative_probs.append(cumulative_sum)
        return cumulative_probs

    def sum_val_seed(self) -> float:
        return self.strength + self.agility + self.lethality + self.viciousness

class LevelUpException(Exception):
    def __init__(self, lvl, text=""):
        self.lvl = lvl
        self.text = text
        super().__init__(text)


class Bully(Base):
    __tablename__ = "bully"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    player_id: Mapped[int] = mapped_column(ForeignKey("player.id"),init=False) 
    player: Mapped["player_info.Player"] = relationship(back_populates="bullies", init=False, lazy="selectin")

    name: Mapped[str] = mapped_column(String(50))

    in_reserve:Mapped[bool] = mapped_column(default=False)

    _: KW_ONLY #Marks all following fields as kw_only=true, which means that they must be explicitly specified in the init.

    image_file_path: Mapped[Optional[Path]] = mapped_column(type_ = DBPath, default=None, nullable=True)
    must_load_image: InitVar[bool] = True
    lvl: Mapped[int] = mapped_column(default = 1)
    exp: Mapped[float] = mapped_column(default = 0.0)
    rarity: Mapped[Rarity] = mapped_column(default=Rarity.NOBODY) #Automatic Enum mapping! neat
    max_pv: Mapped[int] = mapped_column(default=BULLY_MAX_BASE_HP)
    seed: Mapped[Seed] = composite(
        mapped_column(name="seed_strength"),
        mapped_column(name="seed_agility"),
        mapped_column(name="seed_lethality"),
        mapped_column(name="seed_viciousness"),
        # init=False, default_factory=Seed.generate_seed_stat
        default_factory=Seed.generate_seed_stat
    )
    stats: Mapped[Stats] = composite(
        mapped_column(name="stat_strength"),
        mapped_column(name="stat_agility"),
        mapped_column(name="stat_lethality"),
        mapped_column(name="stat_viciousness"),
        default=None
    )

    def __post_init__(self, must_load_image:bool):
        if(must_load_image):
            self.image_file_path = self.new_possible_image_random()
        if self.stats is None or (None in self.stats.__dict__.items()):
            self.generate_bully_stat()


    def generate_bully_stat(self) -> None:
        self.stats = Stats(1,1,1,1)
        if self.rarity == Rarity.UNIQUE :
            for k in range(4) :
                self.stats.strength += self.seed.strength
                self.stats.agility += self.seed.agility
                self.stats.lethality += self.seed.lethality
                self.stats.viciousness += self.seed.viciousness
            return

        nb_points = self.rarity.base_points
        self.increase_stat_with_seed(nb_points, extrem_seed=True)

    def increase_stat_with_seed(self, nb_points=1, valeur:float=1.0, extrem_seed = False, talkative = False):
        used_seed = self.seed
        
        if(extrem_seed):
            #Pour l'initialisation, on extrémise un peu la seed pour que les stats reflètent plus la seed
            used_seed = self.seed.extremization()

        for _ in range(nb_points):
            self.stats.increase_with_seed(used_seed, talkative=talkative, valeur=valeur)
        return
    
    def increase_stat_unique_rarity(self, nb_points):
        if self.rarity != Rarity.UNIQUE:
            raise Exception("This is not a UNIQUE bully")

        for _ in range(nb_points):
            self.stats.strength += self.seed.strength
            self.stats.agility += self.seed.agility
            self.stats.lethality += self.seed.lethality
            self.stats.viciousness += self.seed.viciousness
        return

    def give_exp(self, exp_recu) -> None:
        self.exp += exp_recu
        lvl_except:Optional[LevelUpException] = None
        if(self.exp >= self.lvl):
            try:
                self.level_up()
            except LevelUpException as l :
                lvl_except = l
        self.exp = round(self.exp, 1)
        if lvl_except is not None :
            raise lvl_except
        
    def level_up(self):
        lvl_except:Optional[LevelUpException] = None
        base_lvl = self.lvl
        nobody_evolve = False
        while self.exp >= self.lvl and self.lvl < BULLY_MAX_LEVEL:
            self.exp -= self.lvl
            self.level_up_one()

            if not nobody_evolve:
                lvl_except = LevelUpException(self.lvl, text=f"leveled up from {base_lvl} to {str(self.lvl)} ")
            if(self.lvl >= NOBODY_LEVEL_EVOLUTION and self.rarity == Rarity.NOBODY):
                self.nobody_evolution()
                nobody_evolve = True
                lvl_except = LevelUpException(self.lvl, text=f"unlocks its full potential and becomes . . . {self.rarity.name}!")
                
        if lvl_except is not None:
            raise lvl_except

    def level_up_one(self):
        self.lvl += 1
        if self.rarity == Rarity.UNIQUE :
            self.increase_stat_unique_rarity(self.lvl)
            
        else:
            # new_points = new_points_lvl_up(self.lvl, self.rarity)
            new_points = self.lvl
            valeur = self.rarity.coef_level_points
            self.increase_stat_with_seed(nb_points=new_points, talkative = False, valeur=valeur)

    def exp_give_when_die(self):
        xp = self.lvl
        xp *= self.rarity.death_exp_coeff
        return round(xp, 1)
    
    def gold_give_when_die(self):
        def lerp(start, end, x):
            return x*end + (1-x) * start
        
        mini = self.rarity.death_min_gold
        maxi = self.rarity.death_max_gold
        gold = lerp(mini, maxi, (self.lvl - 1)/9)
        return gold

    def nobody_evolution(self):
        new_rarity:Rarity = random.choices(list(Rarity), weights=NOBODY_RARITY_EVOLUTION_CHANCES)[0]
        
        #On rajoute les points qu'il faut rajouter
        # difference_points = (new_rarity.points_bonus - self.rarity.points_bonus) + int(NOBODY_LEVEL_EVOLUTION * (new_rarity.level_bonus - self.rarity.level_bonus))
        # self.increase_stat_with_seed(nb_points=difference_points, talkative = False)
        difference_points = nb_points_tot_rarity(self.lvl, new_rarity) - self.stats.sum_stats()
        nb_points:int = round(self.lvl * (self.lvl + 1) / 2)
        val = difference_points/nb_points
        self.increase_stat_with_seed(nb_points=nb_points, valeur=val, talkative = False)

        self.rarity = new_rarity

        #On change les pv max
        self.max_pv = BULLY_ASCENDED_MAX_BASE_HP

        #On change l'image : 
        self.image_file_path = self.new_possible_image_random()

    async def kill(self):
        print("je me tue : ", self.name)
        self.player.bullies.remove(self)
        session = async_object_session(self)
        if session is not None:
            await session.delete(self)

    def get_print(self, compact_print = False, current_hp:int|None = None):
        return str_print_bully(self, compact_print, current_hp=current_hp)
    

    #Pour gérer l'image du bully
    def get_image(self) -> Path:
        image_path = self.image_file_path
        if image_path is None or not image_path.exists():
            # Si aucune image correspondante n'est trouvée, renvoie le chemin de l'image par défaut
            image_path = Path("bully_not_found.png")
        return image_path

    def new_possible_image_random(self):
        folder_path = Path(f"game_data/bully_images/{self.rarity.name}")
        if not os.path.isdir(folder_path):
            print("Image dir is absent!")
            return None

        image_files = list(folder_path.iterdir())

        file_path = random.choice(image_files)
        return file_path


    @staticmethod
    def clash_stat(st_actif: float, st_passif: float, neutre: Optional[float] = None):
        """
        return true si la st_actif réussit le challenge
        """
        if neutre is None :
            neutre = min(st_actif, st_passif)
        r = random.random()
        proba = 0.8 * st_actif / (st_actif + st_passif + neutre ) + (0.2 if (st_actif>st_passif) else 0)
        # proba = renforce_proba_sin(proba)
        proba = renforce_proba_atan(proba)
        if( r < proba ) :
            return True
        else :
            return False
        
# /////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
# ________________________________________________________________________________________________________________________________________________

# Pour gérer les print ______________________________________________
def str_print_bully(bully:Bully, compact_print = False, current_hp:int|None = None):
    text = ""
    hp_text = f"Max HP : {bully.max_pv}" if current_hp is None else f"HP : {current_hp}/{bully.max_pv}"
    def good_print_float(x:float) -> float|int:
        xf:float = float(x)
        return int(xf) if xf.is_integer() else round(xf, 1)
    if(compact_print) :
        text += bully.name + " | lvl : " + str(bully.lvl) + " | Rarity : " + bully.rarity.name + " | " + hp_text + "\n\t" 
        text += " |S : "+ str(good_print_float(bully.stats.strength))
        text += " |A : "+ str(good_print_float(bully.stats.agility))
        text += " |L : "+ str(good_print_float(bully.stats.lethality))
        text += " |V : "+ str(good_print_float(bully.stats.viciousness))
    else :
        text += bully.name + "\tRarity : " + bully.rarity.name
        text += "\nlvl : " + str(bully.lvl)
        text += "\texp : " + str(bully.exp)
        text += "\t" + hp_text
        #On print la force
        text += "\nStrength : - - -"
        text += str_text_stat(int(bully.stats.strength))
        
        #On print l'agilité
        text += "\nAgility :- - - -"
        text += str_text_stat(int(bully.stats.agility))

        #On print la lethalité
        text += "\nLethality :- - -"
        text += str_text_stat(int(bully.stats.lethality))

        #On print la vicieusité
        text += "\nViciousness :- -"
        text += str_text_stat(int(bully.stats.viciousness))

    return text

def str_text_stat(value_stat:int):
    """
    Retourne un truc de la forme : "04▮▮▮▮". avec "04" la valeur de la stat, et le même nombre de fois le charactère "▮"
    """
    text_stat = ""
    if(value_stat >= 10):
            text_stat += str(value_stat)
    else :
        text_stat += ("0" + str(value_stat))

    while value_stat >= 1000:
        value_stat -= 1000
        text_stat += "⭐"
    while value_stat >= 100:
        value_stat -= 100
        text_stat +="*"
    while value_stat >= 10:
        value_stat-= 10
        text_stat += "▮"
    for k in range(value_stat):
        text_stat += "."
    return text_stat

def mise_en_forme_str(text):
    new_text:str = "```ansi\n" + text + "```"
    new_text = new_text.replace("UNIQUE", "[2;35m[1;35mUn[0m[2;35m[0m[2;34m[1;34mi[0m[2;34m[0m[2;31m[1;31mq[0m[2;31m[0m[2;32m[1;32mu[0m[2;32m[0m[2;33m[1;33me[0m[2;33m[0m")
    new_text = new_text.replace("SUBLIME", "[2;35m[1;35mSublime[0m[2;35m[0m")
    new_text = new_text.replace("DEVASTATOR", "[2;34m[1;34mDevastator[0m[2;34m[0m")
    new_text = new_text.replace("MONSTER", "[2;31m[1;31mMonster[0m[2;31m[0m")
    new_text = new_text.replace("TOXIC", "[2;32m[1;32mToxic[0m[2;32m[0m")
    new_text = new_text.replace("NOBODY", "[2;33m[1;33mNobody[0m[2;33m[0m")
    return new_text


##//////////////////////////////////////////////////////////////////////////////////////////////////////

# Pour gérer buff de stat selon rareté 
def new_points_lvl_up(lvl, rarity=Rarity.NOBODY) -> int:
    coeff = rarity.coef_level_points
    lvl_win = int(lvl * coeff) - int((lvl-1) * coeff)
    return lvl_win

def nb_points_tot_rarity(lvl, rarity=Rarity.NOBODY) -> float:
    if rarity != Rarity.UNIQUE:
        base = rarity.base_points
        coef = rarity.coef_level_points
        tot:float = base + 4
        for l in range(1 +1, lvl +1):
            tot += l*coef
    else :
        print(f"Le bully est unique et ne peux pas être mis à jour comme ça.")
    # elif coef_unique is not None :
    #     for l in range(1 +1, lvl +1):
    #         tot += l * coef_unique
    # else : 
    #     raise Exception("Unique coef seed must be provided")
    
    return tot


# //////////////////////////////////////////////////////////////////////////////////////////////////////

def renforce_proba_atan(x, c = 1.4, v=1.25):
    import math
    a = 2*x - 1
    a = a if a > -1 else a + 0.001
    a = a if a < 1 else a - 0.001
    r = math.atan(1/(1-a)**v - 1/(1+a)**v)
    r /= (math.pi/2)
    r += 1
    r /= 2
    r = r**c
    return r


def renforce_proba_sin(x, c = 1.0):
    import math
    a = 2*x - 1
    r = math.sin(a * math.pi / 2)
    r += 1
    r /= 2
    r = r**c
    return r


