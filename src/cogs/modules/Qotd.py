import discord
import datetime
from discord import app_commands
from discord.ext import commands

from scripts.message import AtlasMessage, Colour
from scripts.database import ModuleDB, QotdDB, RoleDB
from scripts.permissions import ModuleDisabled, AtlasPermissions
from utils.enums import Module, Roles


class QOTD(commands.Cog):
    """Question of the day!"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def interaction_check(self, interaction: discord.Interaction):
        if not ModuleDB(interaction.guild.id).is_enabled(Module.QOTD):
            raise ModuleDisabled
        return True


    qotd = app_commands.Group(name="qotd", description="Question of the Day!")

    @qotd.command(name="suggest")
    @app_commands.describe(question="The question to suggest")
    @app_commands.guild_only()
    @app_commands.checks.cooldown(rate=1, per=2)
    async def _suggest(self, interaction: discord.Interaction, question: str):
        """Suggest a question!"""
        QotdDB(interaction.guild.id).suggest(question, interaction.user.id)
        await AtlasMessage(interaction).send_field(
            title="Question Added to the Queue",
            colour=Colour.QOTD,
            name=f"**Q) {question}**",
            value=f"by {interaction.user.mention}"
        )

    @qotd.command(name="pending")
    @app_commands.guild_only()
    @app_commands.checks.cooldown(rate=1, per=2)
    async def _pending(self, interaction: discord.Interaction):
        """List out the questions in the pending queue."""
        length, questions = QotdDB(interaction.guild.id).get_pending()
        questions_formatted = ((f"{i}) {question['question']}", f"by <@{question['user']}>") for i, question in enumerate(questions, start=1))

        await AtlasMessage(interaction).send_page(
            title="QOTD Pending Queue",
            description="Accept/Decline a question with +qotd accept/decline index",
            colour=Colour.QOTD,
            length=length, data=questions_formatted
        )

    @qotd.command(name="queue")
    @app_commands.guild_only()
    @app_commands.checks.cooldown(rate=1, per=2)
    async def _queue(self, interaction: discord.Interaction):
        """List out the questions in the accepted queue."""
        length, questions = QotdDB(interaction.guild.id).get_accepted()
        questions_formatted = ((f"{i}) {question['question']}", f"by <@{question['user']}>") for i, question in enumerate(questions, start=1))

        await AtlasMessage(interaction).send_page(
            title="QOTD Questions Queue",
            colour=Colour.QOTD,
            length=length, data=questions_formatted
        )

    @qotd.command(name="accept")
    @app_commands.describe(index="The index of the question to accept")
    @app_commands.guild_only()
    @app_commands.checks.cooldown(rate=1, per=2)
    @AtlasPermissions.verify_level(Roles.MANAGER)
    async def _accept(self, interaction: discord.Interaction, index: int):
        """Accept a QOTD question."""
        index = max(abs(index), 1) - 1
        if not (data := QotdDB(interaction.guild.id).accept(index)):
            await AtlasMessage(interaction).send_error(title="Invalid Index")
            return

        await AtlasMessage(interaction).send_field(
            title="Question Accepted",
            colour=Colour.QOTD,
            name=f"**Q) {data['question']}**",
            value=f"by <@{data['user']}>"
        )

    @qotd.command(name="decline")
    @app_commands.describe(index="The index of the question to decline")
    @app_commands.guild_only()
    @app_commands.checks.cooldown(rate=1, per=2)
    @AtlasPermissions.verify_level(Roles.MANAGER)
    async def _decline(self, interaction: discord.Interaction, index: int):
        """Decline a QOTD question."""
        index = max(abs(index), 1) - 1
        if not (data := QotdDB(interaction.guild.id).decline(index)):
            await AtlasMessage(interaction).send_error(title="Invalid Index")
            return

        await AtlasMessage(interaction).send_field(
            title="Question Declined",
            colour=Colour.QOTD,
            name=f"**Q) {data['question']}**",
            value=f"by <@{data['user']}>"
        )

    @qotd.command(name="force")
    @app_commands.guild_only()
    @app_commands.checks.cooldown(rate=1, per=2)
    @AtlasPermissions.verify_level(Roles.MANAGER)
    async def _force(self, interaction: discord.Interaction):
        """Force a QOTD if one fails."""
        channel = self.bot.get_channel(ModuleDB(interaction.guild.id).get_config(Module.QOTD, "channel"))
        question = QotdDB(interaction.guild.id).fetch()

        if channel is None or question is None:
            await AtlasMessage(interaction).send_error(title=f"An error has occured! Either the channel doesn't exist or the queue is empty.")
            return

        await AtlasMessage(interaction).send(title=f"A QOTD was sent to {channel.name}", colour=Colour.QOTD)
        role = RoleDB(interaction.guild.id).get('qotd')
        await channel.send(f'<@&{role}>', embed=discord.Embed(colour=Colour.QOTD.value)
            .set_author(name="Question Of The Day")
            .add_field(name=f"Q) {question['question']}", value=f"by <@{question['user']}>")
            .set_footer(text=f"{datetime.datetime.utcnow().strftime('%d/%m/%Y | %H:%M')}")
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(QOTD(bot))
