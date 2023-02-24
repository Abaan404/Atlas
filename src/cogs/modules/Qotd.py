import discord
import datetime
from discord.ext import commands

from scripts.pagifier import Pagifier
from scripts.embeds import Colour, Embeds
from scripts.database import ModuleDB, QotdDB, RoleDB
from utils.errors import DMBlocked, ModuleNotFound
from utils.functions import stringify, has_permissions
from utils.enums import Module, Roles

class QOTD(commands.Cog):
    """Question of the day!"""

    def __init__(self, bot):
        self.bot = bot

    def cog_check(self, ctx):
        if isinstance(ctx.channel, discord.channel.DMChannel):
            raise DMBlocked
        if not ModuleDB(ctx.guild.id).is_enabled(Module.QOTD):
            raise ModuleNotFound
        return True

    @commands.group(name="qotd")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.guild)
    async def qotd(self, ctx):
        """Parent command for qotd."""
        if ctx.invoked_subcommand is None:
            pass

    @qotd.command(name="suggest", aliases=["ask", "s"])
    async def _suggest(self, ctx, *question):
        """Suggest a question!"""
        question = stringify(question)
        if not question:
            return

        QotdDB(ctx.guild.id).suggest(question, ctx.author.id)
        await ctx.send(embed=Embeds.default(
            user=ctx.author,
            title="Question Added to the Queue",
            colour=Colour.QOTD
        ).add_field(name=f"**Q) {question}**", value=f"by {ctx.author.mention}"))

    @qotd.command(name="pending", aliases=["p"])
    async def _pending(self, ctx):
        """List out the questions in the pending queue."""
        msg = await ctx.send(embed=Embeds.default(
            user=ctx.author,
            title="QOTD Pending Queue",
            description="Accept/Decline a question with +qotd accept/decline index",
            colour=Colour.QOTD
        ))

        questions = QotdDB(ctx.guild.id).get_pending()
        for i, question in enumerate(questions):
            questions[i] = (f"{i+1}) {question['question']}", f"by <@{question['user']}>")

        pages = Pagifier(data=questions, bot=self.bot, user=ctx.author, msg=msg)
        await pages.generate_page_controls()

    @qotd.command(name="queue", aliases=["q"])
    async def _queue(self, ctx):
        """List out the questions in the accepted queue."""
        msg = await ctx.send(embed=Embeds.default(
            user=ctx.author,
            title="QOTD Questions Queue",
            colour=Colour.QOTD
        ))
        questions = QotdDB(ctx.guild.id).get_accepted()

        for i, question in enumerate(questions):
            questions[i] = (f"{i+1}) {question['question']}", f"by <@{question['user']}>")

        pages = Pagifier(data=questions, bot=self.bot, user=ctx.author, msg=msg)
        await pages.generate_page_controls()

    @qotd.command(name="accept", alises=["add"])
    @has_permissions(Roles.MANAGER)
    async def _accept(self, ctx, index: int):
        """Accept a QOTD question."""
        index = abs(index) - 1
        if not (data := QotdDB(ctx.guild.id).accept(index)):
            return

        await ctx.send(embed=Embeds.default(
            user=ctx.author,
            title="Question Accepted",
            colour=Colour.QOTD
        ).add_field(
            name=f"**Q) {data['question']}**",
            value=f"by <@{data['user']}>"
        ))

    @qotd.command(name="decline", alises=["remove"])
    @has_permissions(Roles.MANAGER)
    async def _decline(self, ctx, index: int):
        """Decline a QOTD question."""
        index = abs(index) - 1
        if not (data := QotdDB(ctx.guild.id).decline(index)):
            return

        await ctx.send(embed = Embeds.default(
            user=ctx.author,
            title="Question Declined",
            colour=Colour.QOTD
        ).add_field(
            name=f"**Q) {data['question']}**",
            value=f"by <@{data['user']}>"
        ))

    @qotd.command(name="force")
    @has_permissions(Roles.MANAGER)
    async def _force(self, ctx):
        """Force a QOTD if one fails."""
        channel = self.bot.get_channel(ModuleDB(ctx.guild.id).get_config(Module.QOTD)["channel"])
        question = QotdDB(ctx.guild.id).fetch()

        if channel is None or question is None:
            return

        role = RoleDB(ctx.guild.id).get('qotd')
        await channel.send(role, embed=discord.Embed(colour=Colour.QOTD.value)
                           .set_author(name="Question Of The Day")
                           .add_field(name=f"Q) {question['question']}", value=f"by <@{question['user']}>")
                           .set_footer(text=f"{datetime.datetime.utcnow().strftime('%d/%m/%Y | %H:%M')}"))


async def setup(bot):
    await bot.add_cog(QOTD(bot))
