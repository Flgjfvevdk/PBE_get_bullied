import discord
import asyncio
from discord.ext.commands import Bot, Context, CommandNotFound
from sqlalchemy.ext.asyncio import AsyncSession

from consumable import AlimentEnum
from interact_game import ViewChoice, ViewYesNo
import money
from player_info import Player
from consumable import ConsumableWaterLvl
from bully import Rarity
from all_texts import getText

CHOICE_TIMEOUT = 20

COST_FOOD_VALUE = 10


async def run_snack_machine(ctx: Context, bot:Bot, session: AsyncSession, user: discord.abc.User, player: Player, value:int|None = None) -> None:
    """Gère l'interaction de la Snack Machine : choix d'un bonus et de trois malus."""
    # Définition de la liste de stats
    stats = ["strength", "agility", "lethality", "viciousness"]

    # --- 1. Sélection du BONUS ---
    event_bonus = asyncio.Event()
    bonus_choice: dict[str, str|None] = {"choix": None}

    # Envoi du message pour choisir le bonus
    message_bonus = await ctx.send(content=getText("snack_bonus_select"),
        view=ViewChoice(
            user=user,
            event=event_bonus,
            list_choix=stats,
            list_choix_name=stats,
            variable_pointer=bonus_choice
        )
    )

    try:
        await asyncio.wait_for(event_bonus.wait(), timeout=CHOICE_TIMEOUT)
    except asyncio.TimeoutError:
        await message_bonus.delete()
        await ctx.send(getText("snack_bonus_timeout"))
        # await ctx.send("Timeout lors du choix du bonus. Veuillez réessayer.")
        return

    bonus_stat = bonus_choice["choix"]
    await message_bonus.delete()

    # --- 2. Sélection des 3 MALUS ---
    # On enlève la stat choisie en bonus pour ne pas la proposer comme malus
    available_malus = [s for s in stats if s != bonus_stat]
    
    event_malus = asyncio.Event()
    malus_choice: dict[str, str|None]  = {"choix": None}
    message_malus = await ctx.send(content=getText("snack_malus_select"),
        view=ViewChoice(
            user=user,
            event=event_malus,
            list_choix=available_malus,
            list_choix_name=available_malus,
            variable_pointer=malus_choice
        )
    )
    try:
        await asyncio.wait_for(event_malus.wait(), timeout=CHOICE_TIMEOUT)
    except asyncio.TimeoutError:
        await message_malus.delete()
        await ctx.send(getText("snack_malus_timeout"))
        # await ctx.send("Timeout lors du choix d'un malus. Veuillez réessayer.")
        return

    malus_stat = malus_choice["choix"]
    await message_malus.delete()

    # Affichage du résultat final
    result_message = (
        f"Snack Machine:\n"
        f"Bonus: **{bonus_stat}**\n"
        f"Malus: **{malus_stat}**"
    )
    await ctx.send(result_message)

    # --- 3. Récupération ou demande de la valeur du consommable ---
    if value is None:
        await ctx.send(getText("conso_value_prompt").format(user=user.mention))
        try:
            reply_msg = await bot.wait_for(
                "message",
                timeout=CHOICE_TIMEOUT,
                check=lambda m: m.author == user and m.channel == ctx.channel
            )
        except asyncio.TimeoutError:
            await ctx.send(getText("conso_level_timeout"))
            return

        try:
            value = int(reply_msg.content)
            if value <= 0:
                raise ValueError
        except ValueError:
            await reply_msg.reply(getText("conso_invalid_value"))
            return

    # --- 4. Création du consommable ---
    consumable_created = None
    for aliment in AlimentEnum:
        # Chaque membre de l'énumération possède une valeur de type AlimentType.
        if aliment.value.stat_buff == bonus_stat and aliment.value.stat_nerf == malus_stat:
            consumable_created = aliment.new_conso(value)
            break

    if consumable_created is None:
        await ctx.send(getText("snack_conso_not_find"))
        # await ctx.send("Aucun consommable correspondant n'a été trouvé pour ces choix.")
        return
    
    event_confirm = asyncio.Event()
    var_confirm: dict[str, bool] = {"choix": False}
    price : int = value * COST_FOOD_VALUE
    message_confirm = await ctx.send(
        content=getText("conso_purchase_confirmation").format(name=consumable_created.name, value=consumable_created.value, price=price, money_emoji=money.MONEY_EMOJI, effect=consumable_created.get_effect()),
        # f"Voulez vous achetez : **{consumable_created.name}[{consumable_created.value}]** pour {price}\nEffet: {consumable_created.get_effect()}", 
        view=ViewYesNo(user=user, event=event_confirm, variable_pointer=var_confirm)
    )
    try:
        await asyncio.wait_for(event_confirm.wait(), timeout=CHOICE_TIMEOUT)
        accept:bool = var_confirm["choix"]
    except asyncio.exceptions.TimeoutError as e:
        return
    # await message_confirm.delete()
    if not accept : return

    if(money.get_money_user(player) < price):
        await message_confirm.edit(content=getText("conso_not_enough_money").format(money_emoji=money.MONEY_EMOJI), view=None)
        # await message_confirm.edit(content=f"You don't have enough {money.MONEY_EMOJI}", view=None)
        return

    
    money.give_money(player, - price)
    player.consumables.append(consumable_created)
    await message_confirm.edit(
            content=getText("conso_purchase_success").format(name=consumable_created.name, value=consumable_created.value, price=price, money_emoji=money.MONEY_EMOJI),
            # content=f"Vous avez achetez  **{consumable_created.name}[{consumable_created.value}]** pour {price} {money.MONEY_EMOJI} !",
            view=None)
    await session.commit()


COST_LVL_RARITY:dict[Rarity, int] = {Rarity.TOXIC: 275,
    Rarity.MONSTER: 325,
    Rarity.DEVASTATOR: 375,
    Rarity.SUBLIME: 500
}

async def run_water_fountain(ctx: Context, bot: Bot, session: AsyncSession, user: discord.abc.User, player: Player, value: int | None = None) -> None:
    """Gère l'achat d'un consommable Water XP dans la Water Fountain."""
    # --- 1. Sélection de la rareté ---
    rarities = ["Toxic", "Monster", "Devastator", "Sublime"]
    event_rarity = asyncio.Event()
    rarity_choice: dict[str, str | None] = {"choix": None}

    message_rarity = await ctx.send(
        content=getText("water_rarity_select"),
        # "Select the **rarity** of the Water XP:",
        view=ViewChoice(
            user=user,
            event=event_rarity,
            list_choix=rarities,
            list_choix_name=rarities,
            variable_pointer=rarity_choice
        )
    )

    try:
        await asyncio.wait_for(event_rarity.wait(), timeout=CHOICE_TIMEOUT)
    except asyncio.TimeoutError:
        await message_rarity.delete()
        await ctx.send(getText("water_rarity_timeout"))
        # await ctx.send("Timeout lors du choix de la rareté. Veuillez réessayer.")
        return

    rarity_name = rarity_choice["choix"]
    await message_rarity.edit(content=getText("water_rarity_selected").format(rarity_name=rarity_name))
    if rarity_name is None:
        return
    rarity = Rarity[rarity_name.upper()]  # Conversion en énumération

    # --- 2. Sélection de la valeur du consommable ---
    if value is None:
        message_request = await ctx.send(getText("conso_value_prompt").format(user=user.mention))
        
        try:
            reply_msg = await bot.wait_for(
                "message",
                timeout=CHOICE_TIMEOUT,
                check=lambda m: m.author == user and m.channel == ctx.channel #and m.reference and m.reference.message_id == message_request.id
            )
        except asyncio.TimeoutError:
            await message_request.delete()
            await ctx.send(getText("conso_level_timeout"))
            return

        try:
            value = int(reply_msg.content)
            if value <= 0:
                raise ValueError
        except ValueError:
            await reply_msg.reply(getText("conso_invalid_value"))
            return

        await message_request.delete()

    # --- 3. Création du consommable ---
    water_conso = ConsumableWaterLvl(getText("water_name").format(rarity=rarity_name, value=value), value, rarity)
    # water_conso = ConsumableWaterLvl(f"Water {rarity_name}", value, rarity)

    # --- 4. Confirmation de l'achat ---
    price = value * COST_LVL_RARITY[rarity]
    event_confirm = asyncio.Event()
    var_confirm: dict[str, bool] = {"choix": False}

    message_confirm = await ctx.send(
        content=getText("conso_purchase_confirmation").format(name=water_conso.name, value=water_conso.val, price=price, money_emoji=money.MONEY_EMOJI, effect=water_conso.get_effect()),
        view=ViewYesNo(user=user, event=event_confirm, variable_pointer=var_confirm)
    )

    try:
        await asyncio.wait_for(event_confirm.wait(), timeout=CHOICE_TIMEOUT)
        accept: bool = var_confirm["choix"]
    except asyncio.TimeoutError:
        return

    if not accept:
        return

    # --- 5. Vérification et achat ---
    if money.get_money_user(player) < price:
        await message_confirm.edit(content=getText("conso_not_enough_money").format(money_emoji=money.MONEY_EMOJI), view=None)
        return

    money.give_money(player, -price)
    player.consumables.append(water_conso)
    await message_confirm.edit(content=getText("conso_purchase_success").format(name=water_conso.name, value=water_conso.val, price=price, money_emoji=money.MONEY_EMOJI)
                               , view=None)
    await session.commit()



