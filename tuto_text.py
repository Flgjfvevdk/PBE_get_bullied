import shop
import lootbox

patchnote="```\n\
- Get bullied est enfin là !\
```"

tuto = "\
- Vous pouvez recruter des **bullies** (max 5). Ils ont des **statistiques**, un **lvl**, et peuvent se battre à mort. Plus d'infos : **!!tuto_bully**\n\
- Vous pouvez défier les autres joueurs dans un combat bully contre bully (**!!challenge @adversaire**) ou équipe contre équipe (**!!teamfight @adversaire**). Plus d'infos : **!!tuto_fight**\n\
- **!!hire** permet de recruter un bully faible.\n\
- **!!payday** permet de gagner de la monnaie.\n\
- **!!shop** permet d'afficher le magasin et d'acheter des bullies puissants. **!!tuto_shop**.\n\
- **!!lootbox** permet d'acheter une lootbox qui contient un bully. **!!tuto_lootbox**.\n\
- Explorer un donjon (**!!dungeon [lvl du donjon]**) rapporte beaucoup **d'xp** pour les combattants (**!!tuto_dungeon**).\n\
- Explorer une ruine (**!!ruin [lvl de la ruine]**) permet de récupérer des **items**, des **consonmmables** et de la monnaie (**!!tuto_ruin**).\n\
- Les consommables sont utilisables pour modifier les statistiques de vos bullies (!!consommable, !!use_consommable).\n\
"

tuto_bully = "\
- Pour voir vos bullies, il faut faire la commande ***!!club***\n\
- Vous pouvez stocker vos bullies dans votre réserve (***!!reserve***). Tant qu'ils sont dans la réserve, ils sont inutilisables en combat.\n\
- Les bullies sont vos **combattants**. Ils ont 4 statistiques différentes. Vous pouvez consulter la liste de vos bullies en faisant ***!!club***\n\
- Chaque bully a une rareté : **NOBODY** < **TOXIC** < **MONSTER** < **DEVASTATOR** < **SUBLIME**. Sa rareté influence l'augmentation de ses statistiques à chaque level up. \n\
- Quand un bully reçoit autant d'expérience que son lvl, il **level up**.\n\
- Quand il meurt, un bully donne de l'expérience à son tueur. L'xp donné dépend de son level mais aussi de sa rareté. NB : \n \
\t- Plus un bully est rare, moins il va gagner d'xp à chaque combat.\n\
\t- Si un bully à au moins 5 lvl de plus que sa victime, il ne gagne pas d'xp. À la place le joueur reçoit de la monnaie.\n\
- Les NOBODIES révèlent leur potentiel au lvl 10 …. \n\
- Vous pouvez vous débarasser d'un bully en faisant ***!!suicide***\n\
"

tuto_fight = "\
- Pour provoquer un joueur en duel à mort il faut faire la commande ***!!challenge @adversaire***.\n\
- Pour provoquer un joueur en duel amical il faut faire la commande ***!!fun_challenge @adversaire***.\n\
- Pour provoquer un joueur en combat TEAM vs TEAM il faut faire la commande ***!!team_challenge @adversaire***.\n\
- Les bullies se frappent chacun leur tour.\n\
- Les bullies ont 4 statistiques qui influencent le combat.\n\
- Les statistiques permettent de **déclencher des effets** qui affectent le combat. Pour déclencher l'effet, il faut réussir un jet aléatoire dont la probabilité de succès dépend de la statistique mais aussi d'une statistique adverse à laquelle elle est comparée.\n\
- Voici les effets des statistiques :\n\
\t- **Strength** : Elle est comparée à la Strength de l'adversaire et permet de bloquer une attaque.\n\
\t- **Agility** : Elle est comparée à l'Agility de l'adversaire et permet de voler le tour d'attaque de l'adversaire.\n\
\t- **Lethality** : Elle est comparée à la Strength et à la Lethality de l'adversaire. Elle permet de faire des dégâts augmentés (+0, +1 ou +3 selon le nombre de succès).\n\
\t- **Viciousness** : Elle est comparée à la Viciousness. À chaque attaque (même bloquée), l'attaquant peut réduire la valeur de la meilleure statistique adverse. Le malus est plus grand si la statistique de l'attaquant est plus faible que celle de l'adversaire. \n\
- Avoir **1 seul point** de plus dans une statistique augmente grandement les chances de réussir les comparaisons. \n \
"


tuto_shop = f"\
- Le shop permet d'acheter des bullies rare.\n\
- Un shop dépend du serveur et est commun à tous les joueurs.\n\
- Le shop reset toutes les {int(shop.SHOP_RESTOCK_TIMEOUT/60)} minutes .\n\
- Voici les probabilités de rareté : \n\
\t- Nobody :  {shop.RARITY_DROP_CHANCES[0]}% \n\
\t- Toxic : {shop.RARITY_DROP_CHANCES[1]}%\n\
\t- Monster : {shop.RARITY_DROP_CHANCES[2]}%\n\
\t- Devastator : {shop.RARITY_DROP_CHANCES[3]}%\n\
\t- Sublime : {shop.RARITY_DROP_CHANCES[4]}%\n\
"

tuto_lootbox = f"\
- Les lootbox permettent de récupérer un bully .\n\
- Une lootbox niveau X, donne un bully niveau X/2.\n\
- Pour acheter une lootbox niveau X, il faut avoir vaincu un donjon au minimum niveau X.\n\
- Voici les probabilités de rareté : \n\
\t- Nobody :  {lootbox.RARITY_DROP_CHANCES[0]}% \n\
\t- Toxic : {lootbox.RARITY_DROP_CHANCES[1]}%\n\
\t- Monster : {lootbox.RARITY_DROP_CHANCES[2]}%\n\
\t- Devastator : {lootbox.RARITY_DROP_CHANCES[3]}%\n\
\t- Sublime : {lootbox.RARITY_DROP_CHANCES[4]}%\n\
"

tuto_dungeon = " \
- Pour rentrer dans un donjon, il faut faire la commande ***!!dungeon [lvl du donjon]***. Par exemple : ***!!dungeon 10*** \n\
- Une fois dans le donjon, vous allez faire une série de **combats**. À chaque fois, vous pouvez voir votre adversaire et choisir votre combattant.\n\
- Vos bullies **ne régénèrent pas leurs points de vies** avant d'avoir fini ou quitter le donjon.\n\
- Les ennemies dans le donjon donnent moins d'argent en mourant.\n\
- Pendant le combat contre le boss de fin, vous pouvez **switch de combattant** sans permettre au boss de récupérer des points de vies.\n\
- Si vous battez le **boss** du donjon, tous vos combattants **multiplient l'expérience** qu'ils ont reçu.\
"
# - Pour rentrer dans un donjon, il faut utiliser une **key**. Vous en gagnez régulièrement.\n\

tuto_ruin = "\
- Pour rentrer dans une ruine, il faut faire la commande ***!!ruin [lvl de la ruine]***. Par exemple : ***!!ruin 10***\n\
- Pour rentrer dans une ruine, il faut utiliser une key. Vous en gagnez régulièrement.\n\
- Une fois dans la ruine, vous allez faire une série de combats. À chaque fois, vous pouvez voir votre adversaire et choisir votre combattant.\n\
- Vos bullies **ne régénèrent pas leurs points de vies** avant d'avoir fini ou quitter la ruine.\n\
- Les ennemies dans la ruine donnent moins d'argent en mourant.\n\
- Il y a une salle des coffres qui donnent de la monnaie si vous arrivez à l'atteindre.\n\
- Pendant le combat contre le boss de fin, vous pouvez **switch de combattant** sans permettre au boss de récupérer des points de vies.\n\
- Si vous battez le **boss** de fin, vous **récupérez l'item du boss**. \
"


