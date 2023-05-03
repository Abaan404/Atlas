import discord
from discord import app_commands
from discord.ext import commands

from scripts.message import AtlasMessage


class Miscellaneous(commands.Cog):
    """Miscellaneous commands"""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="echo")
    @app_commands.checks.cooldown(rate=1, per=10)
    async def _echo(self, interaction: discord.Interaction, content: str):
        """Echos a message."""
        await AtlasMessage(interaction).send(description=content)

    @app_commands.command(name="ping")
    @app_commands.checks.cooldown(rate=1, per=10)
    async def _ping(self, interaction: discord.Interaction):
        """Pings the bot."""
        await AtlasMessage(interaction).send(description=f'**Pong!** *{round(self.bot.latency*1000, 4)} ms*')


async def setup(bot):
    await bot.add_cog(Miscellaneous(bot))
