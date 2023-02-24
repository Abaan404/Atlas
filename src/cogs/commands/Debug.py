from discord.ext import commands
from scripts.embeds import Embeds
from utils.functions import stringify


class Miscellaneous(commands.Cog):
    """Miscellaneous commands"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="echo")
    @commands.cooldown(rate=1, per=1, type=commands.BucketType.guild)
    async def _echo(self, ctx, *content):
        """Echos a message."""
        await ctx.send(embed=Embeds.default(user=ctx.author, description=stringify(content)))

    @commands.command(name="ping")
    @commands.cooldown(rate=1, per=1, type=commands.BucketType.guild)
    async def _ping(self, ctx):
        """Pings the bot."""
        await ctx.send(embed=Embeds.default(user=ctx.author, description=f'**Pong!** *{round(self.bot.latency*1000, 4)} ms*'))


async def setup(bot):
    await bot.add_cog(Miscellaneous(bot))
