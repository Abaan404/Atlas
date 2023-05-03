import discord
from discord import app_commands
from discord.ext import commands

from scripts.message import AtlasMessage
from scripts.database import RoleDB

BOT_ROLES = {"manager", "radio", "qotd"}

ROLES = {
    "MODERATION": ["manager", "radio"],
    "PING": ["mcupdates", "qotd"]
}


class Roles(commands.Cog):
    """Manage bot roles for users"""

    def __init__(self, bot):
        self.bot = bot

    roles = app_commands.Group(name="roles", description="Manage Roles")

    @roles.command(name="list")
    @app_commands.guild_only()
    @app_commands.checks.cooldown(rate=1, per=2)
    @app_commands.checks.has_permissions(administrator=True)
    async def _list(self, interaction: discord.Interaction):
        """Send a list of available roles"""
        registered_roles = RoleDB(interaction.guild.id).list().items()
        for index, (type, id) in enumerate(registered_roles):
            registered_roles[index] = (f"**{type.lower()}**: <@&{id}>")

        await AtlasMessage(interaction).send_field(
            title="Role List",
            description=f"**Moderation**: Manager, Radio\n**Ping Roles**: QOTD, MCUpdates\n",
            name="Registered Roles",
            value="\n".join(registered_roles) or "No roles are registered"
        )

    @roles.command(name="add")
    @app_commands.guild_only()
    @app_commands.checks.cooldown(rate=1, per=2)
    @app_commands.checks.has_permissions(administrator=True)
    async def _add(self, interaction: discord.Interaction, name: str, role: discord.Role):
        """Register a role to the bot"""
        if name.lower() not in BOT_ROLES:
            await AtlasMessage(interaction).send_error(description=f"**Unknown role!**")
            return

        RoleDB(interaction.guild.id).insert(role.id, name.lower())
        await AtlasMessage(interaction).send(description=f"Set **{name.lower()}** to role {role.mention}")

    @_add.autocomplete("name")
    async def _add_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        return [app_commands.Choice(name=choice, value=choice) for choice in BOT_ROLES if current.lower() in choice.lower()]

    @roles.command(name="remove")
    @app_commands.guild_only()
    @app_commands.checks.cooldown(rate=1, per=2)
    @app_commands.checks.has_permissions(administrator=True)
    async def _remove(self, interaction: discord.Interaction, name: str):
        """Unregister a role from the bot"""
        if name.lower() in BOT_ROLES and (role := RoleDB(interaction.guild.id).remove(name.lower())):
            await AtlasMessage(interaction).send(description=f"Removed role <@&{role}> from **{name.lower()}**")
        else:
            await AtlasMessage(interaction).send_error(description=f"**Unknown role!**")

    @_remove.autocomplete("name")
    async def _remove_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        return [app_commands.Choice(name=choice, value=choice) for choice in BOT_ROLES if current.lower() in choice.lower()]


async def setup(bot):
    await bot.add_cog(Roles(bot))
