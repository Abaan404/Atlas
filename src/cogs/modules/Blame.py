import discord
from discord import app_commands
from discord.ext import commands

from scripts.message import AtlasMessage
from scripts.database import ModuleDB, BlameDB
from utils.enums import Module
from utils.errors import ModuleNotFound, DMBlocked


class Blame(commands.Cog):
    """Blame your friends!"""

    def __init__(self, bot):
        self.bot = bot

    def cog_check(self, ctx):
        if isinstance(ctx.channel, discord.channel.DMChannel):
            raise DMBlocked
        if not ModuleDB(ctx.guild.id).is_enabled(Module.BLAME):
            raise ModuleNotFound
        return True

    @app_commands.command(name="blame")
    @app_commands.guild_only()
    @app_commands.checks.cooldown(rate=1, per=2)
    async def _blame(self, interaction: discord.Interaction, blamed: discord.Member, reason: str = None):
        """Add a blame to any user of choice!"""
        blame = BlameDB(interaction.guild.id)
        blame.push(blamed.id, interaction.user.id, reason)

        if reason:
            await AtlasMessage(interaction).send(description=f"{blamed.mention} has been blamed for **{reason}**")
        else:
            await AtlasMessage(interaction).send(description=f"{blamed.mention} has been blamed **{blame.count(blamed.id)}** time(s)!")

    @app_commands.command(name="blamelist")
    @app_commands.guild_only()
    @app_commands.checks.cooldown(rate=1, per=2)
    async def _blamelist(self, interaction: discord.Interaction, blamed: discord.Member = None):
        """List out all the blames for a user."""
        blamed = blamed if blamed else interaction.user
        blame = BlameDB(interaction.guild.id)
        length, data = blame.list(blamed.id)

        date_formatted = ((f"{i}) {blames['reason']}", f"by <@{blames['blamer']}>") for i, blames in enumerate(data, start=1))
        await AtlasMessage(interaction).send_page(
            title=f'{blamed.name} has been blamed for...',
            description=f'\nTotal blames: **{blame.count(blamed.id)}**',
            length=length, data=date_formatted
        )

    @app_commands.command(name="blamecount")
    @app_commands.guild_only()
    @app_commands.checks.cooldown(rate=1, per=2)
    async def _blamecount(self, interaction: discord.Interaction, blamed: discord.Member = None):
        """Count the total number of blames on a user."""
        blamed = blamed if blamed else interaction.user
        blame = BlameDB(interaction.guild.id)

        await AtlasMessage(interaction).send(description=f'User {blamed.mention} has been blamed **{blame.count(blamed.id)}** time(s)!')


async def setup(bot):
    await bot.add_cog(Blame(bot))
