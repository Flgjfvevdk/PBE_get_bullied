import os
import random
import numpy as np
import pickle
import shutil
from typing import List, Optional, Tuple
from dataclasses import dataclass, replace, InitVar, KW_ONLY
from pathlib import Path

from player import Player

from enum import Enum
from sqlalchemy.orm import Mapped, mapped_column, MappedAsDataclass, relationship, composite
from sqlalchemy import String, select, ForeignKey
from sqlalchemy.ext.asyncio.session import async_object_session
from database import Base, new_session


BULLY_RARITY_POINTS = [4, 5, 6, 7, 8]
BULLY_RARITY_LEVEL = [1, 1.1, 1.25, 1.5, 2]
BULLY_RARITY_DEATH_EXP_COEFF = [0.5, 1, 1.25, 1.5, 2]
BULLY_RARITY_DEATH_MIN_GOLD = [0, 40, 80, 150, 200]
BULLY_RARITY_DEATH_MAX_GOLD = [0, 80, 150, 500, 700]

BULLY_MAX_LEVEL = 50
BULLY_MAX_BASE_HP = 10

class Rarity(Enum):
    #self.rarity.name pour avoir le nom du truc
    NOBODY = 0
    TOXIC = 1
    MONSTER = 2
    DEVASTATOR = 3
    SUBLIME = 4

    @property
    def points_bonus(self) -> int:
        return BULLY_RARITY_POINTS[self.value]
    
    @property
    def level_bonus(self) -> float:
        return BULLY_RARITY_LEVEL[self.value]
    
    @property
    def death_exp_coeff(self) -> float:
        return BULLY_RARITY_DEATH_EXP_COEFF[self.value]
    
    @property
    def death_min_gold(self):
        return BULLY_RARITY_DEATH_MAX_GOLD[self.value]

    @property
    def death_max_gold(self):
        return BULLY_RARITY_DEATH_MIN_GOLD[self.value]
@dataclass
class Stats():
    strength: int
    agility: int
    lethality: int
    viciousness: int

    def increase_with_seed(self, seed:"Seed", *, talkative = False) -> None:
        # Get a random stat
        random_num = random.uniform(0, 0.9999) # Not 1 to account for possible float calculation errors.
        cum_prob = seed.cumulative_probs()
        for i, field_name in enumerate(self.__dataclass_fields__):
            if random_num <= cum_prob[i]:
                break
        else:
            print("ERREUR ON NE DEVRAIT PAS ARRIVER ICI ")
            return
        
        # Increase the value of the attribute
        setattr(self,field_name,getattr(self,field_name)+1)
        if(talkative):
            print(f"{field_name.capitalize()} +1!")
        return
    
@dataclass
class Seed():
    strength: float
    agility: float
    lethality: float
    viciousness: float

    @staticmethod
    def generate_seed_stat() -> "Seed":
        seed = []
        for _ in range(len(Seed.__dataclass_fields__)):
            r = random.random()
            seed.append(r)
        seed = np.array(seed)
        seed = seed / np.sum(seed)

        return Seed(*seed)
    
    def extremization(self) -> "Seed":
        seed_extreme = replace(self)
        seed_vals = seed_extreme.__dict__
        for name in seed_vals:
            seed_vals[name] **= 1.5
        total = sum(seed_vals[name] for name in seed_vals)
        for name in seed_vals:
            seed_vals[name] /= total
        return seed_extreme

    def cumulative_probs(self) -> List[float]:
        cumulative_sum: float = 0
        cumulative_probs = []

        # Calculate the cumulative sum of the probabilities
        for name in self.__dict__:
            cumulative_sum += self.__dict__[name]
            cumulative_probs.append(cumulative_sum)
        return cumulative_probs
    

class Bully(Base):
    __tablename__ = "bully"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    player_id: Mapped[int] = mapped_column(ForeignKey("player.id"),init=False) 
    player: Mapped[Player] = relationship(back_populates="bullies", init=False)

    name: Mapped[str] = mapped_column(String(50))

    _: KW_ONLY #Marks all following fields as kw_only=true, which means that they must be explicitly specified in the init.

    image_file_path: Mapped[Optional[Path]] = mapped_column(default=None)
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
        init=False, default_factory=Seed.generate_seed_stat
    )
    stats: Mapped[Stats] = composite(
        mapped_column(name="stat_strength"),
        mapped_column(name="stat_agility"),
        mapped_column(name="stat_lethality"),
        mapped_column(name="stat_viciousness"),
        default=None
    )
    associated_number: Mapped[int] = mapped_column("associated_number", init=False)


    def __post_init__(self, must_load_image:bool):
        if(must_load_image):
            self.image_file_path = self.new_possible_image_random()

        if self.stats is None:
            self.stats = self.generate_bully_stat()
    
    def generate_bully_stat(self) -> None:
        self.stats = Stats(1,1,1,1)
        nb_points = self.rarity.points_bonus
        self.increase_stat_with_seed(nb_points, extrem_seed=True)

    def increase_stat_with_seed(self, nb_points=1, extrem_seed = False, talkative = False):
        used_seed = self.seed
        if(extrem_seed):
            #Pour l'initialisation, on extrémise un peu la seed pour que les stats reflètent plus la seed
            used_seed = self.seed.extremization()

        for _ in range(nb_points):
            self.stats.increase_with_seed(used_seed, talkative=talkative)
        return

    def give_exp(self, exp_recu) -> None:
        self.exp += exp_recu
        if(self.exp >= self.lvl):
            self.level_up()
        self.exp = round(self.exp, 1)
        print("exp : ", self.exp)

    def level_up(self):
        while self.exp >= self.lvl and self.lvl <= BULLY_MAX_LEVEL:
            self.exp -= self.lvl
            self.lvl += 1
            print("level up :", self.lvl)
            new_points = new_points_lvl_up(self.lvl, self.rarity)
            self.increase_stat_with_seed(nb_points=new_points, talkative = True)

    def level_up_one(self):
        self.lvl += 1
        print("level up :", self.lvl)
        new_points = new_points_lvl_up(self.lvl, self.rarity)
        self.increase_stat_with_seed(nb_points=new_points, talkative = True)

    def exp_give_when_die(self):
        xp = self.lvl
        xp *= self.rarity.death_exp_coeff
        return round(xp, 1)
    
    def gold_give_when_die(self):
        def lerp(start, end, x):
            return x*end + (1-x) * start
        
        mini = self.rarity.death_min_gold
        maxi = self.rarity.death_max_gold
        gold = lerp(mini, maxi, (self.lvl -1)/9)
        return gold


    async def kill(self):
        print("je me tue : ", self.name)
        session = async_object_session(self)
        if session is not None:
            await session.delete(self)

    def get_print(self, compact_print = False):
        return str_print_bully(self, compact_print)
    

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
    def clash_stat(st_actif: int, st_passif: int, neutre: Optional[int] = None):
        """
        return true si la st_actif réussit le challenge
        """
        if neutre is None :
            neutre = min(st_actif, st_passif)
        r = random.random()
        #proba = st_actif / ( st_actif + st_passif + neutre )
        proba = 0.8 * st_actif / (st_actif + st_passif + neutre ) + (0.2 if (st_actif>st_passif) else 0)
        if( r < proba ) :
            return True
        else :
            return False
        
# /////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
# ________________________________________________________________________________________________________________________________________________

# Pour gérer les print ______________________________________________
def str_print_bully(bully:Bully, compact_print = False):
    text = ""
    if(compact_print) :
        text += bully.name + " | lvl : " + str(bully.lvl) + " | Rarity : " + bully.rarity.name + "\n\t[" + str(bully.associated_number) + "]\t" 
        text += " |S : "+ str(bully.stats.strength)
        text += " |A : "+ str(bully.stats.agility)
        text += " |L : "+ str(bully.stats.lethality)
        text += " |V : "+ str(bully.stats.viciousness)
    else :
        text += bully.name + "\t[" + str(bully.associated_number) + "]" + " | Rarity : " + bully.rarity.name
        text += "\nlvl : " + str(bully.lvl)
        text += "\texp : " + str(bully.exp)
        #On print la force
        text += "\nStrength : - - -"
        text += str_text_stat(bully.stats.strength)
        
        #On print l'agilité
        text += "\nAgility :- - - -"
        text += str_text_stat(bully.stats.agility)

        #On print la lethalité
        text += "\nLethality :- - -"
        text += str_text_stat(bully.stats.lethality)

        #On print la vicieusité
        text += "\nViciousness :- -"
        text += str_text_stat(bully.stats.viciousness)

    return text

def str_text_stat(value_stat):
    """
    Retourne un truc de la forme : "04▮▮▮▮". avec "04" la valeur de la stat, et le même nombre de fois le charactère "▮"
    """
    text_stat = ""
    if(value_stat >= 10):
            text_stat += str(value_stat)
    else :
        text_stat += ("0" + str(value_stat))

    for k in range(value_stat):
        text_stat += "▮"
    return text_stat

def mise_en_forme_str(text):
    new_text = "```ansi\n" + text + "```"
    new_text = new_text.replace("SUBLIME", "[2;35m[1;35mSublime[0m[2;35m[0m")
    new_text = new_text.replace("DEVASTATOR", "[2;34m[1;34mDevastator[0m[2;34m[0m")
    new_text = new_text.replace("MONSTER", "[2;31m[1;31mMonster[0m[2;31m[0m")
    new_text = new_text.replace("TOXIC", "[2;32m[1;32mToxic[0m[2;32m[0m")
    new_text = new_text.replace("NOBODY", "[2;33m[1;33mNobody[0m[2;33m[0m")
    return new_text


##//////////////////////////////////////////////////////////////////////////////////////////////////////

# Pour gérer lvl up selon rareté 
def new_points_lvl_up(lvl, rarity=Rarity.NOBODY) -> int:
    coef_bonus = rarity.level_bonus - 1
    if(coef_bonus < 0):
        raise Exception("coef_bonus n'est pas censé être négatif")
    if(coef_bonus > 1):
        raise Exception("coef_bonus n'est pas censé être >1 (sinon bug)")
    if(coef_bonus == 0):
        return 1
    else :
        lvl_win = 1
        print("coef_bonus : ", coef_bonus)
        print("(1/coef_bonus) : ", (1/coef_bonus))
        print("lvl % coef_bonus : ", lvl % (1/coef_bonus))
        if(lvl % (1/coef_bonus) < 1):
            print("ici de fou")
            lvl_win+=1
        return lvl_win


# //////////////////////////////////////////////////////////////////////////////////////////////////////




