import discord
from discord import app_commands
from discord.ext import commands

from scripts.message import AtlasMessage


# class HelpCommand(commands.HelpCommand):
#     def __init__(self):
#         super().__init__(
#             command_attrs={
#                 "help": "The help command for the bot",
#                 # "cooldown": commands.Cooldown(1, 1, commands.BucketType.user),
#             }
#         )

#     # Override mapping to recursively get sub-commands too
#     def get_bot_mapping(self):
#         bot = self.context.bot
#         mapping = {cog: cog.walk_commands() for cog in bot.cogs.values()}
#         return mapping

#     def get_command_signature(self, command):
#         return f"{self.context.clean_prefix}{command.qualified_name} {command.signature}"

#     async def send_bot_help(self, mapping):
#         embed = AtlasEmbed.default(
#             user=self.context.author,
#             title="Help Page",
#             description="An [open-source bot](https://github.com/Abaan404/Atlas-Bot) written by <@291439519641894913> in python that does random things. Enjoy! :slight_smile:\n\n**Use +help <category|command(s)> for more details!**"
#         )

#         for cog, commands in mapping.items():
#             commands = list(commands)  # Exhaust Generator
#             if commands:
#                 embed.add_field(
#                     name=f"{cog.qualified_name} | [{len(commands)}]",
#                     value=cog.description,
#                     inline=True
#                 )

#         await self.context.send(embed=embed)

#     async def send_command_help(self, command):
#         embed = AtlasEmbed.default(
#             user=self.context.author,
#             title=f"{command.cog.qualified_name} | {self.get_command_signature(command)}",
#         )
#         embed.add_field(
#             name="Description",
#             value=command.help,
#             inline=False
#         )

#         if command.aliases:
#             embed.add_field(
#                 name="Aliases",
#                 value=', '.join(command.aliases),
#                 inline=False
#             )
#         await self.context.send(embed=embed)

#     async def send_cog_help(self, cog):
#         commands = cog.walk_commands()
#         data = [(self.get_command_signature(command), command.help) for command in commands]

#         embed = AtlasEmbed.default(
#             user=self.context.author,
#             title=f"{cog.qualified_name}",
#             description=cog.description
#         )

#         msg = await self.context.send(embed=embed)
#         pages = Pagifier(data=data, bot=self.context.bot, user=self.context.author, msg=msg)

#         await pages.generate_page_controls()

#     async def send_group_help(self, group):
#         commands = group.walk_commands()
#         data = [(self.get_command_signature(command), command.help)
#                 for command in commands]

#         embed = AtlasEmbed.default(
#             user=self.context.author,
#             title=f"{group.cog_name} | {self.context.clean_prefix}{group.qualified_name}",
#             description=group.help
#         )

#         msg = await self.context.send(embed=embed)
#         pages = Pagifier(data=data, bot=self.context.bot, user=self.context.author, msg=msg)

#         await pages.generate_page_controls()

#     async def send_error_message(self, error):
#         await self.context.send(embed=AtlasEmbed.default(user=self.context.author, description=error))


class Help(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
#         bot.help_command = HelpCommand()
        self.bot.remove_command('help')

    @app_commands.command(name="help")
    @app_commands.checks.cooldown(rate=1, per=2)
    async def _help(self, interaction: discord.Interaction):
        """View the bot's help message."""
        await AtlasMessage(interaction).send_field(
            title="Help Page",
            description="An [open-source bot](https://github.com/Abaan404/Atlas) written by <@291439519641894913> in discord.py and python that does random things. Enjoy! :slight_smile:",
            name="**This command is currently WIP**",
            value="Check back later!"
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Help(bot))
