import discord
from player_info import Player
from discord.ext.commands import Bot, Context, CommandNotFound

import interact_game
from bully import Bully
from utils.color_str import CText

import asyncio
from typing import Optional, Dict

CHOICE_TIMEOUT = 30

async def trade_offer(ctx:Context, user_1:discord.abc.User, user_2:discord.abc.User, player_1: Player, player_2: Player):
    text = f"{user_1.mention} want to trade with {user_2.mention} !"
    #On créer l'event qui sera set quand le bouton sera cliqué par user_2. La valeur du bouton (de la réponse) sera stocké dans var
    event = asyncio.Event()
    var:Dict[str, bool] = {"choix" : False}

    if(user_1 != user_2):
        #On affiche le message
        message = await ctx.channel.send(content=text, view=interact_game.ViewYesNo(user=user_2, event=event, variable_pointer = var))

        #On attend que le joueur clique sur un bouton
        try:
            await asyncio.wait_for(event.wait(), timeout=CHOICE_TIMEOUT)
        except asyncio.exceptions.TimeoutError as e:
            await message.reply(f"Too late! No trade between {user_1} and {user_2}")
            return
        #On récup le choix
        (trade_accepte):bool = var["choix"]
    else : 
        message = await ctx.channel.send(content=text)
        (trade_accepte) = True

    #On affiche le choix de user_2
    if((trade_accepte)) : 
        await message.reply("The Trade begin")
    else : 
        await message.reply("Trade declined")
        return
    
    bully_1 = await interact_game.select_bully(ctx, user_1, player_1, timeout=CHOICE_TIMEOUT)
    bully_2 = await interact_game.select_bully(ctx, user_2, player_2, timeout=CHOICE_TIMEOUT)
    # await ctx.channel.send(trade_str(user_1, user_2, bully_1, bully_2))
    pass
    #PAS FINI


def trade_str(user_1:discord.abc.User, user_2:discord.abc.User, bully_1:Bully, bully_2:Bully) -> str:
    txt_b1 = f"{bully_1.get_print(compact_print=True)}"
    txt_b2 = f"{bully_2.get_print(compact_print=True)}"
    return CText(
            f"{user_1.name} offers : {txt_b1}"
            f"{user_2.name} offers : {txt_b2}"
        ).str()