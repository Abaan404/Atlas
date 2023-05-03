import logging
import os
import discord

from discord.ext import commands
from scripts.message import AtlasMessage, Colour
from utils.errors import DMBlocked, ModuleNotFound, PermissionError

os.makedirs("logs", exist_ok=True)
handler = logging.FileHandler(filename='./logs/bot.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s]: %(name)s  %(message)s'))
logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
logger.addHandler(handler)

class AtlasBot(commands.Bot):
    async def setup_hook(self) -> None:
        for filename in os.listdir("./cogs/commands"):
            if filename.endswith('.py'):
                await bot.load_extension(f"cogs.commands.{filename[:-3]}")

        for filename in os.listdir("./cogs/modules"):
            if filename.endswith('.py'):
                await bot.load_extension(f"cogs.modules.{filename[:-3]}")

        for filename in os.listdir("./cogs/tasks"):
            if filename.endswith('.py'):
                await bot.load_extension(f"cogs.tasks.{filename[:-3]}")

        await bot.tree.sync()


intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = AtlasBot(command_prefix='+', intents=intents)

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

@bot.event
async def on_tree_error(interaction: discord.Interaction, error):
    if isinstance(error, commands.CommandOnCooldown):
        await AtlasMessage(interaction).send_error(
            description=f'**Slow down!** you can use this command in {error.retry_after:.2f} second(s)',
            colour=Colour.WARNING
        )
    elif isinstance(error, DMBlocked):
        await AtlasMessage(interaction).send_error(
            description=f'**Blocked Channel!** You may not use this command in a Private Channel!',
            colour=Colour.ERROR
        )
    elif isinstance(error, ModuleNotFound):
        await AtlasMessage(interaction).send_error(
            user=interaction.user,
            description=f'**Module Disabled**! The module initialized either does not exist or is disabled on this server.',
            colour=Colour.ERROR
        )
    elif isinstance(error, (commands.errors.MissingRequiredArgument, commands.errors.CommandNotFound, commands.errors.UserNotFound)):
        pass
    elif isinstance(error, (commands.errors.MissingPermissions, PermissionError)):
        await AtlasMessage(interaction).send_error(
            description=f'**Invalid Permissions!** You do not meet the required permissions to use this command.',
            colour=Colour.ERROR
        )
    elif isinstance(error, commands.errors.CommandInvokeError):
        if isinstance(error.original, discord.errors.Forbidden):
            await AtlasMessage(interaction).send_error(
                description=f'**Insufficient Permissions!** The bot doesn\'t meet the minimum required permission to execute this action!',
                colour=Colour.ERROR
            )
        else:
            raise error
    else:
        raise error

# See README.md to find out how to add your bot's token
bot.run(os.getenv("BOT_TOKEN"))
