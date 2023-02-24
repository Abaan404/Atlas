import math
import os
import random
import discord
from discord.ext import commands

from scripts.embeds import Embeds, Colour
from scripts.database import ModuleDB
from utils.enums import Module
from utils.errors import DMBlocked, ModuleNotFound


def get_random_image(category):
    file = random.choice(os.listdir(f"./assets/images/{category}"))
    filename, ext = file.split(".")
    return discord.File(f"./assets/images/{category}/{file}", filename=f"{filename.split('_')[0]}.{ext}")


class Fun(commands.Cog):
    """Random commands i thought and went ok"""

    def __init__(self, bot):
        self.bot = bot

    def cog_check(self, ctx):
        if isinstance(ctx.channel, discord.channel.DMChannel):
            raise DMBlocked
        if not ModuleDB(ctx.guild.id).is_enabled(Module.FUN):
            raise ModuleNotFound
        return True

    @commands.command(name="cat")
    @commands.cooldown(rate=1, per=1, type=commands.BucketType.guild)
    async def _cat(self, ctx):
        """Sends an image of a cat."""
        await ctx.send(embed=Embeds.default(user=ctx.author, colour=Colour.INFO, title="Cats!").set_image(url="attachment://cat.gif"), file=get_random_image("cat"))

    @commands.command(name="dog")
    @commands.cooldown(rate=1, per=1, type=commands.BucketType.guild)
    async def _dog(self, ctx):
        """Sends an image of a dog."""
        await ctx.send(embed=Embeds.default(user=ctx.author, colour=Colour.INFO, title="Dogs!").set_image(url="attachment://dog.gif"), file=get_random_image("dog"))

    @commands.command(name="hug")
    @commands.cooldown(rate=1, per=1, type=commands.BucketType.guild)
    async def _hug(self, ctx, user: discord.Member):
        """Hug someone!"""
        await ctx.send(embed=Embeds.default(user=ctx.author, colour=Colour.INFO, title=f"{ctx.author.name} hugged {user.name}!").set_image(url="attachment://hug.gif"), file=get_random_image("hug"))

    @commands.command(name="slap")
    @commands.cooldown(rate=1, per=1, type=commands.BucketType.guild)
    async def _slap(self, ctx, user: discord.Member):
        """Slap someone!"""
        await ctx.send(embed=Embeds.default(user=ctx.author, colour=Colour.INFO, title=f"{ctx.author.name} slapped {user.name}!").set_image(url="attachment://slap.gif"), file=get_random_image("slap"))

    @commands.command(name="pat")
    @commands.cooldown(rate=1, per=1, type=commands.BucketType.guild)
    async def _pat(self, ctx, user: discord.Member):
        """Pat someone!"""
        await ctx.send(embed=Embeds.default(user=ctx.author, colour=Colour.INFO, title=f"{ctx.author.name} patted {user.name}!").set_image(url="attachment://pat.gif"), file=get_random_image("pat"))

    @commands.command(name="dice", aliases=["roll"])
    @commands.cooldown(rate=1, per=1, type=commands.BucketType.guild)
    async def _dice(self, ctx):
        """Roll a dice!"""
        await ctx.send(embed=Embeds.default(user=ctx.author, colour=Colour.INFO, title=f"{ctx.author.name} rolled a dice!", description=f"The number is {random.randint(1,6)}"))

    @commands.command(name="rps")
    @commands.cooldown(rate=1, per=1, type=commands.BucketType.guild)
    async def _rps(self, ctx, type):
        """Play the world famous game Rocks, Papers and Scissors with someone!"""
        playables = ["rock", "paper", "scissors"]
        if type.lower() not in playables:
            return

        response = random.randint(0, 2)
        if type == playables[response+1 if response != 2 else 0]:
            embed = Embeds.default(user=ctx.author, colour=Colour.INFO,
                                   title=f"{ctx.author.name} plays {type.lower()}!", description=f"The bot played **{playables[response]}**, You Win!")
        elif type == playables[response-1]:
            embed = Embeds.default(user=ctx.author, colour=Colour.INFO,
                                   title=f"{ctx.author.name} plays {type.lower()}!", description=f"The bot played **{playables[response]}**, You Lose!")
        else:
            embed = Embeds.default(user=ctx.author, colour=Colour.INFO,
                                   title=f"{ctx.author.name} plays {type.lower()}!", description=f"The bot played **{playables[response]}**, its a Tie!")
        await ctx.send(embed=embed)

    @commands.command(name="combine", aliases=["merge"])
    @commands.cooldown(rate=1, per=1, type=commands.BucketType.guild)
    async def _combine(self, ctx, user_1: discord.Member, user_2: discord.Member):
        """~~ships~~ combines the usernames of any two users!"""
        combine1 = math.ceil(len(user_1.display_name)/2)
        combine2 = math.ceil(len(user_2.display_name)/2)
        combined = user_1.display_name[:combine1] + user_2.display_name[combine2:]
        await ctx.send(embed=Embeds.default(user=ctx.author, title=f"{user_1.display_name} + {user_2.display_name} = {combined}"), colour=Colour.INFO)

    @commands.command(name="bucket", aliases=["lol", "1"])
    @commands.cooldown(rate=1, per=1, type=commands.BucketType.guild)
    async def _bucket(self, ctx):
        """bucket."""
        await ctx.send(embed=Embeds.default(user=ctx.author, colour=Colour.INFO, title="Bucket", description="bucket").set_image(url="attachment://bucket.png"), file=get_random_image("bucket"))

    # @commands.command()
    # async def russian_roulette(self, ctx):
    #     if random.randint(1, 6) == 1:
    #         await ctx.author.kick

    @commands.command(name="avatar", aliases=["pfp"])
    @commands.cooldown(rate=1, per=1, type=commands.BucketType.guild)
    async def _avatar(self, ctx):
        """Fetch the avatar of a user."""
        try:
            user = ctx.message.mentions[0]
        except IndexError:
            user = ctx.author

        await ctx.send(embed=Embeds.default(user=ctx.author, colour=Colour.INFO).set_image(url=user.avatar))


async def setup(bot):
    await bot.add_cog(Fun(bot))
