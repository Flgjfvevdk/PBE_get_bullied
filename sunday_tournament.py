from typing import Dict, Tuple
from player_info import Player

class Tournament:
    def __init__(self):
        self.active = False
        self.results: Dict[Tuple[int, int], int] = {}  # Stores results as {(player1_id, player2_id): winner_id}

    def activate(self):
        self.active = True

    def deactivate(self):
        self.active = False

    def register_fight_result(self, player1: Player, player2: Player, winner: Player):
        if not self.active:
            return "Tournament is not active."

        player1_id = player1.id
        player2_id = player2.id

        # Ensure player1_id is always less than player2_id for consistency
        if player1_id > player2_id:
            player1_id, player2_id = player2_id, player1_id

        fight_key = (player1_id, player2_id)

        if fight_key not in self.results:
            self.results[fight_key] = winner.id
            return 
        else:
            return 

    def get_results(self):
        return self.results