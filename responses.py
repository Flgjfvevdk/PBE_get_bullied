import random
import donnees

def handler_response(message) -> str:
    #on met tous en minuscule pour eviter dêtre sensible à la case
    p_message=message.lower()

    if p_message == "hello":
        return "salut wè"
    
    if p_message == "roll":
        return str(random.randint(1,6))
    
    if p_message == "+1":
        donnees.compteur = donnees.compteur + 1
        return "on augmente le compteur : " + str(donnees.compteur)

    if p_message == "!help":
        return "`aucune aide pour toi.`"
