
import os
import time
from utils import get_player_path

# Var payday
PAYDAY_COOLDOWN = 10 * 60 * 60
PAYDAY_VALUE = 100

MONEY_ICON = "🩹"
MONEY_JOIN_VALUE = 400

async def cooldown_restant_pay(user_id: int) -> int:
    # Vérifier si l'utilisateur est en cooldown
    # En utilisant les informations enregistrées dans un fichier ou une base de données
    # Par exemple, vous pouvez stocker la dernière utilisation dans un fichier
    path_player = get_player_path(user_id)
    try:
        with open(path_player / "cooldown.txt", "r") as file:
            last_usage = int(file.read().strip())
    except FileNotFoundError as e:
        print(e)
        return 0

    current_time = int(time.time())
    elapsed_time = current_time - last_usage
    print("PAYDAY_COOLDOWN ",elapsed_time)
    if elapsed_time > PAYDAY_COOLDOWN:
        return 0
    else:
        return PAYDAY_COOLDOWN - elapsed_time

def enregistrer_cooldown_pay(user_id:int) -> None:
    # Enregistrer l'heure actuelle comme dernière utilisation de la commande
    # Dans un fichier ou une base de données
    path_player = get_player_path(user_id)
    with open(path_player / "cooldown.txt", "w") as file:
        file.write(str(int(time.time())))

def get_money_user(user_id: int) -> int:
    path_player = get_player_path(user_id)
    try:
        with open(path_player / "playerMoney.txt", "r") as file:
            return int(file.read())
    except FileNotFoundError as e:
        print(e)
        return 0


def give_money(user_id:int , montant:int = PAYDAY_VALUE):
    path_player = get_player_path(user_id)
    current_money = get_money_user(user_id)
    print(current_money)
    try:
        with open(path_player / "playerMoney.txt", "w") as file:
            file.write(str(current_money + montant))
    except Exception as e:
        print(e)
    return


def format_temps(secondes:int):
    minutes, secondes = divmod(secondes, 60)
    heures, minutes = divmod(minutes, 60)

    if heures >= 1:
        return f"{heures}h {minutes}m"
    elif minutes > 0:
        return f"{minutes}m"
    else:
        return f"{secondes}s"


