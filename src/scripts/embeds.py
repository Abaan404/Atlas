import discord, datetime

from utils.enums import Colour

class Embeds:
    def __init__(self):
        pass

    @staticmethod
    def default(user, description = "", title = "", colour = Colour.INFO) -> discord.Embed:
        embed = discord.Embed(
            title = title,
            description = description,
            colour = colour.value if hasattr(colour, "value") else colour,
        )
        embed.set_footer(
            text = f"{datetime.datetime.utcnow().strftime('%d/%m/%Y | %H:%M')}"
        )
        embed.set_author(
            name = user.name,
            icon_url = user.avatar
        )
        return embed
