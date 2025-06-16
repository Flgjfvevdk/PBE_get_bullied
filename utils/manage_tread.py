import asyncio
from discord import Thread,Message, TextChannel
from discord.ext.commands import Context
import discord


async def create_thread(ctx: Context, name: str, message:Message) -> Thread:
    """
    Create a thread with the given name and attached to the given message.
    
    Parameters:
        name: The name of the thread (already formatted)
        message: The message to attach the thread to
        
    Returns:
        Thread: The created thread
    """
    if isinstance(ctx.channel, (TextChannel)):
        thread = await ctx.channel.create_thread(name=name, message=message)
        return thread
    else :
        raise TypeError("Cannot create a thread.")

async def create_thread_if_possible(ctx: Context, name: str, message: Message) -> discord.abc.Messageable:
    """
    Create a thread if possible, otherwise return the channel.

    Parameters:
        name: The name of the thread (already formatted)
        message: The message to attach the thread to

    Returns:
        Thread or TextChannel: The created thread or the channel if thread creation is not possible
    """
    try:
        return await create_thread(ctx, name, message)
    except TypeError:
        return message.channel

async def del_thread(thread:Thread, time_bfr_close:int):
    async def dt():
        await thread.leave() # leave the thread and stop responding to any more message here.
        await asyncio.sleep(time_bfr_close)
        await thread.delete()
    asyncio.create_task(dt())


async def del_thread_if_possible(thread: discord.abc.Messageable, time_bfr_close: int = 30) -> None:
    """
    Delete a thread if it is a Thread, otherwise do nothing.

    Parameters:
        thread: The thread or channel to delete
        time_bfr_close: The amount of time to wait before deletion (in seconds)
    """
    if isinstance(thread, Thread):
        await del_thread(thread, time_bfr_close)
    