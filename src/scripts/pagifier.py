import discord, math, asyncio
from discord.ext import commands
from typing import Iterable
from scripts.database import RadioDB, RoleDB
from utils.enums import Colour

from utils.functions import clamp

class Pagifier:
    def __init__(self, data: Iterable, bot: commands.Bot, user: discord.User, msg: discord.Message, timeout = 30, divider = 7, left = "◀️", right = "▶️"):
        self.divider = divider # number of fields per page
        self.bot = bot
        self.user = user
        self.msg = msg
        self.left = left
        self.right = right
        self.timeout = timeout

        self.embed = msg.embeds[0]
        self._current_page = 1
        self.last_page = math.ceil(len(data)/divider)

        self.data = []
        for npage in range(0, self.last_page * divider, divider): # Seperate list into nested lists of fixed length
            self.data.append(data[npage:npage+divider])

    @property
    def current_page(self):
        return self._current_page

    @current_page.setter
    def current_page(self, value):
        self._current_page = clamp(value, 1, self.last_page)

    async def generate_page_controls(self, delay: int = None):
        await self.change_page()
        await self.msg.add_reaction(self.left)
        await self.msg.add_reaction(self.right)
        try:
            while True:
                reaction, user = await self.bot.wait_for("reaction_add", timeout = self.timeout, check = lambda reaction, user: user == self.user and reaction.message == self.msg and str(reaction.emoji) in [self.left, self.right])
                if str(reaction.emoji) == self.left:
                    await self.change_page(-1)
                elif str(reaction.emoji) == self.right:
                    await self.change_page(1)
                await self.msg.remove_reaction(reaction, user)
        except asyncio.TimeoutError:
            if delay:
                await self.msg.delete(delay = delay)
            else:
                await self.msg.clear_reaction(self.right)
                await self.msg.clear_reaction(self.left)

    async def change_page(self, increment = 0):
        self.embed.clear_fields()
        self.current_page += increment
        try:
            for name, value in self.data[self.current_page - 1]:
                self.embed.add_field(
                    name = name,
                    value = value,
                    inline = False
                )
        except IndexError:
            pass
        self.embed.set_footer(text = f"Page: {self.current_page}/{self.last_page}")
        await self.msg.edit(embed = self.embed)


class PlayerMessage:
    def __init__(self, player, playlist):
        self.player = player
        self.playlist = playlist
        self.bot = player.bot
        self.msg = None

    async def update_player_message(self):
        if not self.player:
            return

        if self.player.message in [message async for message in self.player.text_channel.history(limit=4)]:
            await self.player.message.edit(embed=self.create_playlist_embed())
        else:
            self.player.message = self.msg = await self.player.text_channel.send(embed=self.create_playlist_embed())
            await self.create_player_controls()

    def create_playlist_embed(self):
        embed = discord.Embed(
            title=f"Now Playing: {self.playlist[0]['author']} | {self.playlist[0]['title']}",
            colour=Colour.RADIO.value
        ).set_author(
            name="Radio",
            icon_url=self.bot.user.avatar
        )

        for i, item in enumerate(self.playlist[1:], start=1):
            embed.add_field(
                name=f"{i+1}) {item['author']} | {item['title']}",
                value=f"by <@{item['user']}>",
                inline=False
            )
        embed.set_footer(
            text=self.loop_text()
        )

        return embed

    def loop_text(self):
        match RadioDB(self.player.guild.id).get_loop():
            case "playlist_repeat":
                return "🔁 | Playlist"
            case "track_repeat":
                return "🔁 | Track"
            case "no_repeat":
                return "🔁 | Disabled"

    async def create_player_controls(self):
        await self.player.message.add_reaction("⏯️")
        await self.player.message.add_reaction("⏭️")
        await self.player.message.add_reaction("🔁")

        try:
            # while this instance shares the latest player controls
            while self.msg == self.player.message:
                try:
                    await asyncio.sleep(0.4)  # grace for spamming
                    reaction, user = await self.bot.wait_for("reaction_add", timeout=5,
                        check=lambda reaction, user: not user.bot and reaction.message == self.player.message and str(reaction.emoji) in ["⏭️", "⏯️", "🔁"])
                    await self.player.message.remove_reaction(reaction, user)
                    if not RoleDB(self.player.guild.id).permission_level(user) >= 8:
                        continue
                except asyncio.TimeoutError:
                    continue
                if user.voice:
                    match str(reaction.emoji):
                        case "⏯️":
                            await self.player.set_pause(not self.player.is_paused)
                        case "⏭️":
                            await self.player.stop()
                        case "🔁":
                            RadioDB(self.player.guild.id).cycle_loop()
                            await self.msg.edit(embed=self.msg.embeds[0].set_footer(text=self.loop_text()))
        finally:
            await self.msg.clear_reaction("⏭️")
            await self.msg.clear_reaction("⏯️")
            await self.msg.clear_reaction("🔁")


class VolumeMessage:
    def __init__(self, player):
        self.player = player

    async def update_volume(self, value):
        vol = clamp(self.player.volume + value, 0, 100)
        await self.player.set_volume(vol)

    async def create_volume_controls(self):
        msg = await self.player.text_channel.send(embed=self.create_volume_embed())
        await msg.add_reaction("➕")
        await msg.add_reaction("➖")

        try:
            while True:
                reaction, user = await self.player.bot.wait_for("reaction_add", timeout=5,
                    check=lambda reaction, user: str(reaction.emoji) in ["➕", "➖"] and reaction.message.id == msg.id and not user.bot)
                await msg.remove_reaction(reaction, user)
                if not RoleDB(self.player.guild.id).permission_level(user) >= 8:
                    continue
                match str(reaction):
                    case "➕":
                        await self.update_volume(10)
                    case "➖":
                        await self.update_volume(-10)
                await msg.edit(embed=self.create_volume_embed())
        except asyncio.TimeoutError:
            await msg.delete()

    def create_volume_embed(self):
        return discord.Embed(
            title=f"Player Volume: {self.player.volume}",
            colour=Colour.RADIO.value
        )
