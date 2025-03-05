import asyncio
from discord import Thread

async def del_thread(thread:Thread, time_bfr_close:int):
    async def dt():
        await thread.leave() # leave the thread and stop responding to any more message here.
        await asyncio.sleep(time_bfr_close)
        await thread.delete()
    asyncio.create_task(dt())