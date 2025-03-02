import discord
from player_info import Player
from discord.ext.commands import Bot, Context, CommandNotFound

import interact_game
from bully import Bully
from utils.color_str import CText

import asyncio
from typing import Optional, Dict
from all_texts import getText
from utils.locks import PlayerLock

CHOICE_TIMEOUT = 30

async def trade_offer(ctx:Context, user_1:discord.abc.User, user_2:discord.abc.User, player_1: Player, player_2: Player):
    text = getText("trade_offer").format(user1=user_1.mention, user2=user_2.mention)
    event = asyncio.Event()
    var:Dict[str, bool] = {"choix" : False}

    if(user_1 != user_2):
        #On affiche le message
        message = await ctx.channel.send(content=text, view=interact_game.ViewYesNo(user=user_2, event=event, variable_pointer = var))

        #On attend que le joueur clique sur un bouton
        try:
            await asyncio.wait_for(event.wait(), timeout=CHOICE_TIMEOUT)
        except asyncio.exceptions.TimeoutError as e:
            await message.reply(getText("trade_timeout").format(user1=user_1.mention, user2=user_2.mention))
            return
        #On récup le choix
        (trade_accepte):bool = var["choix"]
    else : 
        message = await ctx.channel.send(content=text)
        (trade_accepte) = True

    #On affiche le choix de user_2
    if(not trade_accepte) : 
        await message.reply(getText("trade_declined"))
        return
    
    await message.edit(view=None)
    lock1 = PlayerLock(user_1.id)
    if not lock1.check():
        await message.reply(getText("other_is_in_action").format(user=user_1.name))
        return
    lock2 = PlayerLock(user_2.id)
    if not lock2.check():
        await message.reply(getText("other_is_in_action").format(user=user_2.name))
        return
    
    with lock1, lock2:
        await message.reply(getText("trade_start"))

        bully_1 = await interact_game.select_bully(ctx, user_1, player_1, timeout=CHOICE_TIMEOUT)
        bully_2 = await interact_game.select_bully(ctx, user_2, player_2, timeout=CHOICE_TIMEOUT)
        await ctx.channel.send(trade_str(user_1, user_2, bully_1, bully_2))
        
        # Is trade possible ?
        if bully_1.lvl > player_2.max_dungeon + 1 :
            await ctx.send(getText("trade_impossible").format(user=user_2.name, bully=bully_1.name, lvl=bully_1.lvl, max_dungeon=player_2.max_dungeon))
            # await ctx.channel.send(f"{user_2.name} can't receive {bully_1.name}[lvl:{bully_1.lvl}] because their max dungeon level is {player_2.max_dungeon}.")
            return
        if bully_2.lvl > player_1.max_dungeon + 1 :
            await ctx.send(getText("trade_impossible").format(user=user_1.name, bully=bully_2.name, lvl=bully_2.lvl, max_dungeon=player_1.max_dungeon))
            # await ctx.channel.send(f"{user_1.name} can't receive {bully_2.name}[lvl:{bully_2.lvl}] because their max dungeon level is {player_1.max_dungeon}.")
            return

    # Confirm trade
    event_confirm_1 = asyncio.Event()
    event_confirm_2 = asyncio.Event()
    var_confirm_1: Dict[str, bool] = {"choix": False}
    var_confirm_2: Dict[str, bool] = {"choix": False}
    message_confirm = await ctx.send(content=getText("trade_confirmation").format(user1=user_1.mention, user2=user_2.mention)
                                        , view=interact_game.ViewMultipleYesNo(users=[user_1, user_2], events=[event_confirm_1, event_confirm_2]
                                        , variable_pointers=[var_confirm_1, var_confirm_2]))

    try:
        await asyncio.wait_for(asyncio.gather(event_confirm_1.wait(), event_confirm_2.wait()), timeout=CHOICE_TIMEOUT)
    except asyncio.exceptions.TimeoutError:
        await message_confirm.reply(getText("trade_confirmation_timeout"))
        # await message_confirm.reply("Trade confirmation timed out.")
        return

    if var_confirm_1["choix"] and var_confirm_2["choix"]:
        # Execute trade
        player_1.bullies.remove(bully_1)
        player_2.bullies.remove(bully_2)
        player_1.bullies.append(bully_2)
        player_2.bullies.append(bully_1)
        await ctx.send(getText("trade_completed"))
        # await ctx.channel.send("Trade completed successfully!")
    else:
        await ctx.send(getText("trade_canceled"))
        # await ctx.channel.send("Trade canceled.")
    


def trade_str(user_1:discord.abc.User, user_2:discord.abc.User, bully_1:Bully, bully_2:Bully) -> str:
    txt_b1 = f"{bully_1.get_print(compact_print=True)}"
    txt_b2 = f"{bully_2.get_print(compact_print=True)}"
    return CText(
            getText("u_offer_b").format(user=user_1.name, btxt=txt_b1) + "\n\n"+
            getText("u_offer_b").format(user=user_2.name, btxt=txt_b2)
            # f"{user_1.name} offers : {txt_b1}\n\n"
            # f"{user_2.name} offers : {txt_b2}"
        ).str()


