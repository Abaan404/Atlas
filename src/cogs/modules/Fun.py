import math
import os
import random
import discord
from discord import app_commands
from discord.ext import commands

from scripts.message import AtlasMessage
from scripts.database import ModuleDB
from scripts.permissions import ModuleDisabled
from utils.enums import Module


def get_random_image(category):
    file = random.choice(os.listdir(f"./assets/images/{category}"))
    filename, ext = file.split(".")
    return discord.File(f"./assets/images/{category}/{file}", filename=f"{filename.split('_')[0]}.{ext}")


class Fun(commands.Cog):
    """Random commands i thought and went ok"""

    def __init__(self, bot):
        self.bot = bot

    async def interaction_check(self, interaction: discord.Interaction):
        if not ModuleDB(interaction.guild.id).is_enabled(Module.FUN):
            raise ModuleDisabled
        return True

    @app_commands.command(name="cat")
    @app_commands.checks.cooldown(rate=1, per=1)
    async def _cat(self, interaction: discord.Interaction):
        """Sends an image of a cat."""
        await AtlasMessage(interaction).send_image(title="Cats!", url="attachment://cat.gif", file=get_random_image("cat"))

    @app_commands.command(name="dog")
    @app_commands.checks.cooldown(rate=1, per=1)
    async def _dog(self, interaction: discord.Interaction):
        """Sends an image of a dog."""
        await AtlasMessage(interaction).send_image(title="Dogs!", url="attachment://dog.gif", file=get_random_image("dog"))

    @app_commands.command(name="hug")
    @app_commands.checks.cooldown(rate=1, per=1)
    async def _hug(self, interaction: discord.Interaction, user: discord.Member):
        """Hug someone!"""
        await AtlasMessage(interaction).send_image(title=f"{interaction.user.name} hugged {user.name}!", url="attachment://hug.gif", file=get_random_image("hug"))

    @app_commands.command(name="slap")
    @app_commands.checks.cooldown(rate=1, per=1)
    async def _slap(self, interaction: discord.Interaction, user: discord.Member):
        """Slap someone!"""
        await AtlasMessage(interaction).send_image(title=f"{interaction.user.name} slapped {user.name}!", url="attachment://slap.gif", file=get_random_image("slap"))

    @app_commands.command(name="pat")
    @app_commands.checks.cooldown(rate=1, per=1)
    async def _pat(self, interaction: discord.Interaction, user: discord.Member):
        """Pat someone!"""
        await AtlasMessage(interaction).send_image(title=f"{interaction.user.name} patted {user.name}!", url="attachment://pat.gif", file=get_random_image("pat"))

    @app_commands.command(name="bucket")
    @app_commands.checks.cooldown(rate=1, per=1)
    async def _bucket(self, interaction: discord.Interaction):
        """bucket."""
        await AtlasMessage(interaction).send_image(title="Bucket", description="bucket", url="attachment://bucket.png", file=get_random_image("bucket"))

    @app_commands.command(name="dice")
    @app_commands.checks.cooldown(rate=1, per=1)
    async def _dice(self, interaction: discord.Interaction):
        """Roll a dice!"""
        await AtlasMessage(interaction).send(title=f"{interaction.user.name} rolled a dice!", description=f"You rolled a {random.randint(1,6)}!")

    @app_commands.command(name="rps")
    @app_commands.describe(type="The item to play")
    @app_commands.checks.cooldown(rate=1, per=1)
    async def _rps(self, interaction: discord.Interaction, type: str):
        """Play the world famous game Rocks, Papers and Scissors with someone!"""
        playables = ["rock", "paper", "scissors"]
        if type.lower() not in playables:
            await AtlasMessage(interaction).send_error(title=f"Invalid item {type}!")
            return

        response = random.randint(0, 2)
        if type == playables[response+1 if response != 2 else 0]:
            await AtlasMessage(interaction).send(title=f"{interaction.user.name} plays {type.lower()}!", description=f"The bot played **{playables[response]}**, You Win!")
        elif type == playables[response-1]:
            await AtlasMessage(interaction).send(title=f"{interaction.user.name} plays {type.lower()}!", description=f"The bot played **{playables[response]}**, You Lose!")
        else:
            await AtlasMessage(interaction).send(title=f"{interaction.user.name} plays {type.lower()}!", description=f"The bot played **{playables[response]}**, its a Tie!")

    @_rps.autocomplete("type")
    async def _type_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        playables = ["rock", "paper", "scissors"]
        return [app_commands.Choice(name=choice, value=choice) for choice in playables if current.lower() in choice.lower()]

    @app_commands.command(name="combine")
    @app_commands.describe(user_1="The first user", user_2="The second user")
    @app_commands.checks.cooldown(rate=1, per=1)
    async def _combine(self, interaction: discord.Interaction, user_1: discord.Member, user_2: discord.Member):
        """combines the usernames of any two users!"""
        length1 = math.ceil(len(user_1.display_name)/2)
        length2 = math.ceil(len(user_2.display_name)/2)
        combined = user_1.display_name[:length1] + user_2.display_name[length2:]
        await AtlasMessage(interaction).send(title=f"{user_1.display_name} + {user_2.display_name} = {combined}")

    @app_commands.command(name="avatar")
    @app_commands.describe(user="The user to fetch the avatar of")
    @app_commands.checks.cooldown(rate=1, per=1)
    async def _avatar(self, interaction: discord.Interaction, user: discord.Member = None):
        """Fetch the avatar of a user."""
        user = user if user else interaction.user
        await AtlasMessage(interaction).send_image(url=user.avatar)


async def setup(bot):
    await bot.add_cog(Fun(bot))
