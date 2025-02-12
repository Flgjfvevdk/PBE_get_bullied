lang = "fr"


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
        "other_is_in_action" : "{other} est déjà en interaction.",
        "thanks" : "Merci à tous ceux qui participent à ce jeu ! (admin : Flgjfvevdk)",
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

        #arena
        "arena_enter":"{user} entre dans l'arène !",
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

        #dungeon
        "dungeon_enter": "{user} entre dans {dungeon_name}",
        "dungeon_cancel": "{user} a annulé le combat et quitté le donjon.",
        "dungeon_team_left_timeout": "Votre équipe a quitté le donjon. Choisissez plus vite la prochaine fois {user}.",
        "dungeon_team_left": "Votre équipe a quitté le donjon.",
        "dungeon_win": "{user} a vaincu {dungeon_name} !",
        "dungeon_next_enemy": "Prochain ennemi :\n{enemy}",
        "dungeon_enemy_dead": "{enemy_name} est mort ! Vous progressez dans le donjon.",
        "dungeon_no_change": "{fighter_name} reste en combat.",
        "dungeon_change_too_slow": "Trop lent, {fighter_name} reste en combat.",
        "dungeon_change_error": "Erreur, {fighter_name} reste en combat.",
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
        #"timeout_choose_fighter": "Temps écoulé, choisissez plus vite la prochaine fois, {user}.",
        "challenge_too_late": "Trop tard ! Aucun combat entre {user1} et {user2}.",
        "fight_winner": "{winner} a gagné le combat !",
        "teamfight_winner": "{winner} a gagné le teamfight !",
        "challenge_selected_bully":"{user} a selectionné {bully} (lvl : {lvl})",
        "gain": "{name} a gagné {reward}",
        "select_to_late_random":"Trop tard, un bully aléatoire a été sélectionné pour {user}.",

        #interact_game
        "already_joined_game": "Vous avez déjà rejoint le jeu !",
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
        "choose_suicide": "{user}, choisissez un bully à sacrifier :",
        "suicide_kill": "{user} tue {bully}",
        "no_suicide": "{user} n'a pas sacrifié de bully",
        "your_bullies": "Vos bullies :",
        "you_have_no_bully" : "{user}, vous n'avez aucun bully.",
        "you_receive_gold" : "Vous avez reçu des {money_emoji} ! (+{value}}{money_emoji})",

        #lootbox
        "lootbox_select": "Sélectionnez une lootbox à ouvrir. Vous obtiendrez un bully avec un niveau deux fois inférieur à celui de la box.",
        # "lootbox_already_in_action": "Vous êtes déjà en action.",
        # "lootbox_join_game": "Veuillez rejoindre le jeu d'abord !",
        "lootbox_require_dungeon": "{user}, vous devez battre le donjon de niveau {level} pour acheter cette lootbox",
        "lootbox_not_enough_money": "{user}, vous n'avez pas assez de {money_emoji} pour cette box [coût : {cout}{money_emoji}]",
        "lootbox_purchase_success": "{user} a acheté une lootbox et a obtenu... {bully} un {rarity}!",

        #reserve
        "reserve_bullies_info": "{user}, vos bullies en réserve :",
        "reserve_max_bullies": "Vous ne pouvez pas avoir plus de {max_reserve} bullies !",
        "new_bully_reserve": "Vous avez un nouveau bully en réserve : {bully}",
        "bullie_moved": "{name} a été déplacé(e) vers votre {target}.",
        "team_full": "Votre {target} est déjà pleine.",
        "empty_team_or_reserve": "Votre équipe ou votre réserve est vide",

        #ruine
        "ruin_enter": "{user} entre dans une ruine mystérieuse [lvl : {level}]",
        "ruin_enemy_intro": "Un ennemi se met en travers de votre chemin !\n{formatted_enemy}",
        "ruin_enemy_defeated": "{enemy_name} est mort ! Vous progressez dans la ruine.",
        "ruin_team_timeout": "Votre équipe a quitté la ruine. Choisissez plus vite la prochaine fois {user}.",
        "ruin_cancelled": "{user} a annulé le combat et quitté la ruine",
        "ruin_bully_dead": "Votre bully est mort ou n'existe pas.\nVotre équipe a quitté la ruine.",
        "ruin_victory": "Félicitations {user}, vous avez battu le boss!",
        "ruin_thread_error": "Une erreur s'est produite lors de la création du fil de discussion de la ruine.",
        
        #shop
        "shop_dm_error": "Cette commande ne peut être utilisée que sur un serveur, pas en MP.",
        "shop_not_open": "Le shop n'est pas ouvert sur ce serveur. Demandez à un admin de l'ouvrir.",
        "shop_restocking": "Le shop se remplit. Veuillez patienter <{seconds} secondes>.",
        "shop_closed_message": "```Le shop est fermé. À bientôt!```",
        "shop_purchase_success": "{user} a acheté {name} pour {cost}{money_emoji}!",

        #supply_bully
        # supply_bully - Snack Machine
        "snack_bonus_select": "Sélectionnez votre stat bonus :",
        "snack_bonus_timeout": "Timeout lors du choix du bonus. Veuillez réessayer.",
        "snack_malus_select": "Sélectionnez un malus :",
        "snack_malus_timeout": "Timeout lors du choix d'un malus. Veuillez réessayer.",
        "snack_value_prompt": "{user}, veuillez répondre avec un nombre correspondant au niveau du consommable souhaité :",
        "snack_level_timeout": "Timeout lors de la saisie du niveau. Opération annulée.",
        "snack_invalid_value": "La valeur saisie n'est pas un nombre entier valide. Opération annulée.",
        "snack_purchase_confirmation": "Voulez-vous acheter : **{name}[{value}]** pour {price} {money_emoji} ?\nEffet : {effect}",
        "snack_not_enough_money": "Vous n'avez pas assez de {money_emoji}.",
        "snack_purchase_success": "Vous avez acheté **{name}[{value}]** pour {price} {money_emoji} !",

        # supply_bully - Water Fountain
        "water_rarity_select": "Sélectionnez la **rareté** de l'eau XP :",
        "water_rarity_timeout": "Timeout lors du choix de la rareté. Veuillez réessayer.",
        "water_rarity_selected": "Rareté sélectionnée : **{rarity_name}**",
        "water_value_prompt": "{user}, répondez avec un **nombre** correspondant au niveau du consommable souhaité.",
        "water_value_timeout": "Timeout lors de la saisie du niveau. Opération annulée.",
        "water_invalid_value": "La valeur saisie n'est pas un nombre entier valide. Opération annulée.",
        "water_purchase_confirmation": "Voulez-vous acheter **{name} [{value}]** pour {price} {money_emoji} ?\nEffet : {effect}",
        "water_not_enough_money": "Vous n'avez pas assez de {money_emoji}.",
        "water_purchase_success": "Vous avez acheté **{name} [{value}]** pour {price} {money_emoji} !",

        # trades
        "trade_offer": "{user1} veut échanger avec {user2} !",
        "trade_timeout": "Trop tard ! Aucun échange entre {user1} et {user2}.",
        "trade_start": "L'échange commence",
        "trade_declined": "Échange refusé",
        "trade_confirmation": "Les deux utilisateurs confirment-ils l'échange ?",
        "trade_confirmation_timeout": "La confirmation de l'échange a expiré.",
        "trade_completed": "Échange terminé avec succès !",
        "trade_canceled": "Échange annulé."

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
        "other_is_in_action" : "{other} is already in an interaction.",
        "thanks":"Thanks to everyone who takes part in this game! (admin : Flgjfvevdk)",
        "cant_self_tf":"You can't team challenge yourself.",
        "missing_argument":"Error: Missing required argument `{arg}`.",
        "dg_error_param" : "The parameter 'level' must be a number (or a specific keyword).",
        "dg_greater_0" : "Dungeon level must be greater than 0.",
        "dg_lower_50": "Maximum dungeon level is 50.",
        "dg_pallier":"You must defeat the dungeon level {lvl_pallier} before exploring this dungeon.",
        "ruin_greater_0 ": "Ruin level must be greater than 0.",
        "ruin_lower_50": "Maximum ruin level is 50.",
        "no_arena" : "No arena found for this server. Please create an arena first.",
        "cant_trade_self": "You can't trade with yourself.",

        #arena
        "arena_enter":"{user} enters the arena!",
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

        #dungeon
        "dungeon_enter": "{user} enters {dungeon_name}",
        "dungeon_cancel": "{user} cancelled the fight and left the dungeon.",
        "dungeon_team_left_timeout": "Your team left the dungeon. Choose faster next time {user}.",
        "dungeon_team_left": "Your team left the dungeon.",
        "dungeon_win": "{user} has beaten {dungeon_name}!",
        "dungeon_next_enemy": "Next enemy:\n{enemy}",
        "dungeon_enemy_dead": "{enemy_name} is dead! You progress in the dungeon.",
        "dungeon_no_change": "{fighter_name} stays in fight.",
        "dungeon_change_too_slow": "Too slow, {fighter_name} stays in fight.",
        "dungeon_change_error": "Error, {fighter_name} stays in fight.",
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
        "fight_giveup" : "{user} gave up the fight",
        #"timeout_choose_fighter": "Timeout, choose faster next time {user}.",
        "challenge_too_late": "Too late! No fight between {user1} and {user2}.",
        "fight_winner": "{winner} won the fight!",
        "teamfight_winner": "{winner} won the teamfight!",
        "challenge_selected_bully":"{user} select {bully} (lvl : {lvl})",
        "gain": "{name} earned {reward}",
        "select_to_late_random":"Too late, a random bully has been selected for {user}.",

        #interact_game
        "already_joined_game": "You have already joined the game!",
        "other_join" : "{user} has joined the game!",
        "welcome_adventure": "Welcome to the adventure! (!!tuto)",
        "invite_join_game": "{user}, do you want to join the game?",
        "referral_reward" : "{user}, you have invited {nb} friends ! You deserve a prize (ask for it :wink:)",
        "max_bullies_reached": "You cannot have more than {max_bullies} bullies!",
        "new_bully_msg": "You have a new bully: {bully}",
        "choose_bully": "{user}, choose a bully:",
        "selected_bully": "{user} selects {bully}",
        "choose_fighter": "{user}, choose your fighter:",
        "selected_fighter": "{user} selects {bully}.",
        "choose_suicide": "{user}, choose a bully to sacrifice:",
        "suicide_kill": "{user} kills {bully}",
        "no_suicide": "{user} didn't kill any bullies",
        "your_bullies": "Your bullies:",
        "you_have_no_bully" : "{user}, you do not have any bullies!",
        "you_receive_gold" : "You have received {money_emoji} ! (+{value}}{money_emoji}).",

        #lootbox
        "lootbox_select": "Select a lootbox to open. You'll get a bully with a level 2 times smaller than the box level.",
        # "lootbox_already_in_action": "You are already in an action.",
        # "lootbox_join_game": "Please join the game first !",
        "lootbox_require_dungeon": "{user}, you must beat dungeon level {level} to buy this lootbox",
        "lootbox_not_enough_money": "{user}, you don't have enough {money_emoji} for this box [cost: {cout}{money_emoji}]",
        "lootbox_purchase_success": "{user} has purchased a lootbox and got... {bully} a {rarity}!",

        #reserve
        "reserve_bullies_info": "{user}, your bullies in reserve:",
        "reserve_max_bullies": "You cannot have more than {max_reserve} bullies!",
        "new_bully_reserve": "You have a new bully in reserve: {bully}",
        "bullie_moved": "{name} has been moved to your {target}.",
        "team_full": "Your {target} is already full.",
        "empty_team_or_reserve": "Your team or reserve is empty",

        #ruine
        "ruin_enter": "{user} enters a mysterious ruin [lvl: {level}]",
        "ruin_enemy_intro": "An enemy stands in your way!\n{formatted_enemy}",
        "ruin_enemy_defeated": "{enemy_name} is dead! You progress in the ruin.",
        "ruin_team_timeout": "Your team left the ruin. Choose faster next time {user}.",
        "ruin_cancelled": "{user} cancelled the fight and left the ruin",
        "ruin_bully_dead": "Your bully is dead or does not exist.\nYour team left the ruin.",
        "ruin_victory": "Congratulation {user}, you beat the boss!",
        "ruin_thread_error": "An error occurred while creating the ruin thread.",

        #shop
        "shop_dm_error": "This command can only be used in a server, not in a DM.",
        "shop_not_open": "The shop is not open in this server. Ask an admin to open it.",
        "shop_restocking": "The shop is restocking. Please wait <{seconds} seconds>.",
        "shop_closed_message": "```Shop is closed. See you again!```",
        "shop_purchase_success": "{user} has purchased {name} for {cost}{money_emoji}!",

        # supply_bully - Snack Machine
        "snack_bonus_select": "Select your **bonus** stat:",
        "snack_bonus_timeout": "Timeout during bonus selection. Please try again.",
        "snack_malus_select": "Select malus:",
        "snack_malus_timeout": "Timeout during malus selection. Please try again.",
        "snack_value_prompt": "{user}, please respond with a number corresponding to the desired consumable level:",
        "snack_level_timeout": "Timeout during level input. Operation cancelled.",
        "snack_invalid_value": "The value entered is not a valid integer. Operation cancelled.",
        "snack_purchase_confirmation": "Do you want to purchase **{name}[{value}]** for {price}{money_emoji}? Effect: {effect}",
        "snack_not_enough_money": "You don't have enough {money_emoji}.",
        "snack_purchase_success": "You have purchased **{name}[{value}]** for {price} {money_emoji}!",

        # supply_bully - Water Fountain
        "water_rarity_select": "Select the **rarity** of the Water XP:",
        "water_rarity_timeout": "Timeout during rarity selection. Please try again.",
        "water_rarity_selected": "Rarity selected: **{rarity_name}**",
        "water_value_prompt": "{user}, please reply with a **number** corresponding to the desired consumable level.",
        "water_value_timeout": "Timeout during level input. Operation cancelled.",
        "water_invalid_value": "The value entered is not a valid integer. Operation cancelled.",
        "water_purchase_confirmation": "Do you want to purchase **{name} [{value}]** for {price} {money_emoji}? Effect: {effect}",
        "water_not_enough_money": "You don't have enough {money_emoji}.",
        "water_purchase_success": "You have purchased **{name} [{value}]** for {price} {money_emoji}!",

        # trades
        "trade_offer": "{user1} wants to trade with {user2}!",
        "trade_timeout": "Too late! No trade between {user1} and {user2}.",
        "trade_start": "The Trade begins",
        "trade_declined": "Trade declined",
        "trade_confirmation": "Do both users confirm the trade?",
        "trade_confirmation_timeout": "Trade confirmation timed out.",
        "trade_completed": "Trade completed successfully!",
        "trade_canceled": "Trade canceled."
    }
}



