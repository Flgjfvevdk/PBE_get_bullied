
import os
from datetime import datetime, timezone, timedelta
from player_info import Player

# Var payday
PAYDAY_COOLDOWN = 8 #* 60 * 60
PAYDAY_VALUE = 250

MONEY_EMOJI = "🩹"
MONEY_JOIN_VALUE = 500
MONEY_REFERRAL = 600

async def cooldown_restant_pay(player: Player) -> int:
    # Vérifier si l'utilisateur est en cooldown
    # En utilisant les informations enregistrées dans un fichier ou une base de données
    # Par exemple, vous pouvez stocker la dernière utilisation dans un fichier
    last_usage = player.last_payday.replace(tzinfo=timezone.utc)

    current_time = datetime.now(timezone.utc)
    elapsed_time = current_time - last_usage
    print("PAYDAY_COOLDOWN ",elapsed_time)
    if elapsed_time.total_seconds() > PAYDAY_COOLDOWN:
        return 0
    else:
        return PAYDAY_COOLDOWN - int(elapsed_time.total_seconds())

def enregistrer_cooldown_pay(player: Player) -> None:
    # Enregistrer l'heure actuelle comme dernière utilisation de la commande
    # Dans un fichier ou une base de données
    player.last_payday = datetime.now(timezone.utc)

def get_money_user(player: Player) -> int:
    return player.money


def give_money(player: Player, montant:int = PAYDAY_VALUE):
    player.money += montant


def format_temps(secondes:int):
    minutes, secondes = divmod(secondes, 60)
    heures, minutes = divmod(minutes, 60)

    if heures >= 1:
        return f"{heures}h {minutes}m"
    elif minutes > 0:
        return f"{minutes}m"
    else:
        return f"{secondes}s"


