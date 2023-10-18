import os
import random
import numpy as np
import pickle
import shutil

from enum import Enum
#self.rarity.name pour avoir le nom du truc
class Rarity(Enum):
    NOBODY = 0
    TOXIC = 1
    MONSTER = 2
    DEVASTATOR = 3
    SUBLIME = 4

nb_points_init_rarity = [4, 5, 6, 7, 8]
nb_points_lvl_rarity = [1, 1.1, 1.25, 1.5, 2]

lvl_max = 50
base_max_pv = 10

class Bully :
    def __init__(self, name, file_path, stats=None, rarity=Rarity.NOBODY, must_load_image = True, max_pv = base_max_pv):
        self.name = name
        self.set_file_path(file_path)
        #print("associated number ", self.associated_number)
        self.lvl = 1
        self.exp = 0.0
        self.rarity = rarity
        self.max_pv = max_pv
        self.seed = generate_seed_stat()
        if(must_load_image):
            self.set_image_with_path(self.new_possible_image_random())
        #print(name + "'s seed :", self.seed)
        if(stats is None):
            self.strength = 1
            self.agility = 1
            self.lethality = 1
            self.viciousness = 1
            #self.increase_stat_with_seed(nb_points=5, extrem_seed=True)
            points_bonus = nb_points_init_rarity[self.rarity.value]
            self.increase_stat_with_seed(nb_points=points_bonus, extrem_seed=True)
                
        else :
            self.strength = stats[0]
            self.agility = stats[1]
            self.lethality = stats[2]
            self.viciousness = stats[3]

    def to_json(self):
        return {
            "name": self.name,
            "file_path": self.get_file_path(),
            "lvl": self.lvl,
            "exp": self.exp,
            "rarity": self.rarity.name,
            "max_pv": self.max_pv,
            "seed": list(self.seed),
            "stats": [self.strength, self.agility, self.lethality, self.viciousness],
            "image_file_path": self.get_image_path()
        }
    
    def __setstate__(self, state):
        # Check if 'rarity' exists in the state
        if 'rarity' not in state:
            state['rarity'] = Rarity.NOBODY
        if 'max_pv' not in state:
            state['max_pv'] = base_max_pv
        self.__dict__.update(state)


    def increase_stat_with_seed(self, nb_points=1, extrem_seed = False, talktative = False):
        used_seed = self.seed
        if(extrem_seed):
            #Pour l'initialisation, on extrémise un peu la seed pour que les stats reflètent plus la seed
            used_seed = extremisation_seed(self.seed)

        augmentations = [0,0,0,0]
        cumulative_probs = cumulative_probs_seed(used_seed)
        for k in range(nb_points):
            i = random_seed_index(cumulative_probs)
            augmentations[i] += 1
            if(talktative):
                match (i):
                    case 0 :
                        print("Strenght +1")
                    case 1 :
                        print("Agility +1")
                    case 2 :
                        print("Lethality +1")
                    case 3 :
                        print("Viciousness +1")
        
        self.strength += augmentations[0]
        self.agility += augmentations[1]
        self.lethality += augmentations[2]
        self.viciousness += augmentations[3]
        return

    def give_exp(self, exp_recu):
        self.exp += exp_recu
        if(self.exp >= self.lvl):
            self.level_up()
        self.exp = round(self.exp, 1)
        print("exp : ", self.exp)
        self.save_changes()

    def level_up(self):
        while self.exp >= self.lvl:
            self.exp -= self.lvl
            self.lvl += 1
            self.lvl = min(self.lvl, lvl_max)
            print("level up :", self.lvl)
            new_points = new_points_lvl_up(self.lvl, self.rarity)
            self.increase_stat_with_seed(nb_points=new_points, talktative = True)

    def level_up_one(self):
        self.lvl += 1
        print("level up :", self.lvl)
        new_points = new_points_lvl_up(self.lvl, self.rarity)
        self.increase_stat_with_seed(nb_points=new_points, talktative = True)

    def set_level(self, level):
        print("/!\\ do not change stat, donc faut faire gaffe, mieux vaut enlever ça ou renommer")
        self.lvl = level

    def exp_give_when_die(self):
        xp = self.lvl
        match (self.rarity.value):
            case 0 :
                xp = xp * 0.5
            case 1 :
                xp = xp * 1
            case 2 :
                xp = xp * 1.25
            case 3 :
                xp = xp * 1.5
            case 4 :
                xp = xp * 2
        return round(xp, 1)
    
    def gold_give_when_die(self):
        gold = 0
        min_gold_gave = [0, 40, 80, 150, 200]
        max_gold_gave = [0, 80, 150, 500, 700]
        def f(x):
            x = max(1, min(10, x))
            return (x - 1) / 9
        
        mini = min_gold_gave[self.rarity.value]
        maxi = max_gold_gave[self.rarity.value]
        gold = f(self.lvl) * maxi + (1 - f(self.lvl)) * mini
        return gold

    # Manipulation file
    def kill(self):
        print("je me tue : ", self.name)
        os.remove(self.get_file_path())
        self.remove_image()
    
    def save_changes(self, forced_save = False):
        print("Saving file")
        try :
            print("j'essaie de save' : ", self.name)
            if(not os.path.exists(self.get_file_path()) and not forced_save) :
                print("can't save the file")
                return
            file = open(self.get_file_path(), "wb")
            print(file)
            pickle.dump(self, file)
            file.close()
        except Exception as e :
            print(e)
    
    def set_file_path(self, new_file_path):
        self.associated_file_path = new_file_path
        self.associated_number = os.path.splitext(os.path.basename(new_file_path))[0]

    def get_file_path(self):
        return self.associated_file_path

    def get_print(self, compact_print = False):
        return str_print_bully(self, compact_print)

    #_____

    #Pour gérer l'image du bully
    def get_image(self):
        folder_path = os.path.dirname(self.associated_file_path)  # Obtenir le chemin du dossier
        image_files = os.listdir(folder_path)

        for file_name in image_files:
            if file_name.startswith(f"{self.associated_number}_"):
                image_path = os.path.join(folder_path, file_name)
                return image_path

        # Si aucune image correspondante n'est trouvée, renvoie le chemin de l'image par défaut
        default_image_path = "bully_not_found.png"
        return default_image_path
    
    def get_image_path(self):
        folder_path = os.path.dirname(self.associated_file_path)
        image_files = os.listdir(folder_path)
        for file_name in image_files:
            if file_name.startswith(f"{self.associated_number}_"):
                return os.path.join(folder_path, file_name)
        default_image_path = "bully_not_found.png"
        return default_image_path

    def set_image_with_path(self, image_path):
        if(image_path is None):
            #print("aucune image dispo")
            return
        image_name = os.path.basename(image_path)
        new_image_name = f"{self.associated_number}_{image_name}"
        new_image_path = os.path.join(os.path.dirname(self.associated_file_path), new_image_name)
        shutil.move(image_path, new_image_path)
        return new_image_path
    
    def set_image_with_name(self, image_name):
        folder_path = f"game_data/bully_images/{self.rarity.name}"
        image_path = os.path.join(folder_path, image_name)
        self.set_image_with_path(image_path)

    def remove_image(self):
        folder_path = os.path.dirname(self.associated_file_path)

        for file_name in os.listdir(folder_path):
            if file_name.startswith(f"{self.associated_number}_"):
                image_path = os.path.join(folder_path, file_name)
                new_image_name = file_name.replace(f"{self.associated_number}_", "")
                new_folder_path = os.path.join("game_data/bully_images", self.rarity.name)
                new_image_path = os.path.join(new_folder_path, new_image_name)

                if not os.path.exists(new_folder_path):
                    os.makedirs(new_folder_path)

                shutil.move(image_path, new_image_path)
                return new_image_path

        return None
    
    def new_possible_image_random(self):
        #print("on est al")
        folder_path = f"game_data/bully_images/{self.rarity.name}"
        #print("folder_path : ", folder_path)
        if not os.path.isdir(folder_path):
            return None

        image_files = os.listdir(folder_path)
        #print("image_files : ", image_files)
        if not image_files:
            return None

        random_image_file = random.choice(image_files)
        file_path = os.path.join(folder_path, random_image_file)
        #print("on retourne ,", file_path)
        return file_path
    #______


    @staticmethod
    def clash_stat(st_actif, st_passif, neutre = None):
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

    @staticmethod
    def combat_tres_simple(b1, b2):
        """
        Renvoie un tuple : (bully_gagnant, bully_perdant)
        """
        r = random.random()
        if( r < b1.strength / ( b1.strength + b2.strength ) ) :
            return (b1, b2)
        else :
            return (b2, b1)
        
# /////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
# ________________________________________________________________________________________________________________________________________________

# Pour gérer les print ______________________________________________
def str_print_bully(bully:Bully, compact_print = False):
    text = ""
    if(compact_print) :
        text += bully.name + " | lvl : " + str(bully.lvl) + " | Rarity : " + bully.rarity.name + "\n\t[" + str(bully.associated_number) + "]\t" 
        text += " |S : "+ str(bully.strength)
        text += " |A : "+ str(bully.agility)
        text += " |L : "+ str(bully.lethality)
        text += " |V : "+ str(bully.viciousness)
    else :
        text += bully.name + "\t[" + str(bully.associated_number) + "]" + " | Rarity : " + bully.rarity.name
        text += "\nlvl : " + str(bully.lvl)
        text += "\texp : " + str(bully.exp)
        #On print la force
        text += "\nStrength : - - -"
        text += str_text_stat(bully.strength)
        
        #On print l'agilité
        text += "\nAgility :- - - -"
        text += str_text_stat(bully.agility)

        #On print la lethalité
        text += "\nLethality :- - -"
        text += str_text_stat(bully.lethality)

        #On print la vicieusité
        text += "\nViciousness :- -"
        text += str_text_stat(bully.viciousness)

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

# Pour gérer les modifs de stat _____________________________________
def generate_seed_stat(nb_stat = 4):
    seed = []
    for k in range(nb_stat):
        r = random.random()
        seed.append(r)
    seed = np.array(seed)
    seed = seed / np.sum(seed)
    return seed

def extremisation_seed(seed):
    seed_extreme = seed.copy()
    seed_extreme = seed_extreme**(1.5)
    seed_extreme = seed_extreme / sum(seed_extreme)
    return seed_extreme

def cumulative_probs_seed(seed):
    cumulative_sum = 0
    cumulative_probs = []

    # Calculate the cumulative sum of the probabilities
    for prob in seed:
        cumulative_sum += prob
        cumulative_probs.append(cumulative_sum)
    return cumulative_probs

def random_seed_index(cumulative_probs):
    # Generate a random number between 0 and 1
    random_num = random.uniform(0, 1)

    # Find the index corresponding to the random number in the cumulative probabilities
    for i, cum_prob in enumerate(cumulative_probs):
        if random_num <= cum_prob:
            return i
    
    print("ERREUR ON NE DEVRAIT PAS ARRIVER ICI ")
    return -1
##//////////////////////////////////////////////////////////////////////////////////////////////////////

# Pour gérer lvl up selon rareté 
def new_points_lvl_up(lvl, rarity=Rarity.NOBODY):
    coef_bonus = nb_points_lvl_rarity[rarity.value] - 1
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




