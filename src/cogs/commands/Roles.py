import discord
from discord.ext import commands

from scripts.embeds import Embeds, Colour
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

    @commands.group()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.guild)
    async def roles(self, ctx):
        """Parent command for roles"""
        if ctx.invoked_subcommand is None:
            pass

    @roles.command(name="list")
    async def _list(self, ctx):
        """Send a list of available roles"""
        registered_roles = RoleDB(ctx.guild.id).list().items()
        registered_roles = list(registered_roles)  # make the array mutable
        for index, (type, id) in enumerate(registered_roles):
            registered_roles[index] = (f"**{type.lower()}**: <@&{id}>")

        await ctx.send(embed=Embeds.default(
            user=ctx.author,
            title="Role List",
            description=f"**Moderation**: Manager, Radio\n**Ping Roles**: QOTD, MCUpdates\n"
        ).add_field(
            name="Registered Roles",
            value="\n".join(registered_roles) or "No roles are registered"
        ))

    @roles.command(name="add", aliases=["set"])
    async def _add(self, ctx, name, role: discord.Role):
        """Register a role to the bot"""
        if name.lower() in BOT_ROLES:
            RoleDB(ctx.guild.id).insert(role.id, name.lower())
            await ctx.send(embed=Embeds.default(
                user=ctx.author,
                description=f"Set **{name.lower()}** to role {role.mention}"
            ))
        else:
            await ctx.send(embed=Embeds.default(
                user=ctx.author,
                description=f"**Unknown role!**",
                colour=Colour.ERROR
            ))

    @roles.command(name="remove")
    async def _remove(self, ctx, name):
        """Unregister a role from the bot"""
        if name.lower() in BOT_ROLES and (role := RoleDB(ctx.guild.id).remove(name.lower())):
            await ctx.send(embed=Embeds.default(
                user=ctx.author,
                description=f"Removed role <@&{role}> from **{name.lower()}**"
            ))
        else:
            await ctx.send(embed=Embeds.default(
                user=ctx.author,
                description=f"**Unknown role!**",
                colour=Colour.ERROR
            ))


async def setup(bot):
    await bot.add_cog(Roles(bot))
