import os

class Item :

    def __init__(self, name = "ITEM", description="a mysterious item", is_bfr_fight = False, is_end_round = False, is_aft_fight = False, 
                 buff_self_start = [0,0,0,0,0], buff_adv_start = [0,0,0,0,0], 
                 buff_self_start_multiplicatif_lvl = [0,0,0,0], buff_adv_start_multiplicatif_lvl = [0,0,0,0]) :
        '''
        Param : 
            - is_bfr_fight : Est ce que y'a un effet qui doit s'appliquer avant le début du combat
                - buff_self = [buff_pv, buff_force, buff_agility, buff_lethality, buff_viciousness]
                - buff_enemy = [buff_pv, buff_force, buff_agility, buff_lethality, buff_viciousness]
            - is_end_round : Est ce que y'a un effet qui doit s'appliquer a la fin de chaque round
                -
            - is_aft_fight : Est ce que y'a un effet qui doit s'appliquer après la fin du combat
                -
        '''
        self.name = name
        self.description = description
        
        self.is_bfr_fight = is_bfr_fight
        self.is_end_round = is_end_round
        self.is_aft_fight = is_aft_fight

        if(self.is_bfr_fight): 
            self.buff_start_self_pv = buff_self_start[0]
            self.buff_start_self_strength = buff_self_start[1]
            self.buff_start_self_agility = buff_self_start[2]
            self.buff_start_self_lethality = buff_self_start[3]
            self.buff_start_self_viciousness = buff_self_start[4]

            self.buff_start_self_mult_lvl_strength = buff_self_start_multiplicatif_lvl[0]
            self.buff_start_self_mult_lvl_agility = buff_self_start_multiplicatif_lvl[1]
            self.buff_start_self_mult_lvl_lethality = buff_self_start_multiplicatif_lvl[2]
            self.buff_start_self_mult_lvl_viciousness = buff_self_start_multiplicatif_lvl[3]

            self.buff_start_adv_pv = buff_adv_start[0]
            self.buff_start_adv_strength = buff_adv_start[1]
            self.buff_start_adv_agility = buff_adv_start[2]
            self.buff_start_adv_lethality = buff_adv_start[3]
            self.buff_start_adv_viciousness = buff_adv_start[4]

            self.buff_start_adv_mult_lvl_strength = buff_adv_start_multiplicatif_lvl[0]
            self.buff_start_adv_mult_lvl_agility = buff_adv_start_multiplicatif_lvl[1]
            self.buff_start_adv_mult_lvl_lethality = buff_adv_start_multiplicatif_lvl[2]
            self.buff_start_adv_mult_lvl_viciousness = buff_adv_start_multiplicatif_lvl[3]

        if(self.is_end_round) :
            #Faire un truc
            pass

        if(self.is_aft_fight) : 
            #Faire un truc 
            pass

    def effect_before_fight(self, pv_self, stat_self, pv_adv, stat_adv, lvl_self=1, lvl_adv=1):
        if(self.is_bfr_fight) :
            pv_self += self.buff_start_self_pv
            buff_self_str = self.buff_start_self_strength + round(lvl_self * self.buff_start_self_mult_lvl_strength)
            buff_self_agi = self.buff_start_self_agility + round(lvl_self * self.buff_start_self_mult_lvl_agility)
            buff_self_leth = self.buff_start_self_lethality + round(lvl_self * self.buff_start_self_mult_lvl_lethality)
            buff_self_vicious = self.buff_start_self_viciousness + round(lvl_self * self.buff_start_self_mult_lvl_viciousness)
            #stat_self = [stat_self[0] + self.buff_start_self_strength, stat_self[1] + self.buff_start_self_agility, stat_self[2] + self.buff_start_self_lethality, stat_self[3] + self.buff_start_self_viciousness]
            stat_self = [stat_self[0] + buff_self_str, stat_self[1] + buff_self_agi, stat_self[2] + buff_self_leth, stat_self[3] + buff_self_vicious]
            
            pv_adv += self.buff_start_adv_pv
            buff_adv_str = self.buff_start_adv_strength + round(lvl_adv * self.buff_start_adv_mult_lvl_strength)
            buff_adv_agi = self.buff_start_adv_agility + round(lvl_adv * self.buff_start_adv_mult_lvl_agility)
            buff_adv_leth = self.buff_start_adv_lethality + round(lvl_adv * self.buff_start_adv_mult_lvl_lethality)
            buff_adv_vicious = self.buff_start_adv_viciousness + round(lvl_adv * self.buff_start_adv_mult_lvl_viciousness)
            #stat_adv = [stat_adv[0] + self.buff_start_adv_strength, stat_adv[1] + self.buff_start_adv_agility, stat_adv[2] + self.buff_start_adv_lethality, stat_adv[3] + self.buff_start_adv_viciousness]
            stat_adv = [stat_adv[0] + buff_adv_str, stat_adv[1] + buff_adv_agi, stat_adv[2] + buff_adv_leth, stat_adv[3] + buff_adv_vicious]

        
        return (pv_self, stat_self, pv_adv, stat_adv)

    def effect_end_round(self, pv_self, stat_self, pv_adv, stat_adv, my_turn:bool = False, hit_success:bool = False, letha_sucess:bool = False, agi_success:bool = False, vicious_succes:bool = False, vicious_victim:bool = False):
        #Modification
        return (pv_self, stat_self, pv_adv, stat_adv)

    def effect_after_fight(self, gold_earned, xp_earned):
        #Modification
        return (gold_earned, xp_earned)


    # __
    def set_file_path(self, new_file_path):
        self.associated_file_path = new_file_path
        self.associated_number = os.path.splitext(os.path.basename(new_file_path))[0]

    def get_print(self, compact_print = False):
        return str_print_item(self, compact_print)


# Pour gérer les print ______________________________________________
def str_print_item(i:Item, compact_print = False):
    text = ""
    if(compact_print) :
        text += i.name
    else :
        text += i.name
        text += "\nDescription : " + i.description
        if(i.is_bfr_fight) :
            if i.buff_start_self_pv != 0:
                text += "\nBonus HP : " + str(i.buff_start_self_pv)
            if (i.buff_start_self_strength != 0 or i.buff_start_self_mult_lvl_strength != 0):
                text += f"\nBonus Strength : {i.buff_start_self_strength} + {i.buff_start_self_mult_lvl_strength}*[LVL]"

            if (i.buff_start_self_agility != 0 or i.buff_start_self_mult_lvl_agility != 0):
                text += f"\nBonus Agility : {i.buff_start_self_agility} + {i.buff_start_self_mult_lvl_agility}*[LVL]"

            if (i.buff_start_self_lethality != 0 or i.buff_start_self_mult_lvl_lethality != 0):
                text += f"\nBonus Lethality : {i.buff_start_self_lethality} + {i.buff_start_self_mult_lvl_lethality}*[LVL]"

            if (i.buff_start_self_viciousness != 0 or i.buff_start_self_mult_lvl_viciousness != 0):
                text += f"\nBonus Viciousness : {i.buff_start_self_viciousness} + {i.buff_start_self_mult_lvl_viciousness}*[LVL]"
        

    return text

def mise_en_forme_str(text):
    new_text = "```" + text + "```"
    return new_text


"""
Ici on va mettre quelques exemples d'items par niveau de puissance, comme ça on garde une idéée pour l'équilibrage.
Le niveau de l'item en référence correspond à un item qui pourrait être trouvé dans une ruine de ce lvl. PS : on peut imaginer que la récompense de l'item de boss soit un niveau au dessus.

/!\ Il vaut mieux donner des buff_self_start_multiplicatif_lvl plutot que buff_self_start, car les +3 en force est beaucoup plus puissant pour les bully low-level. 
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

