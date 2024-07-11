from unidecode import unidecode
from faker import Faker
import pickle


import random
from collections import defaultdict


class NameGenerator:
    def __init__(self, names):
        self.names = names
        self.transitions = defaultdict(list)
        self.starters = []

    def train(self) -> None:
        for name in self.names:
            if len(name) >= 2:
                self.starters.append(name[:2])
                for i in range(len(name) - 2):
                    self.transitions[name[i:i+2]].append(name[i + 2])

    def generate_name(self, length=None) -> str :
        length_:int = length if length is not None else random.randint(5, 8)
        if not self.starters:
            return ""

        name = random.choice(self.starters)
        while len(name) < length_:
            if name[-2:] in self.transitions:
                next_char = random.choice(self.transitions[name[-2:]])
                name += next_char
            else:
                break
        return name

NAME_GENERATOR:NameGenerator


try : 
    with open('generator_name.pkl', 'rb') as file:
        NAME_GENERATOR = pickle.load(file)
    
    print("on a déjà créé le truc\n")

except Exception as e:
    print(e)
    print("on créée le générateur\n")
    faker_en = Faker()
    names_en = [unidecode(faker_en.first_name()) for _ in range(50000)]
    names = names_en

    # Entrainement
    name_list = []
    for k in range(20000):
        random_name = random.choice(names)
        name_list.append(random_name)
        names.remove(random_name)

    NAME_GENERATOR = NameGenerator(name_list)
    NAME_GENERATOR.train()

    with open('generator_name.pkl', 'wb') as file:
        pickle.dump(NAME_GENERATOR, file)

if __name__ =="__main__":
    if not isinstance(NAME_GENERATOR, NameGenerator):
            raise TypeError("le generateur de noms n'est pas correct")
    
    txt=""
    for k in range(30):
        new_name = NAME_GENERATOR.generate_name()
        txt+=new_name
        txt+="\n"
    print(txt)