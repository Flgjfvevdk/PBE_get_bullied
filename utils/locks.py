

players_in_interaction: set[int] = set()
class PlayerLock():
    def __init__(self, id: int):
        self.player_id = id

    def check(self) -> bool:
        return self.player_id not in players_in_interaction
    def __enter__(self):
        if not self.check():
            raise Exception("User is already in interaction")
        players_in_interaction.add(self.player_id)
    def __exit__(self, _exc_type, _exc_va, _exc_tb):
        players_in_interaction.remove(self.player_id)
