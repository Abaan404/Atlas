import re
from discord.ext import commands
from scripts.database import ModuleDB, RoleDB
from utils.errors import PermissionError


def clamp(num, min_value, max_value) -> int:
    return int(max(min(num, max_value), min_value))


def snowflake_id(snowflake: str) -> int:
    return int(snowflake[2:-1])


def stringify(array) -> str:
    return " ".join(array)


def verify_channel(module):
    def predicate(ctx):
        if ModuleDB(ctx.guild.id).get_config(module)["channel"] != ctx.channel.id:
            raise PermissionError
        return True
    return commands.check(predicate)

def has_permissions(role):
    def predicate(ctx):
        if not RoleDB(ctx.guild.id).permission_level(ctx.author) >= role.value:
            raise PermissionError
        return True
    return commands.check(predicate)


async def decay_send(ctx, *args, **kwargs):
    msg = await ctx.send(*args, **kwargs)
    await msg.delete(delay=5)


def format_track_time(length):
    if length < 3600000:  # if less than 01:00:00 minutes
        return f"{length//60000:02}:{(length//1000)%60:02}"
    else:
        return f"{length//3600000:02}:{(length//60000)%60:02}:{(length//1000)%60:02}"

class Regex:
    def match_channel(text): return re.search("^<#(\d+)>$", text)
    def match_user(text): return re.search("^<@(\d+)>$", text)
    def match_snowflake(text): return re.search("^<*(\d+)>$", text)
    def match_https(text, url): return re.search(f"^https:\/\/{url}", text)
    def match_time_24h(text): return re.search("^(2[0-4]|1[0-9]|[1-9]):([1-5]?[0-9])$", text)
