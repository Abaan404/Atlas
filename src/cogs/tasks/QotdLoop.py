import discord, datetime, asyncio
from discord.ext import commands, tasks

from scripts.message import Colour
from scripts.database import ModuleDB, QotdDB, RoleDB
from utils.enums import Module

class QOTDLoop(commands.Cog):
    """Internal QOTD loop."""
    def __init__(self, bot):
        self.bot = bot
        self.qotd.start()

    @tasks.loop(minutes = 1) # Not the most ideal solution but it works
    async def qotd(self):
        current_time = datetime.datetime.utcnow().strftime("%H:%M")
        for data in ModuleDB(None).get_guilds_enabled(Module.QOTD):
            if current_time == data["config"]["time"]:
                await self.execute(data)

    @qotd.before_loop
    async def wait(self):
        await self.bot.wait_until_ready()
        await asyncio.sleep(75 - datetime.datetime.now().second) # Start the loop at XX:XX:15

    async def execute(self, data):
        if (channel := self.bot.get_channel(data["config"]["channel"])) is None:
            return
        if (question := QotdDB(data["guild"]).fetch()) is None:
            return
        role = RoleDB(data["guild"]).get('qotd')
        await channel.send(role, embed = discord.Embed(colour = Colour.QOTD.value)
                                         .set_author(name = "Question Of The Day")
                                         .add_field(name = f"Q) {question['question']}", value = f"by <@{question['user']}>")
                                         .set_footer(text = f"{datetime.datetime.utcnow().strftime('%d/%m/%Y | %H:%M')}"))

async def setup(bot):
    await bot.add_cog(QOTDLoop(bot))
