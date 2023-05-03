from discord.ext import commands
from scripts.database import ModuleDB, RoleDB
from utils.errors import PermissionError


def clamp(num, min_value, max_value) -> int:
    return int(max(min(num, max_value), min_value))

def verify_channel(module):
    def predicate(ctx):
        if ModuleDB(ctx.guild.id).get_config(module)["channel"] != ctx.channel.id:
            raise PermissionError
        return True
    return commands.check(predicate)


def has_permissions(role):
    def predicate(interaction):
        if not RoleDB(interaction.guild.id).permission_level(interaction.user) >= role.value:
            raise PermissionError
        return True
    return commands.check(predicate)
