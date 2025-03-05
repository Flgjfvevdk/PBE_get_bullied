import json
import discord
from typing import List
SERVERS_FILENAME = 'discord_servers.json'

def load_servers() -> List[int]:
    try:
        with open(SERVERS_FILENAME, 'r') as f:
            servers_id = json.load(f)
    except FileNotFoundError:
        servers_id = []
    return servers_id


def save_server(servers_ids:List[int]):
    with open(SERVERS_FILENAME, 'w') as f:
        json.dump(servers_ids, f, indent=4)

