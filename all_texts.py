from typing import Optional
from utils.language_manager import language_manager_instance, DEFAULT_LANG
from discord.ext.commands import Context

# lang_default = "fr"


texts = {
    "fr":{
        "join":"Veuillez rejoindre le jeu avant ! (!!join)",
        "other_hasnt_joined":"{other} n'a pas rejoint le jeu.",
        "other_already_joined":"{user} a déjà rejoint le jeu.",
        "cooldown_wait": "Vous devez attendre encore {cd} avant de pouvoir utiliser cette commande à nouveau.",
        "arena_bonus_py": "×{bonus} (bonus champion d'arène)",
        "payday": ("Vous avez reçu des {money_emoji} ! +{recu}{money_emoji} {bonus_str}\n"
                    "Vous avez {total_money} {money_emoji}"),
        "bank": "Vous avez {money} {money_emoji}",
        "already_in_action": "Vous êtes déjà en interaction.",
        "other_is_in_action" : "{user} est déjà en interaction.",
        "credits" : "Devs : Flgjfvevdk, Pelvis Presley. Aide : Texz, et toutes les personnes qui ont testé le jeu dans ses premières versions. Admin : Flgjfvevdk",
        "cant_self_tf" :"Vous ne pouvez pas vous team challenge vous-même.",
        "missing_argument" :"Erreur : Argument requis manquant `{arg}`.",
        "dg_error_param" : "Le paramètre 'level' doit être un nombre (ou un mot-clé spécifique).",
        "dg_greater_0" : "Le niveau du donjon doit être supérieur à 0.",
        "dg_lower_50" : "Le niveau maximum du donjon est 50.",
        "dg_pallier" : "Vous devez vaincre le niveau de donjon {lvl_pallier} avant d'explorer ce donjon.",
        "ruin_greater_0" : "Le niveau de la ruine doit être supérieur à 0.",
        "ruin_lower_50": "Le niveau maximum de la ruine est 50.",
        "no_arena" : "Aucune arène trouvée pour ce serveur. Veuillez créer une arène d'abord.",
        "cant_trade_self": "Vous ne pouvez pas échanger avec vous-même.",

        #bully 
        "bully_died" : "{bully} est mort dans d'atroces souffrances.",
        "bully_lost_lvl" : "{bully} a perdu {lvl} niveau(x).",

        #arena
        "arena_enter":"{user} entre dans l'arène !",
        "arena_title_thread":"{user} est dans l'arène",
        "arena_ask_enter": "{user}, voulez-vous entrer dans l'arène ? (Prix = {price} {money_emoji})",
        "arena_label":"Entrer dans l'arène (et payer {price})",
        "arena_no_money": "{user}, vous n'avez pas assez de {money_emoji} pour entrer dans l'arène. (Prix = {price})",
        "arena_next_teamfight": "Prochain teamfight contre :\n{teamfighters}",
        "arena_reached_rank": "{user}, vous avez atteint le rang {rank} dans l'arène ! (récompense : {reward} {money_emoji})",
        "arena_no_improve_rank": "{user}, vous n'avez pas amélioré votre rang dans l'arène.",

        #consumable
        "consumable_aliment_effect":"Debuff **{nerf}** pour buff **{buff}** d'une valeur max : {value}.",
        "consumable_water_rarity_error" : "Cette Water est faite pour les bullies **{water_rarity}**, pas **{bully_rarity}**",
        "consumable_water_effect":"{name} : à l'utilisation, un bully de rareté **{rarity}** récupérera un maximum de **{value} niveaux**.",
        "consumable_too_many_select": (
            "Vous avez trop de consommables. "
            "Veuillez sélectionner un consommable existant pour le remplacer."
        ),
        "consumable_too_many_destroyed": (
            "Vous avez trop de consommables, le nouveau est détruit."
        ),
        "consumable_added": (
            "Le consommable : {name} a été ajouté à votre inventaire."
        ),
        "timeout_choose_faster": (
            "Temps écoulé, choisissez plus vite la prochaine fois, {user}."
        ),
        "consumable_no_selection": "Vous n'avez sélectionné aucun consommable.",
        "consumable_applied": (
            "Le consommable ({name}) a été appliqué avec succès !"
        ),
        "consumable_none": (
            "Vous n'avez aucun consommable :("
        ),
        "consumable_do_ruin": "Faites des ruines pour en obtenir.",
        "consumable_choose_title": "Choisissez un consommable",
        "consumable_user_title": "Consommables de {user}",
        "consumable_use_command": "!!use_consumable pour en utiliser un",
        "consumable_removed" : "Le consommable {name} a été retiré de votre inventaire.",

        #dungeon
        "dungeon_enter": "{user} entre dans {dungeon_name}",
        "dungeon_cancel": "{user} a annulé le combat et quitté le donjon.",
        "dungeon_team_left_timeout": "Votre équipe a quitté le donjon. Choisissez plus vite la prochaine fois {user}.",
        "dungeon_team_left": "Votre équipe a quitté le donjon.",
        "dungeon_win": "{user} a vaincu {dungeon_name} !",
        "dungeon_next_enemy": "Prochain ennemi :\n{enemy}",
        "dungeon_enemy_dead": "{enemy_name} est mort ! Vous progressez dans le donjon.",
        "fighter_stay_in_fight": "{fighter_name} reste en combat.",
        "fighter_change_too_slow": "Trop lent, {fighter_name} reste en combat.",
        "fighter_change_error": "Erreur, {fighter_name} reste en combat.",
        "dungeon_highest_ranked": "<@{player_id}> - Niveau de Donjon le plus élevé vaincu : {max_dungeon}",
        "dungeon_not_ranked": "<@{player_id}> - n'est pas classé en Donjon.",

        #fight_manager
        "challenge_fight": "{user1} défie {user2} !",
        "challenge_fight_for_fun": "{user1} défie {user2} pour un combat amical (pas de mort, pas d'xp) !",
        "challenge_teamfight": "{user1} défie {user2} dans un combat d'équipe !",
        "challenge_teamfight_for_fun": "{user1} défie {user2} dans un combat d'équipe amical (pas de mort, pas d'xp) !",
        "challenge_accepted": "Défi accepté !",
        "challenge_declined": "Défi refusé.",
        "fight_cancel": "{user} a annulé le combat",
        "fight_giveup": "{user} a abandonné le combat",
        "challenge_too_late": "Trop tard ! Aucun combat entre {user1} et {user2}.",
        "fight_winner": "{winner} a gagné le combat !",
        "teamfight_winner": "{winner} a gagné le teamfight contre {loser}!",
        "challenge_selected_bully":"{user} a selectionné {bully} (lvl : {lvl})",
        "gain": "{name} a gagné {reward}",
        "select_to_late_random":"Trop tard, un bully aléatoire a été sélectionné pour {user}.",
        "title_challenge": "{user1} vs {user2}",

        #interact_game
        "already_joined_game": "Vous avez déjà rejoint le jeu ! (!!tuto pour le tutoriel)",
        "other_join" : "{user} a rejoint le jeu !",
        "welcome_adventure": "Bienvenue dans l'aventure ! (!!tuto)",
        "invite_join_game": "{user}, voulez-vous rejoindre le jeu ?",
        "referral_reward" : "{user}, vous avez invité {nb} amis ! Vous méritez une récompense (demandez-la :wink:)",
        "max_bullies_reached": "{user}, vous ne pouvez pas avoir plus de {max_bullies} bullies !",
        "new_bully_msg": "Vous avez un nouveau bully : {bully}",
        "choose_bully": "{user}, choisissez un bully :",
        "selected_bully": "{user} a sélectionné {bully}",
        "choose_fighter": "{user}, choisissez votre combattant :",
        "selected_fighter": "{user} sélectionne {bully}.",
        "choose_suicide": "{user}, choisissez un bully à abandonner :",
        "suicide_kill": "{user} a abandonné {bully}",
        "no_suicide": "{user} n'a pas abandonné de bully",
        "confirm_suicide": "{user}, voulez vous confirmer l'abandon définitive de {bully} ?",
        "your_bullies": "Vos bullies :",
        "you_have_no_bully" : "{user}, vous n'avez aucun bully.",
        "you_receive_gold" : "Vous avez reçu des {money_emoji} ! (+{value}){money_emoji})",

        #lootbox
        "lootbox_select": "Sélectionnez une lootbox à ouvrir. Bully level = [40-80]% du level de la box",
        "lootbox_require_dungeon": "{user}, vous devez battre le donjon de niveau {level} pour acheter cette lootbox",
        "lootbox_not_enough_money": "{user}, vous n'avez pas assez de {money_emoji} pour cette box [coût : {cout}{money_emoji}]",
        "lootbox_purchase_success": "{user} a acheté une lootbox et a obtenu... {bully} un {rarity}!",
        "lootbox_buff" : " [Avec {buff_tag}]",

        #reserve
        "reserve_bullies_info": "{user}, vos bullies en réserve :",
        "reserve_max_bullies": "Vous ne pouvez pas avoir plus de {max_reserve} bullies  dans votre réserve.",
        "new_bully_reserve": "Vous avez un nouveau bully en réserve : {bully}",
        "bully_moved": "{bully} a été déplacé vers votre {target}.",
        "team_full": "Votre {target} est déjà pleine.",
        "empty_team_or_reserve": "Votre équipe ou votre réserve est vide",
        "active_team" : "équipe active",
        "reserve" : "réserve",
        "label_send_reserve" :"Envoyer un bully en réserve",
        "label_send_team" : "Envoyer un bully dans votre équipe", 
        "label_switch_team_reserve" : "Switch team and réserve",
        "reserve_switch_bullies" : "{bully1} et {bully2} ont été échangés.",

        #ruine
        "ruin_enter": "{user} entre dans une ruine mystérieuse [lvl : {level}]",
        "ruin_enemy_intro": "Un ennemi se met en travers de votre chemin !\n{enemy}",
        "ruin_enemy_defeated": "{enemy} est mort ! Vous progressez dans la ruine.",
        "ruin_team_timeout": "Votre équipe a quitté la ruine. Choisissez plus vite la prochaine fois {user}.",
        "ruin_cancelled": "{user}, vous avez annulé le combat et quitté la ruine",
        "ruin_bully_error": "Votre bully est mort ou n'existe pas.\nVotre équipe a quitté la ruine.",
        "ruin_victory": "Félicitations {user}, vous avez battu le boss!",
        "elixir_of" : "Elixir - {elixir}",
        "found_conso" : "Vous avez trouvé un consommable : {name} !",
        "ruin_thread_error": "Une erreur s'est produite lors de la création du fil de discussion de la ruine.",
        "found_treasure" : "Vous avez trouvé un **trésor**. Il contient **{gold}** {money_emoji}!",
        "bully_is_dead" : "{bully} est mort !",
        
        "trap_strength_intro": "[STRENGTH] La salle est remplie de grosses pierres tranchantes. Quelqu'un doit créer un chemin en déplaçant ces grosses rochers.",
        "trap_strength_success": "Votre bully a déplacé des rochers et a créé un chemin sûr pour tout le monde.",
        "trap_strength_fail": "Déplacer ces rochers a laissé votre bully avec de nombreuses blessures et des saignements, mais le chemin est dégagé.",
        
        "trap_agility_intro": "[AGILITY] Pour progresser il faut grimper en haut d'un escalier en pierre en ruine. Quelqu'un doit grimper et attacher une corde en haut pour créer un chemin.",
        "trap_agility_success": "Votre bully a grimpé parfaitement et a attaché une corde pour les autres.",
        "trap_agility_fail": "En grimpant votre bully s'est blessé, mais la corde est finalement attachée pour les autres.",
        
        "trap_lethality_intro": "[LETHALITY] Une créature terrifiante dort dans la salle. Quelqu'un doit l'assassiner pour créer un chemin sûr.",
        "trap_lethality_success": "Votre bully a poignardé la créature, qui est morte instantanément.",
        "trap_lethality_fail": "Votre bully a poignardé la créature, mais elle n'est pas morte instantanément, et a blessé votre bully.",
        
        "trap_viciousness_intro": "[VICIOUSNESS] La salle est pleine de pièges. Quelqu'un doit les identifier pour trouver un chemin sûr.",
        "trap_viciousness_success": "Votre bully a identifié tous les pièges et a trouvé un chemin sûr pour tout le monde.",
        "trap_viciousness_fail": "Votre bully a été blessé par de nombreux pièges mais a fini par trouver un chemin sûr.",
        
        #shop
        "shop_dm_error": "Cette commande ne peut être utilisée que sur un serveur, pas en MP.",
        "shop_not_open": "Le shop n'est pas ouvert sur ce serveur. Demandez à un admin de l'ouvrir.",
        "shop_restocking": "Le shop se remplit. Veuillez patienter <{seconds} secondes>.",
        "shop_closed_message": "Le shop est fermé. À bientôt!",
        "shop_purchase_success": "{user} a acheté {bully} pour {cost}{money_emoji}!",
        "shop_bully_not_available" : "Ce bully n'est plus disponible (déso {user})",
        "shop_not_enough_money" : "{user}, vous n'avez pas assez de {money_emoji} pour acheter {bully}. Coût : {cost}{money_emoji}",
        "bully_in_shop" : "Bullies dans le shop : ",
        "price" : "Prix : {cost} {money_emoji}",

        #supply_bully
        # supply_bully - Snack Machine
        "snack_bonus_select": "Sélectionnez votre stat **bonus** :",
        "snack_bonus_timeout": "Timeout lors du choix du bonus. Veuillez réessayer.",
        "snack_malus_select": "Sélectionnez une stat **malus** :",
        "snack_malus_timeout": "Timeout lors du choix d'un malus. Veuillez réessayer.",
        "snack_conso_not_find": "Aucun consommable correspondant n'a été trouvé pour ces choix.",

        "conso_not_enough_money": "Vous n'avez pas assez de {money_emoji}.",
        "conso_value_prompt": "{user}, veuillez répondre avec un nombre correspondant au niveau du consommable souhaité :",
        "conso_level_timeout": "Timeout lors de la saisie du niveau. Opération annulée.",
        "conso_invalid_value": "La valeur saisie n'est pas un nombre entier valide. Opération annulée.",
        "conso_purchase_confirmation": "Voulez-vous acheter : **{name}[{value}]** pour {price} {money_emoji} ?\nEffet : {effect}",
        "conso_purchase_success": "Vous avez acheté **{name}[{value}]** pour {price} {money_emoji} !",

        # supply_bully - Water Fountain
        "water_name": "Eau XP - {rarity} - {value} LVL",
        "water_rarity_select": "Sélectionnez la **rareté** de l'eau XP :",
        "water_rarity_timeout": "Timeout lors du choix de la rareté. Veuillez réessayer.",
        "water_rarity_selected": "Rareté sélectionnée : **{rarity_name}**",

        # trades
        "trade_offer": "{user1} veut échanger avec {user2} !",
        "trade_timeout": "Trop tard ! Aucun échange entre {user1} et {user2}.",
        "trade_start": "L'échange commence",
        "trade_declined": "Échange refusé",
        "trade_confirmation": "Les deux utilisateurs confirment-ils l'échange ? ({user1} et {user2})",
        "trade_confirmation_timeout": "La confirmation de l'échange a expiré.",
        "trade_completed": "Échange terminé avec succès !",
        "trade_canceled": "Échange annulé.",
        "u_offer_b": "{user} propose : {btxt}",
        "trade_impossible":"{user} ne peux pas recevoir {bully}[lvl:{lvl}] car son plus grand donjon vaincu est niveau : {max_dungeon}.",

        #tournament
        "tournament_end": "```Le tournoi est terminé ! Résultats : \n{results}```",
        "tournament_recap_fight": "{user1} VS {user2} : {winner} a gagné",
        "tournament_winner": "{user} est le vainqueur du tournoi avec un score de {score}.",
        "tournament_player_score": "{user} : {score} points",

        # Category translations
        "category_Game": "Jeu",
        "category_Bully": "Bully",
        "category_Fight": "Combat",
        "category_Money": "Argent",
        "category_Tuto": "Tutoriel",
        "category_Consumable": "Consommable",
        "category_Uncategorized": "Uncategorized Commands",
        "category_Admin": "Admin",
        
        # Command help texts
        "help_join": "Pour rejoindre le jeu",
        "help_invite": "Pour inviter un ami à rejoindre le jeu",
        "help_payday": "Pour recevoir des 🩹",
        "help_bank": "Afficher ses ressources",
        "help_patchnote": "Nouvelle mise à jour récente",
        "help_leaderboard": "Affiche le classement des joueurs en fonction du donjon maximum terminé",
        "help_print_shop": "Affiche le shop de ce server",
        "help_buy_lootbox": "Pour acheter une lootbox",
        "help_credits": "Affiche les crédits",
        "help_sacrifice": "Élimine un bully de son club",
        "help_tuto": "Affiche un tutoriel général. Faites le si vous êtes perdu !",
        "help_tuto_all": "Affiche la liste des tutoriels. Faites le si vous êtes perdu !",
        "help_tuto_bully": "Affiche un tutoriel concernant le fonctionnemet des bullies",
        "help_tuto_rarity": "Affiche un tutoriel concernant le fonctionnemet des bullies",
        "help_tuto_fight": "Affiche un tutoriel concernant les combats",
        "help_tuto_dungeon": "Affiche un tutoriel concernant les donjons",
        "help_tuto_ruin": "Affiche un tutoriel concernant les ruines",
        "help_tuto_shop": "Affiche un tutoriel concernant les achats de bullies",
        "help_tuto_economy": "Affiche un tutoriel concernant l'économie du jeu",
        "help_tuto_lootbox": "Affiche un tutoriel concernant les lootbox",
        "help_tuto_buff": "Affiche un tutoriel concernant les buffs",
        "help_tuto_consumable": "Affiche un tutoriel concernant les consommables",
        "help_list_buffs": "Affiche la liste des buffs",
        "help_challenge": "Pour provoquer un joueur en duel à mort, bully vs bully",
        "help_fun_challenge": "Pour provoquer un joueur en duel amical, bully vs bully",
        "help_team_challenge": "Pour provoquer un joueur en combat (amical) TEAM vs TEAM",
        "help_explore_dungeon": "Pour explorer un donjon. Très utile pour xp rapidement",
        "help_explore_ruin": "Pour explorer une ruine. Très utile pour obtenir des items et de la monnaie",
        "help_arena": "Pour afficher l'arène",
        "help_club": "Affiche les bullies d'un joueur",
        "help_print_reserve": "Affiche les bullies de la réserve d'un joueur",
        "help_trade": "Pour faire un échange de bullies",
        "help_hire": "Pour engager un NOBODY",
        "help_hire_all": "Pour remplir son club de NOBODY",
        "help_use_consumable": "Pour utiliser un consommable",
        "help_print_consumables": "Pour afficher vos consommables",
        "help_del_conso": "Pour supprimer un consommable",
        "help_snack_machine": "Pour acheter un consommable snack (modifie les stats)",
        "help_water_fountain": "Pour acheter un consommable eau XP",
        "help_custom_help": "Affiche l'aide des commandes par catégorie",
    },
    "en":{
        "join":"Please join the game first ! (!!join)",
        "other_hasnt_joined":"{other} hasn't joined the game.",
        "other_already_joined":"{user} has already joined the game.",
        "cooldown_wait": "You must wait {cd} before using this command again.",
        "arena_bonus_py": "×{bonus} (arena champion bonus)",
        "payday": ("You received {money_emoji} ! +{recu}{money_emoji} {bonus_str}\n"
                   "You have {total_money} {money_emoji}"),
        "bank": "You have {money} {money_emoji}",
        "already_in_action": "You are already in an interaction.",
        "other_is_in_action" : "{user} is already in an interaction.",
        "credits" : "Devs: Flgjfvevdk, Pelvis Presley. Help: Texz, and all the people who tested the game in its early versions. Admin: Flgjfvevdk",
        "cant_self_tf":"You can't team challenge yourself.",
        "missing_argument":"Error: Missing required argument `{arg}`.",
        "dg_error_param" : "The parameter 'level' must be a number (or a specific keyword).",
        "dg_greater_0" : "Dungeon level must be greater than 0.",
        "dg_lower_50": "Maximum dungeon level is 50.",
        "dg_pallier":"You must defeat the dungeon level {lvl_pallier} before exploring this dungeon.",
        "ruin_greater_0": "Ruin level must be greater than 0.",
        "ruin_lower_50": "Maximum ruin level is 50.",
        "no_arena" : "No arena found for this server. Please create an arena first.",
        "cant_trade_self": "You can't trade with yourself.",

        #bully 
        "bully_died" : "{bully} died in terrible agony.",
        "bully_lost_lvl" : "{bully} lost {lvl} level(s).",

        #arena
        "arena_enter":"{user} enters the arena!",
        "arena_title_thread":"{user} is in the arena",
        "arena_ask_enter": "{user}, do you want to enter the arena?  (Price = {price} {money_emoji})",
        "arena_label":"Enter The Arena (and pay {price})",
        "arena_no_money": "{user}, you do not have enough {money_emoji} to enter the arena. (Price = {price})",
        "arena_next_teamfight": "Next teamfight against:\n{teamfighters}",
        "arena_reached_rank": "{user}, you have reached rank {rank} in the arena! (reward: {reward} {money_emoji})",
        "arena_no_improve_rank": "{user}, you did not improve your rank in the arena.",
        
        #consumable
        "consumable_aliment_effect":"Debuff **{nerf}** to buff **{buff}** by up to {value}.",
        "consumable_water_rarity_error" : "This water is made for **{water_rarity}** bullies, not **{bully_rarity}**",
        "consumable_water_effect":"{name} : on use, a bully of rarity **{rarity}** will recover a maximum of **{value} levels**.",
        "consumable_too_many_select": (
            "You have too many consumables. "
            "Please select one consumable you own to replace with the new one."
        ),
        "consumable_too_many_destroyed": (
            "You have too many consumables, the new one is destroyed."
        ),
        "consumable_added": (
            "The consumable: {name} has been added to your inventory."
        ),
        "timeout_choose_faster": (
            "Timeout, choose faster next time {user}."
        ),
        "consumable_no_selection": "You didn't select any consumable.",
        "consumable_applied": (
            "Consumable ({name}) has been successfully applied!"
        ),
        "consumable_none": (
            "You don't have any consumables. :("
        ),
        "consumable_do_ruin": "But you may get some from ruins!",
        "consumable_choose_title": "Choose a consumable",
        "consumable_user_title": "{user}'s consumables",
        "consumable_use_command": "!!use_consumable to use one.",
        "consumable_removed" : "The consumable {name} has been removed from your inventory.",

        #dungeon
        "dungeon_enter": "{user} enters {dungeon_name}",
        "dungeon_cancel": "{user} cancelled the fight and left the dungeon.",
        "dungeon_team_left_timeout": "Your team left the dungeon. Choose faster next time {user}.",
        "dungeon_team_left": "Your team left the dungeon.",
        "dungeon_win": "{user} has beaten {dungeon_name}!",
        "dungeon_next_enemy": "Next enemy:\n{enemy}",
        "dungeon_enemy_dead": "{enemy_name} is dead! You progress in the dungeon.",
        "fighter_stay_in_fight": "{fighter_name} stays in fight.",
        "fighter_change_too_slow": "Too slow, {fighter_name} stays in fight.",
        "fighter_change_error": "Error, {fighter_name} stays in fight.",
        "dungeon_highest_ranked": "<@{player_id}> - Highest Dungeon Level Reached: {max_dungeon}",
        "dungeon_not_ranked": "<@{player_id}> - is not ranked in Dungeon.",

        #fight_manager
        "challenge_fight": "{user1} challenges {user2}!",
        "challenge_fight_for_fun": "{user1} challenges {user2} to a fun fight (no death, no xp)!",
        "challenge_teamfight": "{user1} challenges {user2} in a teamfight!",
        "challenge_teamfight_for_fun": "{user1} challenges {user2} to a fun teamfight (no death, no xp)!",
        "challenge_accepted": "Challenge accepted!",
        "challenge_declined": "Challenge declined",
        "fight_cancel": "{user} cancelled the fight",
        "fight_giveup": "{user} gave up the fight",
        "challenge_too_late": "Too late! No fight between {user1} and {user2}.",
        "fight_winner": "{winner} won the fight!",
        "teamfight_winner": "{winner} won the teamfight against {loser}!",
        "challenge_selected_bully":"{user} select {bully} (lvl : {lvl})",
        "gain": "{name} earned {reward}",
        "select_to_late_random":"Too late, a random bully has been selected for {user}.",
        "title_challenge": "{user1} vs {user2}",

        #interact_game
        "already_joined_game": "You have already joined the game! (!!tuto for the turoial)",
        "other_join" : "{user} has joined the game!",
        "welcome_adventure": "Welcome to the adventure! (!!tuto)",
        "invite_join_game": "{user}, do you want to join the game?",
        "referral_reward" : "{user}, you have invited {nb} friends ! You deserve a prize (ask for it :wink:)",
        "max_bullies_reached": "{user}, you cannot have more than {max_bullies} bullies!",
        "new_bully_msg": "You have a new bully: {bully}",
        "choose_bully": "{user}, choose a bully:",
        "selected_bully": "{user} selects {bully}",
        "choose_fighter": "{user}, choose your fighter:",
        "selected_fighter": "{user} selects {bully}.",
        "choose_suicide": "{user}, choose a bully to abandon:",
        "suicide_kill": "{user} abandons {bully}",
        "no_suicide": "{user} didn't abandon any bullies",
        "confirm_suicide": "{user}, do you confirm the definitive abandon of {bully}?",
        "your_bullies": "Your bullies:",
        "you_have_no_bully" : "{user}, you do not have any bullies!",
        "you_receive_gold" : "You have received {money_emoji} ! (+{value}){money_emoji}).",

        #lootbox
        "lootbox_select": "Select a lootbox to open. Bully level = [40-80]%% of the box level.",
        "lootbox_require_dungeon": "{user}, you must beat dungeon level {level} to buy this lootbox",
        "lootbox_not_enough_money": "{user}, you don't have enough {money_emoji} for this box [cost: {cout}{money_emoji}]",
        "lootbox_purchase_success": "{user} has purchased a lootbox and got... {bully} a {rarity}!",
        "lootbox_buff" : " [with : {buff_tag}]",

        #reserve
        "reserve_bullies_info": "{user}, your bullies in reserve:",
        "reserve_max_bullies": "You cannot have more than {max_reserve} bullies in your reserve.",
        "new_bully_reserve": "You have a new bully in reserve: {bully}",
        "bully_moved": "{bully} has been moved to your {target}.",
        "team_full": "Your {target} is already full.",
        "empty_team_or_reserve": "Your team or reserve is empty",
        "active_team" : "active team",
        "reserve" : "reserve",
        "label_send_reserve" :"Send bully to reserve",
        "label_send_team" : "Send bully to team", 
        "label_switch_team_reserve" : "Switch team and reserve",
        "reserve_switch_bullies" : "{bully1} and {bully2} have been switched.",

        #ruine
        "ruin_enter": "{user} enters a mysterious ruin [lvl: {level}]",
        "ruin_enemy_intro": "An enemy stands in your way!\n{enemy}",
        "ruin_enemy_defeated": "{enemy} est mort ! Vous progressez dans la ruine.",
        "ruin_team_timeout": "Your team left the ruin. Choose faster next time {user}.",
        "ruin_cancelled": "{user}, you have cancelled the fight and left the ruin",
        "ruin_bully_error": "Your bully is dead or do not exist.\nYour team left the ruin.",
        "ruin_victory": "Congratulation {user}, you beat the boss!",
        "elixir_of" : "Elixir - {elixir}",
        "found_conso" : "You found a consumable: {name}!",
        "ruin_thread_error": "An error occurred while creating the ruin thread.",
        "found_treasure" : "You found a **treasure**. It contains **{gold}** {money_emoji}!",
        "bully_is_dead" : "{bully} is dead!",

        "trap_strength_intro": "[STRENGTH] The room is filled with large, sharp stones. One must create a path by moving these large stones.",
        "trap_strength_success": "Your bully moved rocks and created a safe path for everyone.",
        "trap_strength_fail": "Moving these rocks has left your bully with numerous wounds and bleeding, but the path is cleared.",
        
        "trap_agility_intro": "[AGILITY] The door to the next room is at the top of a ruined stone staircase. One must climb and tie a rope on top to create a path.",
        "trap_agility_success": "Your bully climbed perfectly and tied a rope on top.",
        "trap_agility_fail": "Climbing has left your bully with numerous wounds and bleeding, but the rope is tied.",
        
        "trap_lethality_intro": "[LETHALITY] A terrifying creature is sleeping in the room. One must assassinate it to create a safe path.",
        "trap_lethality_success": "Your bully stabbed the creature, which died instantly.",
        "trap_lethality_fail": "Your bully stabbed the creature, but it didn't instantly die, and hurt your bully.",
        
        "trap_viciousness_intro": "[VICIOUSNESS] The room is full of traps. One must identify them and find a safe path.",
        "trap_viciousness_success": "Your bully identified every trap and found a safe path for everyone.",
        "trap_viciousness_fail": "Your bully was wounded by many traps but ended up finding a safe path.",

        #shop
        "shop_dm_error": "This command can only be used in a server, not in a DM.",
        "shop_not_open": "The shop is not open in this server. Ask an admin to open it.",
        "shop_restocking": "The shop is restocking. Please wait <{seconds} seconds>.",
        "shop_closed_message": "Shop is closed. See you again!",
        "shop_purchase_success": "{user} has purchased {bully} for {cost}{money_emoji}!",
        "shop_bully_not_available" : "This bully is no longer available (sorry {user})",
        "shop_not_enough_money" : "{user}, you don't have enough {money_emoji} to buy {bully}. Cost: {cost}{money_emoji}",
        "bully_in_shop" : "Bullies in shop: ",
        "price" : "Price: {cost} {money_emoji}",

        # supply_bully - Snack Machine
        "snack_bonus_select": "Select your **bonus** stat:",
        "snack_bonus_timeout": "Timeout during bonus selection. Please try again.",
        "snack_malus_select": "Select your **malus** stat:",
        "snack_malus_timeout": "Timeout during malus selection. Please try again.",
        "snack_conso_not_find": "No consumable found.",
        "conso_not_enough_money": "You don't have enough {money_emoji}.",
        "conso_value_prompt": "{user}, please respond with a number corresponding to the desired consumable level:",
        "conso_level_timeout": "Timeout during level input. Operation cancelled.",
        "conso_invalid_value": "The value entered is not a valid integer. Operation cancelled.",
        "conso_purchase_confirmation": "Do you want to purchase **{name}[{value}]** for {price}{money_emoji}?\nEffect: {effect}",
        "conso_purchase_success": "You have purchased **{name}[{value}]** for {price} {money_emoji}!",

        # supply_bully - Water Fountain
        "water_name": "Water XP - {rarity} - {value} LVL",
        "water_rarity_select": "Select the **rarity** of the Water XP:",
        "water_rarity_timeout": "Timeout during rarity selection. Please try again.",
        "water_rarity_selected": "Rarity selected: **{rarity_name}**",

        # trades
        "trade_offer": "{user1} wants to trade with {user2}!",
        "trade_timeout": "Too late! No trade between {user1} and {user2}.",
        "trade_start": "The Trade begins",
        "trade_declined": "Trade declined",
        "trade_confirmation": "Do both users confirm the trade? ({user1} and {user2})",
        "trade_confirmation_timeout": "Trade confirmation timed out.",
        "trade_completed": "Trade completed successfully!",
        "trade_canceled": "Trade canceled.",
        "u_offer_b": "{user} offers : {btxt}",
        "trade_impossible":"{user} can't receive {bully}[lvl:{lvl}] because their max dungeon level is {max_dungeon}.",

        #tournament
        "tournament_end": "```The tournament is over! Results: \n{results}```",
        "tournament_recap_fight": "{user1} VS {user2} : {winner} won",
        "tournament_winner": "{user} is the winner or the Sunday tournament with a score of {score}.",
        "tournament_player_score": "{user} : {score} points",

        # Category translations
        "category_Game": "Game",
        "category_Bully": "Bully",
        "category_Fight": "Fight",
        "category_Money": "Money",
        "category_Tuto": "Tutorial",
        "category_Consumable": "Consumable",
        "category_Uncategorized": "Uncategorized Commands",
        "category_Admin": "Admin",
        
        # Command help texts
        "help_join": "Join the game",
        "help_invite": "Invite a friend to join the game",
        "help_payday": "Receive bandages",
        "help_bank": "Display your resources",
        "help_patchnote": "Show recent updates",
        "help_leaderboard": "Show player ranking based on maximum completed dungeon",
        "help_print_shop": "Display this server's shop",
        "help_buy_lootbox": "Buy a lootbox",
        "help_credits": "Display credits",
        "help_sacrifice": "Eliminate a bully from your club",
        "help_tuto": "Display a general tutorial. Use this if you're lost!",
        "help_tuto_all": "Display the list of tutorials. Use this if you're lost!",
        "help_tuto_bully": "Display a tutorial on how bullies work",
        "help_tuto_rarity": "Display a tutorial on bullies rarity",
        "help_tuto_fight": "Display a tutorial on fights",
        "help_tuto_dungeon": "Display a tutorial on dungeons",
        "help_tuto_ruin": "Display a tutorial on ruins",
        "help_tuto_shop": "Display a tutorial on buying bullies",
        "help_tuto_economy": "Display a tutorial on the game's economy",
        "help_tuto_lootbox": "Display a tutorial on lootboxes",
        "help_tuto_buff": "Display a tutorial on buffs",
        "help_tuto_consumable": "Display a tutorial on consumables",
        "help_list_buffs": "Display the list of buffs",
        "help_challenge": "Challenge a player to a death duel, bully vs bully",
        "help_fun_challenge": "Challenge a player to a friendly duel, bully vs bully",
        "help_team_challenge": "Challenge a player to a (friendly) TEAM vs TEAM fight",
        "help_explore_dungeon": "Explore a dungeon. Very useful for quick XP",
        "help_explore_ruin": "Explore a ruin. Very useful for obtaining items and currency",
        "help_arena": "Display the arena",
        "help_club": "Display a player's bullies",
        "help_print_reserve": "Display the bullies in a player's reserve",
        "help_trade": "Exchange bullies with another player",
        "help_hire": "Hire a NOBODY",
        "help_hire_all": "Fill your club with NOBODIES",
        "help_use_consumable": "Use a consumable",
        "help_print_consumables": "Display your consumables",
        "help_del_conso": "Delete a consumable",
        "help_snack_machine": "Buy a snack consumable (modifies stats)",
        "help_water_fountain": "Buy a water XP consumable",
        "help_custom_help": "Display command help by category",
    }
}

def getText(key: str, guild_id: Optional[int] = None, lang: Optional[str] = None, ctx:Optional[Context] = None) -> str:
    """
    Get the text for a given key in the specified language.
    If lang is None, it will use the language of the server (guild_id) or the context (ctx).
    If guild_id is provided, it will use that guild's language.
    If ctx is provided and guild_id is None, it will use the guild ID from the context.
    """
    if lang is None:
        if ctx is not None and guild_id is None:
            guild_id = ctx.guild.id if ctx.guild else None
        lang = language_manager_instance.get_server_language(guild_id)
    return texts[lang][key]

def getTextFromContext(key: str, ctx:Context) -> str:
    guild_id = ctx.guild.id if ctx.guild else None
    return getText(key, guild_id)

def verify_texts_keys() -> bool:
    """
    Verify if the keys in texts["fr"] and texts["en"] are the same.
    Returns True if all keys match, False otherwise.
    """
    fr_keys = set(texts["fr"].keys())
    en_keys = set(texts["en"].keys())
    missing_in_en = fr_keys - en_keys
    missing_in_fr = en_keys - fr_keys

    if not missing_in_en and not missing_in_fr:
        print("All keys match between 'fr' and 'en'.")
        return True

    if missing_in_en:
        print("Keys missing in 'en':", missing_in_en)
    if missing_in_fr:
        print("Keys missing in 'fr':", missing_in_fr)
    return False

def verify_keys_format() -> bool:
    import re
    """
    Verify if every key in both texts["fr"] and texts["en"] matches the format "my_key".
    The keys must consist of only lowercase letters and underscores,
    and cannot start or end with an underscore.
    
    Returns True if all keys match the format, False otherwise.
    """
    pattern = re.compile(r'^[a-z0-9](?:[a-z0-9_]*[a-z0-9])?$')
    invalid_keys = []
    
    for lang_code in texts:
        for key in texts[lang_code]:
            if not pattern.fullmatch(key):
                invalid_keys.append((lang_code, key))
                
    if not invalid_keys:
        print("All keys match the required format.")
        return True

    for lang_code, key in invalid_keys:
        print(f"Invalid key in '{lang_code}': {key}")
    return False



def verify_keys_placeholders() -> bool:
    import re
    """
    Verify if the keys in texts["fr"] and texts["en"] have the same placeholders.
    Returns True if all keys match, False otherwise.
    """
    placeholder_pattern = re.compile(r'{[^}]*}')
    
    fr_keys = set(texts["fr"].keys())
    en_keys = set(texts["en"].keys())
    common_keys = fr_keys & en_keys
    
    mismatched_keys = []
    
    for key in common_keys:
        fr_placeholders = set(placeholder_pattern.findall(texts["fr"][key]))
        en_placeholders = set(placeholder_pattern.findall(texts["en"][key]))
        
        if fr_placeholders != en_placeholders:
            mismatched_keys.append(key)
    
    if not mismatched_keys:
        print("All keys have matching placeholders between 'fr' and 'en'.")
        return True
    
    for key in mismatched_keys:
        print(f"Placeholders mismatch in key '{key}':")
        print(f"  fr: {texts['fr'][key]}")
        print(f"  en: {texts['en'][key]}")
    
    return False

if __name__ == "__main__":
    verify_texts_keys()
    verify_keys_format()
    verify_keys_placeholders()

