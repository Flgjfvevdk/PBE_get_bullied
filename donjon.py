import os
import random
from bully import Bully #ne pas confondre avec bully (le fichier)
import bully #ne pas confondre avec Bully (la class)
from fighting_bully import FightingBully
import interact_game
import fight_manager
import money
import pickle
import asyncio

import utils

from typing import Optional
from typing import List

from discord.ext.commands import Context

ID_joueur_en_donjon = []

enemies_possibles_names=["Thyr O'Flan", "Grobrah Le Musclé", "Plu Didié", "Wè wè", "XxX_BOSS_XxX", "Crapcrap", "Fou Fur", "Eric", "le gars qu'on choisit en dernier en sport et qui se venge" ]
size_dungeon = 5

DUNGEON_CHOICE_TIMEOUT = 30
THREAD_DELETE_AFTER = 90
COEF_XP_WIN = 0.3

minimum_pv = 4
maximum_pv = 10

def generate_donjon_team(level: int, size:int) -> List[FightingBully]:
    # enemies = []
    # enemies_pv = []

    enemies_fighters:List[FightingBully] = []

    for k in range(size):
        rarity = bully.Rarity.TOXIC if random.random() < level/10 else bully.Rarity.NOBODY

        enemy_fighter = Bully(enemies_possibles_names[k], "", [1,1,1,1], rarity=rarity, must_load_image=False)

        point_init = bully.BULLY_RARITY_POINTS[rarity.value]
        coef_point_lvl_up = bully.BULLY_RARITY_LEVEL[rarity.value]
        
        if(k < size - 1):
            preterme1 = (size - k - 1)/size
            terme1 = (level * coef_point_lvl_up + point_init) / 3 * preterme1
            preterme2 = (k + 1) / size
            terme2 = (level * coef_point_lvl_up + point_init) * preterme2
            pointBonus = round(terme1 + terme2)

            pv_enemy = round((maximum_pv - minimum_pv)*(k + 1) / size + minimum_pv)
            lvl_enemy = round((pointBonus - 4) * pv_enemy / 10, 1) if pointBonus > 4 else (round(pointBonus / 5 * pv_enemy / 10, 1))
            #enemies_pv.append(pv_enemy)
            
        else :
            pointBonus = int(point_init + level * coef_point_lvl_up)
            lvl_enemy = level
            pv_enemy = maximum_pv
            #enemies_pv.append(pv_enemy)
        
        enemy_fighter.increase_stat_with_seed(pointBonus)
        enemy_fighter.set_level(lvl_enemy)
        # enemies.append(enemy_fighter)

        stat_enemy = [enemy_fighter.strength, enemy_fighter.agility, enemy_fighter.lethality, enemy_fighter.viciousness]
        new_fighter = FightingBully(combattant= enemy_fighter, name=enemy_fighter.name, lvl= lvl_enemy, pv= pv_enemy, base_stat= stat_enemy.copy(), stat= stat_enemy.copy())

        enemies_fighters.append(new_fighter)
    return enemies_fighters
    return enemies, enemies_pv

async def enter_the_dungeon(ctx: Context, user, lvl, bot) -> None:
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
    #pv_team_joueur = [] #pv du bully n°index. Si bully n°index n'existe pas alors -1
    fighters_joueur:List[Optional[FightingBully]] = []
    xp_earned_bullies = [] #L'xp gagné par chaque bully
    for k in range(interact_game.BULLY_NUMBER_MAX):
        file_bully = player_brute_path / f"{k}.pkl"
        if file_bully.exists():
            try :
                with file_bully.open('rb') as pickle_file:
                    bul = pickle.load(pickle_file)
                new_fighter = FightingBully.create_fighting_bully(b=bul)
                fighters_joueur.append(new_fighter)
                #pv_team_joueur.append(bul.max_pv)
            except Exception as e:
                print (e)
                await thread.send("probleme DATA") 
                raise e
                #pv_team_joueur.append(10)
            xp_earned_bullies.append(0)
        else :
            fighters_joueur.append(None)
            #pv_team_joueur.append(-1)
            xp_earned_bullies.append(-1)

    #On génère les ennemies
    #enemies, enemies_pv = generate_donjon_team(lvl, size_dungeon)
    enemies_fighters = generate_donjon_team(lvl, size_dungeon)

    #On set les paramètres du donjon
    current_floor = 0

    #On fait la boucle de combat
    while current_floor < size_dungeon :

        #On affiche le prochain ennemy
        #current_enemy = enemies[current_floor]
        fighting_bully_enemy = enemies_fighters[current_floor]
        text_enemy_coming = f"An enemy is coming! {fighting_bully_enemy.combattant.get_print(compact_print=True)}"
        await thread.send(f"{bully.mise_en_forme_str(text_enemy_coming)}") 

        #Le player choisit son bully
        try :
            #bully_joueur, num_bully_j = await interact_game.player_choose_bully(ctx, user= user, bot= bot, channel_cible= thread, timeout= DUNGEON_CHOICE_TIMEOUT)
            _, num_bully_j = await interact_game.player_choose_bully(ctx, user= user, bot= bot, channel_cible= thread, timeout= DUNGEON_CHOICE_TIMEOUT)
        except TimeoutError as e:
            print (e)
            await thread.send(f"Your team left the dungeon. Choose faster next time {user}") 
            await exit_dungeon(ctx= ctx, thread= thread, time_bfr_close=THREAD_DELETE_AFTER)
            return 
        except IndexError as e:
            print(e)
            await thread.send(
                f"[{user}] -> You don't have this bully\n" #TODO: fix with ui
                "Your team left the dungeon"
            ) 
            await exit_dungeon(ctx= ctx, thread= thread, time_bfr_close=THREAD_DELETE_AFTER)
            return
        except Exception as e:
            print(e)
            return
        
        #On fait le combat. Les pv sont maj dans la class fightingBully
        fighting_bully_joueur = fighters_joueur[num_bully_j]
        if(fighting_bully_joueur is None or fighting_bully_joueur.pv <= 0):
            await thread.send(f"Your bully is dead or do not exist. \nYour team left the dungeon") 
            await exit_dungeon(ctx= ctx, thread= thread, time_bfr_close=THREAD_DELETE_AFTER)
            return 
        
        await fight_manager.fight_simulation(ctx, bot= bot, 
                                            fighting_bully_1= fighting_bully_joueur, fighting_bully_2= fighting_bully_enemy,
                                            channel_cible= thread)
        
        pv_restant_joueur = fighting_bully_joueur.pv
        bully_joueur = fighting_bully_joueur.combattant
        #On regarde qui a perdu (le joueur ou l'ennemi)
        if(pv_restant_joueur > 0) :
            #Le joueur a gagné

            #On maj les pv des combattants
            #pv_team_joueur[num_bully_j] = pv_restant_joueur
            #enemies_pv[current_floor] = 0

            #On calcul les récompenses, on les affiches et on les stocks
            (exp_earned, gold_earned) = fight_manager.reward_win_fight(bully_joueur, fighting_bully_enemy.combattant)
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
            await thread.send(f"{pretext}{fighting_bully_enemy.name} is dead! You progress in the dungeon.")
            current_floor += 1

        else : 
            #Le joueur à perdu

            #On maj les pv des combattants
            #pv_team_joueur[num_bully_j] = 0
            #enemies_pv[current_floor] = fighting_bully_enemy.pv

            #On tue le bully qui est ded
            await thread.send(f"{bully_joueur.name} died in terrible agony")
            bully_joueur.kill()
            fighters_joueur[num_bully_j] = None

    #On est plus dans le combat, le joueur à tryompher

    #On écrit le message de victoire dans les 2 channels
    await ctx.channel.send(f"{user.name} has beaten the level {lvl} dungeon!") 
    await thread.send(f"{user.name} has beaten the level {lvl} dungeon!") 

    #on donne la récompense d'xp
    for k in range(len(xp_earned_bullies)):
        # if(pv_team_joueur[k] > 0 and xp_earned_bullies[k] > 0):
        fighter = fighters_joueur[k]
        if(isinstance(fighter, FightingBully) and xp_earned_bullies[k] > 0):
            bully_joueur_recompense = fighter.combattant
            bully_joueur_recompense.give_exp(round(xp_earned_bullies[k] * COEF_XP_WIN, 1))

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
    await exit_dungeon(ctx= ctx, thread= thread, time_bfr_close=THREAD_DELETE_AFTER)
    return



async def exit_dungeon(ctx: Context, thread, time_bfr_close) -> None:
    ID_joueur_en_donjon.remove(ctx.author.id)
    try :
        await asyncio.sleep(time_bfr_close)
        await thread.delete()
    except Exception as e:
        print(e)
    return


async def str_leaderboard_donjon(ctx: Context, bot) -> str:
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

