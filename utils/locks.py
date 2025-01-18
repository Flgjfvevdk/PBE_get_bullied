

players_in_interaction: set[int] = set()
class PlayerLock():
    def __init__(self, id: int):
        self.player_id = id

    def check(self) -> bool:
        return self.player_id not in players_in_interaction
    def __enter__(self):
        # if not self.check():
        #     raise Exception("User is already in interaction")
        players_in_interaction.add(self.player_id)
    def __exit__(self, _exc_type, _exc_va, _exc_tb):
        players_in_interaction.discard(self.player_id)

import asyncio
arenas_in_interaction: dict[int, asyncio.Lock] = {}
class ArenaLock:
    def __init__(self, arena_id: int):
        self.arena_id = arena_id
        if arena_id not in arenas_in_interaction:
            arenas_in_interaction[arena_id] = asyncio.Lock()
        self.lock = arenas_in_interaction[arena_id]

    async def __aenter__(self):
        await self.lock.acquire()

    async def __aexit__(self, _exc_type, _exc_val, _exc_tb):
        self.lock.release()
