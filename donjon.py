import os
import random
from bully import Bully #ne pas confondre avec bully (le fichier)
import bully #ne pas confondre avec Bully (la class)
import interract_game
import fight_manager
import money
import pickle
import asyncio

import utils

from discord.ext.commands import Context

ID_joueur_en_donjon = []

enemies_possibles_names=["Thyr O'Flan", "Grobrah Le Musclé", "Plu Didié", "Wè wè", "XxX_BOSS_XxX", "Crapcrap", "Fou Fur", "Eric", "le gars qu'on choisit en dernier en sport et qui se venge" ]
size_dungeon = 5

delaie_timeout_dungeon = 30
delaie_delete_thread_fin = 90
coef_xp_win = 0.3

minimum_pv = 4
maximum_pv = 10

def generate_donjon_team(level: int, size:int):
    Enemies = []
    Enemies_pv = []
    for k in range(size):
        rarity = bully.Rarity.TOXIC if random.random() < level/10 else bully.Rarity.NOBODY

        e = Bully(enemies_possibles_names[k], "", [1,1,1,1], rarity=rarity, must_load_image=False)

        point_init = bully.nb_points_init_rarity[rarity.value]
        coef_point_lvl_up = bully.nb_points_lvl_rarity[rarity.value]
        
        if(k < size - 1):
            preterme1 = (size - k - 1)/size
            terme1 = (level * coef_point_lvl_up + point_init) / 3 * preterme1
            preterme2 = (k + 1) / size
            terme2 = (level * coef_point_lvl_up + point_init) * preterme2
            pointBonus = round(terme1 + terme2)
            pv_e = round((maximum_pv - minimum_pv)*(k + 1) / size + minimum_pv)
            lvl_set = round((pointBonus - 4) * pv_e / 10, 1) if pointBonus > 4 else (round(pointBonus / 5 * pv_e / 10, 1))
            #lvl_set = round((level * (k + 1) / size /2) * 10) /10
            Enemies_pv.append(pv_e)
            
        else :
            pointBonus = int(point_init + level * coef_point_lvl_up)
            lvl_set = level
            Enemies_pv.append(maximum_pv)
        
        e.increase_stat_with_seed(pointBonus)
        e.set_level(lvl_set)
        Enemies.append(e)
    return Enemies, Enemies_pv

async def enter_the_dungeon(ctx: Context, user, lvl, bot):
    #Le joueur rentre dans le donjon
    ID_joueur_en_donjon.append(ctx.author.id)

    message = await ctx.channel.send(f"{user.mention} enters the dungeon lvl : {lvl}")
    try :
        thread = await ctx.channel.create_thread(name=f"Dungeon - Level {lvl}", message=message) #type: ignore
    except Exception as e:
        print(e)
        return

    #On met les chemins vers les dossiers du joueur
    player_brute_path = utils.get_player_path(user.id) / "brutes"
    path_players_data = "game_data/player_data"

    #On initialise les pv et xp gagné par les bullies
    pv_team_joueur = [] #pv du bully n°index. Si bully n°index n'existe pas alors -1
    xp_earned_bullies = [] #L'xp gagné par chaque bully
    for k in range(interract_game.number_bully_max):
        file_bully = player_brute_path / f"{k}.pkl"
        if file_bully.exists():
            try :
                with file_bully.open('rb') as pickle_file:
                    bul = pickle.load(pickle_file)
                pv_team_joueur.append(bul.max_pv)
            except Exception as e:
                print (e)
                print("erreur DATATATATATATA")
                await thread.send("probleme DATA") 
                pv_team_joueur.append(10)
            xp_earned_bullies.append(0)
        else :
            pv_team_joueur.append(-1)
            xp_earned_bullies.append(-1)

    #On génère les ennemies
    Enemies, Enemies_pv = generate_donjon_team(lvl, size_dungeon)

    #On set les paramètres du donjon
    current_floor = 0

    #On fait la boucle de combat
    while current_floor < size_dungeon :

        #On affiche le prochain ennemy
        current_enemy = Enemies[current_floor]
        text_enemy_coming = f"An enemy is coming! {current_enemy.get_print(compact_print=True)}"
        await thread.send(f"{bully.mise_en_forme_str(text_enemy_coming)}") 

        #Le player choisit son bully
        try :
            bully_joueur, num_bully_j = await interract_game.player_choose_bully(ctx, user= user, bot= bot, channel_cible= thread, delaie_timeout= delaie_timeout_dungeon)
        except TimeoutError as e:
            await thread.send(f"Your team left the dungeon. Choose faster next time {user}") 
            print (e)
            await exit_dungeon(ctx= ctx, thread= thread, time_bfr_close=delaie_delete_thread_fin)
            return 
        except IndexError as e:
            print(e)
            await thread.send(
                f"[{user}] -> you don't have a bully n°{num_bully_j}\n" #TODO: fix with ui
                "Your team left the dungeon"
            ) 
            await exit_dungeon(ctx= ctx, thread= thread, time_bfr_close=delaie_delete_thread_fin)
            return
        except Exception as e:
            print(e)
            return
        
        #On fait le combat et on récup les pv restants des combattants
        stat_joueur = [bully_joueur.strength, bully_joueur.agility, bully_joueur.lethality, bully_joueur.viciousness]
        stat_enemy = [current_enemy.strength, current_enemy.agility, current_enemy.lethality, current_enemy.viciousness]
        pv_restant_joueur, pv_restant_enemy = await fight_manager.fight_simulation(ctx, bot= bot, 
                                                                    stat_base_1= stat_joueur, stat_base_2= stat_enemy, 
                                                                    name_1= bully_joueur.name, name_2= current_enemy.name, 
                                                                    max_pv_1= pv_team_joueur[num_bully_j], max_pv_2= Enemies_pv[current_floor], 
                                                                    lvl_1= bully_joueur.lvl, lvl_2= current_enemy.lvl,
                                                                    channel_cible=thread)
        
        #On regarde qui a perdu (le joueur ou l'ennemi)
        if(pv_restant_joueur > 0) :
            #Le joueur a gagné

            #On maj les pv des combattants
            pv_team_joueur[num_bully_j] = pv_restant_joueur
            Enemies_pv[current_floor] = 0

            #On calcul les récompenses, on les affiches et on les stocks
            (exp_earned, gold_earned) = fight_manager.reward_win_fight(bully_joueur, current_enemy)
            pretext = ""
            if (exp_earned > 0):
                bully_joueur.give_exp(exp_earned)
                pretext += f"{bully_joueur.name} earned {exp_earned} xp\n"
            if (gold_earned > 0):
                user_gagnant = user
                money.give_money(user_id=user_gagnant.id, montant=gold_earned)
                pretext += f"{user.name} earned {gold_earned}{money.MONEY_ICON}\n"
            xp_earned_bullies[num_bully_j] += exp_earned

            #On envoie le message de succès et on progress dans le dungeon
            await thread.send(f"{pretext}{current_enemy.name} is dead! You progress in the dungeon.")
            current_floor += 1

        else : 
            #Le joueur à perdu

            #On maj les pv des combattants
            pv_team_joueur[num_bully_j] = 0
            Enemies_pv[current_floor] = pv_restant_enemy

            #On tue le bully qui est ded
            await thread.send(f"{bully_joueur.name} died in terrible agony")
            bully_joueur.kill()

    #On est plus dans le combat, le joueur à tryompher

    #On écrit le message de victoire dans les 2 channels
    await ctx.channel.send(f"{user.name} has beaten the level {lvl} dungeon!") 
    await thread.send(f"{user.name} has beaten the level {lvl} dungeon!") 

    #on donne la récompense d'xp
    for k in range(len(xp_earned_bullies)):
        if(pv_team_joueur[k] > 0 and xp_earned_bullies[k] > 0):
            file_path = player_brute_path / f"{str(k)}.pkl"

            try :
                with file_path.open('rb') as pickle_file:
                    bully_joueur = pickle.load(pickle_file)
                bully_joueur.give_exp(round(xp_earned_bullies[k] * coef_xp_win, 1))
            except Exception as e:
                print (e)

    #On maj le record du joueur sur son dungeon si nécessaire
    player_dungeon_stat = utils.get_player_path(user.id) / "playerMaxDungeon.txt"
    try:
        file = player_dungeon_stat.open("r+")  # Open the file for reading and writing
        contents = file.read()

        if contents:
            number = int(contents)
            if number < lvl:
                file.seek(0)  # Move the file pointer to the beginning
                file.write(str(lvl))  # Overwrite the existing number with X
        else:
            file.write(str(lvl))  # Write X to the empty file

    except FileNotFoundError:
        file = open(player_dungeon_stat, "w")  # Create a new file if it doesn't exist
        file.write(str(lvl))

    finally:
        file.close()

    #On quitte le donjon
    await exit_dungeon(ctx= ctx, thread= thread, time_bfr_close=delaie_delete_thread_fin)
    return


# async def fight_enemy_dungeon(ctx: Context, bot, bully_joueur, bully_enemy, pv_joueur, pv_enemy, channel_cible=None):
#     """
#     return : (pv_restant_joueur, pv_restant_bully)
#     """

#     if(channel_cible == None):
#         channel_cible = ctx.channel

#     barre_pv_joueur = fight_manager.value_to_bar_str(pv_joueur)
#     barre_pv_enemy = fight_manager.value_to_bar_str(pv_enemy)

#     text_pv_combat = "\t\tBully 1 : " + bully_joueur.name + "\nhp : " + barre_pv_joueur + "\n\n\t\t\t\tVS\n\n\t\tBully 2 : " + bully_enemy.name + "\nhp : " + barre_pv_enemy
#     action_combat = "Let's get ready to rumble!"
#     text_combat = "```" + text_pv_combat + "\n\n" + action_combat + "```"
    
#     message = await channel_cible.send(text_combat)
#     await asyncio.sleep(fight_manager.fight_msg_time_update)

#     emoji_recap_j1 = ""
#     emoji_recap_j2 = ""
#     tour = random.randint(0,1)
#     while pv_joueur > 0 and pv_enemy > 0 :
#         #On l'action
#         (text_action, pv_perdu_1, pv_perdu_2,  emoji_j1, emoji_j2, tour) = fight_manager.nouvelle_action(bully_joueur, bully_enemy, tour)

#         #On save les emoji pour la frise chronologique
#         emoji_recap_j1+= emoji_j1
#         emoji_recap_j2+= emoji_j2

#         #on maj les parametres des pv 
#         pv_joueur -= pv_perdu_1
#         pv_enemy -= pv_perdu_2
#         barre_pv_joueur = fight_manager.value_to_bar_str(pv_joueur)
#         barre_pv_enemy = fight_manager.value_to_bar_str(pv_enemy)

#         #On fait visuellement la modif de pv : 
#         text_pv_combat = "\t\tBully 1 : " + bully_joueur.name + "\nhp : " + barre_pv_joueur + "\n\t\t\t\t\t" + emoji_recap_j1 + "\n\t\t\t\tVS\n\t\t\t\t\t" + emoji_recap_j2 + "\n\t\tBully 2 : " + bully_enemy.name + "\nhp : " + barre_pv_enemy
#         action_combat = text_action
#         text_combat = "```" + text_pv_combat + "\n\n" + action_combat + "```"
#         await message.edit(content = text_combat)
#         await asyncio.sleep(fight_manager.fight_msg_time_update)

#     return pv_joueur, pv_enemy


async def exit_dungeon(ctx: Context, thread, time_bfr_close):
    ID_joueur_en_donjon.remove(ctx.author.id)
    try :
        await asyncio.sleep(time_bfr_close)
        await thread.delete()
    except Exception as e:
        print(e)
    return


async def str_leaderboard_donjon(ctx: Context, bot):
    dossier_principal = "game_data/player_data"
    text_classement = ""

    classement_joueurs = []
    
    for nom_dossier in os.listdir(dossier_principal):
        chemin_dossier = os.path.join(dossier_principal, nom_dossier)

        # Vérifier si l'élément est un dossier
        if os.path.isdir(chemin_dossier):
            print("on est ici : ", chemin_dossier)
            # Lire le fichier "playerMaxDungeon.txt" s'il existe
            chemin_fichier = os.path.join(chemin_dossier, "playerMaxDungeon.txt")
            print("on lit : ", chemin_fichier)
            if os.path.isfile(chemin_fichier):
                print("c'est un fichier")
                with open(chemin_fichier, "r") as fichier:
                    contenu_fichier = fichier.read()
                    try:
                        classement = int(contenu_fichier)
                    except ValueError:
                        classement = None
                    print("classement, ", classement)

                    # Ajouter le classement du joueur à la liste
                    classement_joueurs.append((nom_dossier, classement))
    
    # Trier la liste des classements des joueurs
    classement_joueurs = sorted(classement_joueurs, key=lambda x: x[1], reverse=True)

    # Afficher le classement des joueurs
    for joueur, classement in classement_joueurs:
        if classement is not None:
            text_classement+=(f"Player : {await bot.fetch_user(int(joueur))} - Highest Dungeon Level Reached: {classement}\n")
        else:
            text_classement+=(f"Player : {int(joueur)}: is not ranked\n")

    return "```Leaderbord dungeon :\n" + text_classement + "```"

