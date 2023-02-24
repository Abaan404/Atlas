from discord.ext import commands

from scripts.embeds import Colour, Embeds
from scripts.database import ModuleDB
from utils.enums import Module
from utils.errors import ModuleNotFound
from utils.functions import snowflake_id, stringify
from utils.regex import regex_channel, regex_time_24h


class Modules(commands.Cog):
    """Load/Unload modules from the bot"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.group()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.guild)
    async def modules(self, ctx):
        """Parent command for modules."""
        if ctx.invoked_subcommand is None:
            pass

    @modules.command(name="load", aliases=["enable", "add"])
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def _enable(self, ctx, module: str, *args):
        """Loads the module from the bot on your server."""

        match (module := Module.__dict__.get(module.upper())):  # meh am lazy
            case Module.FUN:
                config = {}
                text = ""

            case Module.BLAME:
                config = {}
                text = ""

            case Module.QOTD:
                if len(args) != 2:
                    await ctx.send(embed=Embeds.default(
                        user=ctx.author,
                        description="**Invalid Syntax** +modules enable qotd <channel> <time [HH:MM UTC 24h]>",
                        colour=Colour.ERROR
                    ))
                    return

                if not regex_channel(args[0]):
                    await ctx.send(embed=Embeds.default(
                        user=ctx.author,
                        description="**Invalid Syntax** Unknown Channel",
                        colour=Colour.ERROR
                    ))
                    return

                if not regex_time_24h(args[1]):
                    await ctx.send(embed=Embeds.default(
                        user=ctx.author,
                        description=f"Invalid Time Format [HH:MM UTC 24h]: {args[1]}",
                        colour=Colour.ERROR
                    ))
                    return

                config = {"channel": snowflake_id(args[0]), "time": args[1]}
                text = f"Channel: {args[0]}\nTime: {args[1]}"

            case Module.RADIO:
                if len(args) != 1:
                    await ctx.send(embed=Embeds.default(
                        user=ctx.author,
                        description="**Invalid Syntax** +modules enable radio <channel>",
                        colour=Colour.ERROR
                    ))
                    return

                if not regex_channel(args[0]):
                    await ctx.send(embed=Embeds.default(
                        user=ctx.author, description="**Invalid Syntax** Unknown Channel",
                        colour=Colour.ERROR
                    ))
                    return

                config = {"channel": snowflake_id(args[0])}
                text = f"Channel: {args[0]}"
            case _:
                raise ModuleNotFound

        ModuleDB(ctx.guild.id).enable(module, config)
        await ctx.send(embed=Embeds.default(user=ctx.author, title=f"**Enabled Module {module.value}**\n{text}"))

    @modules.command(name="unload", aliases=["disable", "remove"])
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def _disable(self, ctx, module):
        """Unloads the module from the bot on your server."""
        if not (module := Module.__dict__.get(module.upper())):
            raise ModuleNotFound

        ModuleDB(ctx.guild.id).disable(module)
        await ctx.send(embed=Embeds.default(
            user=ctx.author,
            title=f"Disabled Module {module.value}!",
            colour=Colour.ERROR
        ))

    @modules.command(name="loaded", aliases=["enabled"])
    @commands.guild_only()
    async def _enabled(self, ctx):
        """List out the loaded modules on your server."""
        modules = ModuleDB(ctx.guild.id).fetch_enabled_name()
        if not modules:
            await ctx.send(embed=Embeds.default(
                user=ctx.author, description=f"No modules are enabled for **{ctx.guild.name}**.",
                colour=Colour.ERROR
            ))
        else:
            await ctx.send(embed=Embeds.default(
                user=ctx.author,
                description=f"The enabled modules for **{ctx.guild.name}** are listed below:\n\n {stringify([f'`{x}`' for x in modules])}"
            ))

    @modules.command(name="list")
    async def _list(self, ctx):
        """List out all available modules on the server."""
        await ctx.send(embed=Embeds.default(
            user=ctx.author,
            description="""Available modules, have an idea? Message @Abaan404#9892!\n\n • **Blame** - Blame your friends!\n • **QOTD** - Pings a role at a certain time of the day everyday to ask a question\n • **Fun** - Just a bunch of random commands lol.\n • **Radio** - Play Music!"""
        ))


async def setup(bot):
    await bot.add_cog(Modules(bot))
