
import os
import time

# Var payday
temps_attente_payday = 10 * 60 * 60
payday_value = 100

icon_money = "🩹"
money_join_value = 400

async def cooldown_restant_pay(user_id):
    # Vérifier si l'utilisateur est en cooldown
    # En utilisant les informations enregistrées dans un fichier ou une base de données
    # Par exemple, vous pouvez stocker la dernière utilisation dans un fichier
    path_player = "game_data/player_data/" + str(user_id)
    try:
        with open(path_player + "/cooldown.txt", "r") as file:
            last_usage = int(file.read())
    except FileNotFoundError as e:
        print(e)
        return 0

    current_time = int(time.time())
    print("temps_attente_payday ",current_time - last_usage)
    if current_time - last_usage > temps_attente_payday:
        return 0
    else:
        return temps_attente_payday - (current_time - last_usage)

def enregistrer_cooldown_pay(user_id):
    # Enregistrer l'heure actuelle comme dernière utilisation de la commande
    # Dans un fichier ou une base de données
    path_player = "game_data/player_data/" + str(user_id)
    with open(path_player + "/cooldown.txt", "w") as file:
        file.write(str(int(time.time())))

def get_money_user(user_id):
    path_player = "game_data/player_data/" + str(user_id)
    try:
        with open(path_player + "/playerMoney.txt", "r") as file:
            return int(file.read())
    except FileNotFoundError as e:
        print(e)
        return 0


def give_money(user_id, montant=payday_value):
    path_player = "game_data/player_data/" + str(user_id)
    current_money = get_money_user(user_id)
    print(current_money)
    try:
        with open(path_player + "/playerMoney.txt", "w") as file:
            file.write(str(current_money + montant))
    except Exception as e:
        print(e)
    return


def format_temps(seconde):
    heures = seconde // 3600
    minutes = (seconde % 3600) // 60
    secondes = seconde % 60

    if heures >= 1:
        return f"{heures}h {minutes}m"
    elif minutes > 0:
        return f"{minutes}m"
    else:
        return f"{secondes}s"


