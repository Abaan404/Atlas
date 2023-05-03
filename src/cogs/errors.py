import discord
from discord import app_commands
from discord.ext import commands

from scripts.message import AtlasMessage, Colour
from scripts.permissions import ChannelError, ModuleDisabled, PermissionError


class Error(commands.Cog):
    """Atlas error handling"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot.tree.error(coro=self.__dispatch_to_app_command_handler)

    async def __dispatch_to_app_command_handler(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        self.bot.dispatch("app_command_error", interaction, error)

    @commands.Cog.listener("on_app_command_error")
    async def error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        if isinstance(error, (commands.errors.MissingRequiredArgument, commands.errors.CommandNotFound, commands.errors.UserNotFound)):
            pass
        elif isinstance(error, app_commands.errors.CommandOnCooldown):
            await AtlasMessage(interaction).send_error(description=f'**Slow down!** you can use this command in {error.retry_after:.2f} second(s)', colour=Colour.WARNING)
        elif isinstance(error, ModuleDisabled):
            await AtlasMessage(interaction).send_error(description=f'**Module Disabled**! The module initialized either does not exist or is disabled on this server')
        elif isinstance(error, ChannelError):
            await AtlasMessage(interaction).send_error(description=f'**Invalid Channel!** This command can only be ran in <#{error.channel_id}>')
        elif isinstance(error, (app_commands.errors.MissingPermissions, PermissionError)):
            await AtlasMessage(interaction).send_error(description=f'**Invalid Permissions!** You do not meet the required permissions to use this command')
        elif isinstance(error, app_commands.errors.CommandInvokeError):
            if isinstance(error.original, discord.errors.Forbidden):
                await AtlasMessage(interaction).send_error(description=f'**Insufficient Permissions!** The bot doesn\'t meet the minimum required permission to execute this action!')
            else:
                raise error
        else:
            raise error


async def setup(bot: commands.Bot):
    await bot.add_cog(Error(bot))
