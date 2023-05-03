import discord
import datetime
import itertools

from discord.interactions import Interaction

from scripts.database import RadioDB, RoleDB

from utils.enums import Colour
from utils.functions import clamp
from typing import Any, Coroutine, Iterator


class AtlasEmbed:

    @staticmethod
    def default(user, description="", title="", colour=Colour.INFO) -> discord.Embed:
        embed = discord.Embed(
            title=title,
            description=description,
            colour=colour.value if hasattr(colour, "value") else colour,
        )
        embed.set_footer(
            text=f"{datetime.datetime.utcnow().strftime('%d/%m/%Y | %H:%M')}"
        )
        embed.set_author(
            name=user.name,
            icon_url=user.avatar
        )
        return embed

class AtlasPagifier(discord.ui.View):
    def __init__(self, data, timeout, divider, length) -> None:
        self.data = data if isinstance(data, Iterator) else iter(data)
        self.divider = divider  # number of fields per page

        self.cache = []
        self.last_page = (length - 1) // divider + 1
        self._current_page = 0

        super().__init__(timeout=timeout)

    @property
    def current_page(self):
        return self._current_page

    @current_page.setter
    def current_page(self, value):
        self._current_page = clamp(value, 0, self.last_page - 1)
        if self._current_page > len(self.cache) - 1:
            self.cache.append(tuple(itertools.islice(self.data, self.divider))) # fetch the next set of values

    @discord.ui.button(label="◀️", style=discord.ButtonStyle.blurple)
    async def previous_button_callback(self, interaction: discord.Interaction, button: discord.Button):
        await self.change_page(interaction, -1)

    @discord.ui.button(label="▶️", style=discord.ButtonStyle.blurple)
    async def next_button_callback(self, interaction: discord.Interaction, button: discord.Button):
        await self.change_page(interaction, +1)

    def update_embed(self, embed, increment=0):
        embed.clear_fields()
        self.current_page += increment
        for name, value in self.cache[self.current_page]:
            embed.add_field(
                name=name,
                value=value,
                inline=False
            )
        embed.set_footer(text=f"Page: {self.current_page + 1}/{self.last_page}")
        return embed

    async def change_page(self, interaction: discord.Interaction, increment=0):
        embed = self.update_embed(interaction.message.embeds[0], increment=increment)
        await interaction.response.edit_message(embed=embed)

class AtlasPlayerControl(discord.ui.View):
    def __init__(self, player, playlist):
        self.player = player
        self.playlist = playlist
        super().__init__(timeout=None)

    async def interaction_check(self, interaction: Interaction) -> Coroutine[Any, Any, bool]:
        if not (interaction.user.voice and interaction.user.voice.channel == self.player.channel):
            await AtlasMessage(interaction).send_error(title="You are not connected to the bot's channel!")
            return

        if not RoleDB(self.player.guild.id).permission_level(interaction.user) >= 8:
            await AtlasMessage(interaction).send_error(title="You do not meet the permissions to run this command!")
            return

        return True

    @discord.ui.button(label="⏯️", style=discord.ButtonStyle.primary)
    async def pause_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.player.set_pause(not self.player.is_paused)
        await interaction.response.defer()

    @discord.ui.button(label="⏯️", style=discord.ButtonStyle.primary)
    async def skip_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.player.stop()
        await interaction.response.defer()

    @discord.ui.button(label="🔁", style=discord.ButtonStyle.primary)
    async def loop_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        RadioDB(self.player.guild.id).cycle_loop()
        await interaction.response.edit_message(embed=interaction.message.embeds[0].set_footer(text=self.loop_text()))

    async def update_player_controls(self):
        if not self.player:
            return

        if self.player.message in [message async for message in self.player.text_channel.history(limit=4)]:
            await self.player.message.edit(embed=self.update_embed(), view=self)
        else:
            if self.player.message:
                await self.player.message.delete()
            self.player.message = await self.player.text_channel.send(embed=self.update_embed(), view=self)

    def update_embed(self):
        embed = discord.Embed(
            title=f"Now Playing: {self.playlist[0]['author']} | {self.playlist[0]['title']}",
            colour=Colour.RADIO.value
        )
        for i, item in enumerate(self.playlist[1:], start=2):
            embed.add_field(
                name=f"{i}) {item['author']} | {item['title']}",
                value=f"by <@{item['user']}>",
                inline=False
            )
        embed.set_author(name="Radio", icon_url=self.player.bot.user.avatar)
        embed.set_footer(text=self.loop_text())

        return embed

    def loop_text(self):
        match RadioDB(self.player.guild.id).get_loop():
            case "playlist_repeat":
                return "🔁 | Playlist"
            case "track_repeat":
                return "🔁 | Track"
            case "no_repeat":
                return "🔁 | Disabled"


class AtlasVolumeControl(discord.ui.View):
    def __init__(self, interaction, timeout=30):
        self.initiator = interaction.user
        self.player = interaction.guild.voice_client
        super().__init__(timeout=timeout)

    async def interaction_check(self, interaction: Interaction) -> Coroutine[Any, Any, bool]:
        if not (interaction.user.voice and interaction.user.voice.channel == self.player.channel):
            await AtlasMessage(interaction).send_error(title="You are not connected to the bot's channel!")
            return False

        if not RoleDB(self.player.guild.id).permission_level(interaction.user) >= 8:
            await AtlasMessage(interaction).send_error(title="You do not meet the permissions to run this command!")
            return False

        return True

    @discord.ui.button(label="➕", style=discord.ButtonStyle.gray)
    async def increase_callback(self, interaction: discord.Interaction, button: discord.Button):
        await self.player.set_volume(clamp(self.player.volume + 10, 0, 100))
        await interaction.response.edit_message(embed=self.update_embed())

    @discord.ui.button(label="➖", style=discord.ButtonStyle.gray)
    async def decrease_callback(self, interaction: discord.Interaction, button: discord.Button):
        await self.player.set_volume(clamp(self.player.volume - 10, 0, 100))
        await interaction.response.edit_message(embed=self.update_embed())

    def update_embed(self):
        return AtlasEmbed.default(
            user=self.initiator,
            title=f"Player Volume: {self.player.volume}",
            colour=Colour.RADIO
        )

class AtlasVoteSkipControl(discord.ui.View):
    def __init__(self, interaction: discord.interactions, timeout=30):
        self.skippers = set()
        self.connected = [member.id for member in filter(lambda user: not user.bot, interaction.guild.voice_client.channel.members)]
        self.initiator = interaction.user

        super().__init__(timeout=timeout)

    async def interaction_check(self, interaction: Interaction) -> Coroutine[Any, Any, bool]:
        if interaction.user.id not in self.connected:
            await AtlasMessage(interaction).send_error(title="You are not connected to the bot's channel!")
            return False

        return True

    def update_embed(self):
        return AtlasEmbed.default(
            user=self.initiator,
            title="Vote to skip! (50% skip votes needed)",
            description=f"Votes: {len(self.skippers)}/{len(self.connected)}",
            colour=Colour.RADIO
        )

    @discord.ui.button(label="skip", style=discord.ButtonStyle.green)
    async def voteskip_callback(self, interaction: discord.Interaction, button: discord.Button):
        self.skippers.add(interaction.user.id)
        if len(self.connected) / 2 <= len(self.skippers):
            button.disabled = True
            await interaction.guild.voice_client.stop()
            await interaction.response.edit_message(view=self, embed=AtlasEmbed.default(
                user=self.initiator,
                title="Skipped!",
                colour=Colour.RADIO
            ))
        else:
            await interaction.response.edit_message(embed=self.update_embed())

class AtlasMessage:
    def __init__(self, interaction: discord.Interaction) -> None:
        self.interaction = interaction

    async def send(self, title="", description="", colour=Colour.INFO) -> None:
        await self.interaction.response.send_message(embed=AtlasEmbed.default(
            user=self.interaction.user,
            title=title,
            description=description,
            colour=colour,
        ))

    async def send_error(self, title="", description="", delete_after=5, colour=Colour.ERROR) -> None:
        await self.interaction.response.send_message(delete_after=delete_after, embed=AtlasEmbed.default(
            user=self.interaction.user,
            title=title,
            description=description,
            colour=colour
        ))

    async def send_image(self, url, file=discord.utils.MISSING, title="", description="", colour=Colour.INFO):
        await self.interaction.response.send_message(file=file, embed=AtlasEmbed.default(
            user=self.interaction.user,
            title=title,
            description=description,
            colour=colour
        ).set_image(url=url))

    async def send_field(self, title="", description="", name="", value="", inline=False, colour=Colour.INFO) -> None:
        embed = AtlasEmbed.default(
            user=self.interaction.user,
            title=title,
            description=description,
            colour=colour
        )
        embed.add_field(name=name, value=value, inline=inline)
        await self.interaction.response.send_message(embed=embed)

    async def send_page(self, data, length, title="", description="", timeout=30, divider=7, colour=Colour.INFO) -> None:
        view = AtlasPagifier(data=data, divider=divider, timeout=timeout, length=length)
        embed = view.update_embed(embed=AtlasEmbed.default(
            user=self.interaction.user,
            title=title,
            description=description,
            colour=colour
        ))
        await self.interaction.response.send_message(embed=embed, view=view)

    async def send_radio_volume_control(self):
        view = AtlasVolumeControl(self.interaction)
        await self.interaction.response.send_message(embed=view.update_embed(), view=view)

    async def send_radio_voteskip(self):
        view = AtlasVoteSkipControl(self.interaction)
        await self.interaction.response.send_message(embed=view.update_embed(), view=view)
