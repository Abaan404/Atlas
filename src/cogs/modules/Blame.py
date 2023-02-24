import discord
from discord.ext import commands

from scripts.pagifier import Pagifier
from scripts.embeds import Embeds
from scripts.database import ModuleDB, BlameDB
from utils.enums import Module
from utils.errors import ModuleNotFound, DMBlocked
from utils.functions import stringify


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

    @commands.command(name="blame")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.guild)
    async def _blame(self, ctx, blamed: discord.User, *reason):
        """Add a blame to any user of choice!"""
        blame = BlameDB(ctx.guild.id)

        if reason := stringify(reason):
            blame.push(blamed.id, ctx.author.id, reason)
            embed = Embeds.default(
                user=ctx.author,
                description=f"{blamed.mention} has been blamed for **{reason}**"
            )
        else:
            blame.push(blamed.id, ctx.author.id)
            embed = Embeds.default(
                user=ctx.author,
                description=f"{blamed.mention} has been blamed **{blame.count(blamed.id)}** time(s)!"
            )

        await ctx.send(embed=embed)

    @commands.command(name="blamelist")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.guild)
    async def _blamelist(self, ctx, blamed: discord.Member = None):
        """List out all the blames for a user."""
        if blamed is None:
            blamed = ctx.message.author
        blame = BlameDB(ctx.guild.id)

        data = blame.list(blamed.id)
        for i, (user, text) in enumerate(data):
            data[i] = (f"{i+1}) {text}", f"by <@{user}>")

        msg = await ctx.send(embed=Embeds.default(
            user=ctx.author,
            title=f'Fetching all blames for user {blamed.name}',
            description=f'\nTotal blames: **{blame.count(blamed.id)}**'
        ))

        pages = Pagifier(bot=self.bot, user=ctx.author, msg=msg, data=data)
        await pages.generate_page_controls()

    @commands.command(name="blamecount")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.guild)
    async def _blamecount(self, ctx, blamed: discord.Member = None):
        """Count the total number of blames on a user."""
        if blamed is None:
            blamed = ctx.message.author
        blame = BlameDB(ctx.guild.id)

        await ctx.send(embed=Embeds.default(
            user=ctx.author,
            description=f'User {blamed.mention} has been blamed **{blame.count(blamed.id)}** time(s)!'
        ))


async def setup(bot):
    await bot.add_cog(Blame(bot))
