from fighting_bully import BuffFight, FightingBully, RecapRound

#Les buffs qui existe : /////////////////////////////////////////////////////////////////////////
class NoBuff(BuffFight):
    def apply_buff(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound):
        return
    
class Rage(BuffFight):
    def __init__(self):
        super().__init__()
        self.description:str = "When damaged, buff Strength"
    def apply_buff(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound):
        if fighter == recap_round.defender and recap_round.damage_receive > 0:
            fighter.stats.strength += fighter.combattant.lvl * 0.15
        return 

class Frustration(BuffFight):
    def __init__(self):
        super().__init__()
        self.description:str = "When attack fails, buff Lethality"
    def apply_buff(self, fighter: FightingBully, opponent: FightingBully, recap_round: RecapRound):
        if fighter == recap_round.attacker and recap_round.damage_receive == 0:
            fighter.stats.lethality += fighter.combattant.lvl * 0.1
        return 
