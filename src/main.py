import logging
import os
import discord
from discord.ext import commands

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

        for filename in os.listdir("./cogs"):
            if filename.endswith('.py'):
                await bot.load_extension(f"cogs.{filename[:-3]}")

        await bot.tree.sync()


intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = AtlasBot(command_prefix='+', intents=intents)


@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

# See README.md to find out how to add your bot's token
bot.run(os.getenv("BOT_TOKEN"))
