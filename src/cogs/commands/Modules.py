import discord
import re
from discord import app_commands
from discord.ext import commands

from scripts.message import AtlasMessage
from scripts.database import ModuleDB

from utils.enums import Module
from utils.errors import ModuleNotFound


class Modules(commands.Cog):
    """Load/Unload modules from the bot"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    modules = app_commands.Group(name="modules", description="Enable features for your server!")
    enable = app_commands.Group(name="enable", description="enable a module", parent=modules)

    @enable.command(name="fun")
    @app_commands.guild_only()
    @app_commands.checks.cooldown(rate=1, per=2)
    @app_commands.checks.has_permissions(administrator=True)
    async def _fun(self, interaction: discord.Interaction):
        ModuleDB(interaction.guild.id).enable(Module.FUN)
        await AtlasMessage(interaction).send(title=f"**Enabled Module Fun!**")

    @enable.command(name="blame")
    @app_commands.guild_only()
    @app_commands.checks.cooldown(rate=1, per=2)
    @app_commands.checks.has_permissions(administrator=True)
    async def _blame(self, interaction: discord.Interaction):
        ModuleDB(interaction.guild.id).enable(Module.BLAME)
        await AtlasMessage(interaction).send(title=f"**Enabled Module Blame!**")

    @enable.command(name="radio")
    @app_commands.guild_only()
    @app_commands.checks.cooldown(rate=1, per=2)
    @app_commands.checks.has_permissions(administrator=True)
    async def _radio(self, interaction: discord.Interaction, channel: discord.TextChannel):
        ModuleDB(interaction.guild.id).enable(Module.RADIO, {"channel": channel.id})
        await AtlasMessage(interaction).send(title=f"**Enabled Module Radio!**")

    @enable.command(name="qotd", description="Ensure time is in the format of HH:MM UTC 24h")
    @app_commands.guild_only()
    @app_commands.checks.cooldown(rate=1, per=2)
    @app_commands.checks.has_permissions(administrator=True)
    async def _qotd(self, interaction: discord.Interaction, channel: discord.TextChannel, time: str):
        if not re.search("^(2[0-4]|[0-1|]?[0-9]):([0-5]?[0-9])$", time):
            await AtlasMessage(interaction).send_error(description=f"Invalid Time Format [HH:MM UTC 24h]: {time}")
            return

        ModuleDB(interaction.guild.id).enable(Module.QOTD, {"channel": channel.id, "time": time})
        await AtlasMessage(interaction).send(title=f"**Enabled Module QOTD!**")

    @modules.command(name="disable")
    @app_commands.guild_only()
    @app_commands.checks.cooldown(rate=1, per=2)
    @app_commands.checks.has_permissions(administrator=True)
    async def _disable(self, interaction: discord.Interaction, module: str):
        """Unloads the module from the bot on your server."""
        if not (module := Module.__dict__.get(module.upper())):
            raise ModuleNotFound

        ModuleDB(interaction.guild.id).disable(module)
        await AtlasMessage(interaction).send(f"Disabled Module {module.value}!")

    @_disable.autocomplete("module")
    async def _disable_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        modules = ModuleDB(interaction.guild.id).fetch_enabled_name()
        return [app_commands.Choice(name=choice, value=choice) for choice in modules if current.lower() in choice.lower()]

    @modules.command(name="list")
    @app_commands.guild_only()
    @app_commands.checks.cooldown(rate=1, per=2)
    async def _list(self, interaction: discord.Interaction):
        """List out all available modules on the server."""
        modules = ModuleDB(interaction.guild.id).fetch_enabled_name()
        await AtlasMessage(interaction).send_field(
            title="Modules List",
            description=f" • **Blame** - Blame your friends!\n • **QOTD** - Pings a role at a certain time of the day everyday to ask a question\n • **Fun** - Just a bunch of random commands lol.\n • **Radio** - Play Music!",
            name="Enabled Modules",
            value=" ".join([f'`{module}`' for module in modules]) or "No modules are enabled for this server"
        )


async def setup(bot):
    await bot.add_cog(Modules(bot))
