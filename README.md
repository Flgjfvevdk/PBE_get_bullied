# Get Bullied

This project contains both a game and a Discord bot to interact with it.

## Requirements

This project has multiple dependencies:
- Python >=3.10 (3.10 & 3.11 tested).
- `discord` and `python-dotenv` python packages.

## Setup

Before starting the bot, multiple steps need to be done in order ton configure it.
### Bot configuration
A `config/` folder needs to be created.
The folder contains the following configuration:
- `admins.txt` containing a list of the bot admins' discord id on each line.

The `env.example` file needs to be renamed `.env` and contain the following fields:
- `DISCORD_TOKEN` your discord bot token.

### Game Configuration
For the moment, no configuration is available.

## Todo
- [x] Faire une liste de taches
- [ ] thread pour les 1v1 Joueurs (team fight)
- [ ] sélectionner que les images de bully parfaite
- [ ] les bully qui perdent autant de level que leur nombre de brutal loose (true loses)
- [ ] systèmes d'xp combat entre 2 joueurs à modifier
- [ ] faire le système du tournoi du dimanche
- [ ] modifs les buffs qui donnenent + X*LVL (faire des LVL^2)
- [ ] Tester tous les boss (notamment le boss level 50)
- [ ] buff boss level 50 (shadow ?)
- [ ] voir buff devil pocket watch (dmg que en cas de parade ? Pulvérise Le boss Ombre ?)
- [ ] Reward gold à revoir ?
- [ ] Quand les 2 meurts en m^me temps, J1 gagne toujours ?

____ Bonus ____
- [ ] faire un donjon spécial dnd (beholder, hibours, tiamat ... ?)

TBD.

## License

TBD.
