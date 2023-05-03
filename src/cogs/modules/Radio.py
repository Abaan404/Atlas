import asyncio
import discord
import os
import pomice
from discord import app_commands
from discord.ext import commands

from scripts.database import ModuleDB, RadioDB
from scripts.message import AtlasMessage, AtlasPlayerControl, Colour
from scripts.pomice import AtlasNodePool, AtlasPlayer
from utils.enums import Module, Roles
from utils.errors import DMBlocked, ModuleNotFound
from utils.functions import clamp, has_permissions, verify_channel


class RadioCore(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.pomice = AtlasNodePool()
        bot.loop.create_task(self.connect_nodes())

    async def connect_nodes(self):
        while True:
            try:
                await asyncio.sleep(2)
                await self.pomice.create_node(
                    bot=self.bot,
                    host="lavalink",
                    port=2333,
                    password=os.getenv("LAVALINK_PASSWORD"),
                    identifier="MAIN",
                    spotify_client_id=os.getenv("SPOTIFY_CLIENT_ID"),
                    spotify_client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
                    apple_music=True,
                )
                break
            except pomice.NodeConnectionFailure:  # keep reconnecting until lavalink is ready
                continue
        print(f'Pomice is ready!')

    async def play_song(self, player, playlist):
        if not player:  # idk it stops working if i remove this
            return
        if not playlist:
            await player.destroy()
            return
        self.bot.loop.create_task(AtlasPlayerControl(player, playlist).update_player_controls())
        song = await player.get_tracks(query=playlist[0]["url"])
        await player.play(track=song[0])

    @commands.Cog.listener()
    async def on_error(self, interaction, error):
        if isinstance(error, (pomice.exceptions.SpotifyAlbumLoadFailed, pomice.exceptions.SpotifyPlaylistLoadFailed, pomice.exceptions.SpotifyTrackLoadFailed)):
            await AtlasMessage(interaction).send_error(description=f"Could not find the song or playlist")

    @commands.Cog.listener()
    async def on_pomice_track_end(self, player, track, _):
        RadioDB(player.guild.id).update()
        playlist = RadioDB(player.guild.id).playlist(8)
        await self.play_song(player, playlist)

    @commands.Cog.listener("on_voice_state_update")
    async def afk_check(self, member, before, after):
        player = self.pomice.get_node().get_player(member.guild.id)
        if player and len(self.bot.get_channel(player.channel.id).members) == 1:
            try:
                await self.bot.wait_for("voice_state_update", timeout=15,
                                        check=lambda member, before, after: member is not self.bot.user)  # 15 second grace before disconnect
            except asyncio.TimeoutError:
                await player.destroy()


class Radio(RadioCore):
    """Play Music!"""

    def cog_check(self, ctx):
        if isinstance(ctx.channel, discord.channel.DMChannel):
            raise DMBlocked
        if not ModuleDB(ctx.guild.id).is_enabled(Module.RADIO):
            raise ModuleNotFound
        return True

    @staticmethod
    def format_track_time(length):
        if length < 3600000:  # if less than 01:00:00 minutes
            return f"{length//60000:02}:{(length//1000)%60:02}"
        else:
            return f"{length//3600000:02}:{(length//60000)%60:02}:{(length//1000)%60:02}"


    @staticmethod
    async def is_player_ready(interaction, player):
        if not player:
            await AtlasMessage(interaction).send_error(title="The radio isn't currently active")
            return False
        if not player.is_playing:
            await AtlasMessage(interaction).send_error(title="The radio isn't currently playing anything")
            return False
        return True

    @staticmethod
    async def is_user_connected(interaction, player):
        if player and interaction.user.voice.channel == player.channel:
            return True
        await AtlasMessage(interaction).send_error(title="You're not connected to the bot's channel")

    @app_commands.command(name="join")
    @app_commands.checks.cooldown(rate=1, per=3)
    @app_commands.guild_only()
    @verify_channel(Module.RADIO)
    async def _join(self, interaction: discord.Interaction, channel: discord.VoiceChannel = None):
        """Joins a vc and start playing."""
        if not (channel if channel else interaction.user.voice):
            await AtlasMessage(interaction).send_error(title="You're not connected to a voice channel")
            return

        channel = channel if channel else interaction.user.voice.channel
        player = interaction.guild.voice_client
        if not player:
            player = await channel.connect(cls=AtlasPlayer)
        elif player.channel != channel:
            # await player.destroy()
            # await asyncio.sleep(1)
            # player = await channel.connect(cls=AtlasPlayer)
            await AtlasMessage(interaction).send_error(title="Already connected to a channel!")
            return
        player.text_channel = interaction.channel

        if not (playlist := RadioDB(interaction.guild.id).playlist(8)):
            await AtlasMessage(interaction).send_error(title="The current playlist is empty")
            return

        await self.play_song(player, playlist)
        await AtlasMessage(interaction).send(title=f"Joined channel {channel.name}", colour=Colour.RADIO)

    @app_commands.command(name="leave")
    @app_commands.checks.cooldown(rate=1, per=3)
    @app_commands.guild_only()
    @verify_channel(Module.RADIO)
    async def _leave(self, interaction: discord.Interaction):
        """Disconnects from the voice channel."""
        player = interaction.guild.voice_client
        if player:
            await player.destroy()
        await AtlasMessage(interaction).send(title=f"Radio disconnected", colour=Colour.RADIO)

    @app_commands.command(name="play")
    @app_commands.checks.cooldown(rate=1, per=1)
    @app_commands.guild_only()
    @has_permissions(Roles.RADIO)
    @verify_channel(Module.RADIO)
    async def _play(self, interaction: discord.Interaction, query: str = None):
        """Add a song into the playlist."""
        if not interaction.user.voice:
            await AtlasMessage(interaction).send_error(title="You're not connected to a voice channel")
            return

        player = interaction.guild.voice_client
        if not player:
            player = await interaction.user.voice.channel.connect(cls=AtlasPlayer)
        elif player.channel != interaction.user.voice.channel:
            await player.destroy()
            player = await interaction.user.voice.channel.connect(cls=AtlasPlayer)
        player.text_channel = interaction.channel

        if query:
            data = await player.get_tracks(query)
            if isinstance(data, list):
                data = data[0]
                position = RadioDB(interaction.guild.id).push([{
                    "url": data.uri,
                    "title": data.title,
                    "author": data.author,
                    "length": 0 if data.is_stream else data.length,
                    "user": interaction.user.id
                }])

                match data.track_type.value:
                    case "youtube":
                        await AtlasMessage(interaction).send(
                            description=f"**Added [{data.title}]({data.uri}) [{'∞' if data.is_stream else self.format_track_time(data.length)}] to the queue ({position})**",
                            colour=Colour.YOUTUBE
                        )
                    case "soundcloud":
                        await AtlasMessage(interaction).send(
                            description=f"**Added [{data.title}]({data.uri}) [{data.length}] to the queue ({position})**",
                            colour=Colour.SOUNDCLOUD
                        )
                    case "spotify":
                        await AtlasMessage(interaction).send(
                            description=f"**Added [{data.title}]({data.uri}) [{data.length}] to the queue ({position})**",
                            colour=Colour.SPOTIFY
                        )
                    case "apple_music":
                        await AtlasMessage(interaction).send(
                            description=f"**Added [{data.title}]({data.uri}) [{data.length}] to the queue ({position})**",
                            colour=Colour.APPLE_MUSIC
                        )
                    case "twitch":
                        await AtlasMessage(interaction).send(
                            description=f"**Added [{data.title}]({data.uri}) [∞] to the queue ({position})**",
                            colour=Colour.TWITCH
                        )

            elif isinstance(data, pomice.Playlist):
                position = RadioDB(interaction.guild.id).push([{
                    "url": track.uri,
                    "title": track.title,
                    "author": track.author,
                    "length": 0 if track.is_stream else track.length,
                    "user": interaction.user.id,
                } for track in data.tracks])

                match data.playlist_type.value:
                    case "youtube":
                        await AtlasMessage(interaction).send(
                            description=f"**Added {data.track_count} song(s) to the queue ({position - data.track_count})**",
                            colour=Colour.YOUTUBE
                        )
                    case "soundcloud":
                        await AtlasMessage(interaction).send(
                            description=f"**Added {data.track_count} song(s) to the queue ({position - data.track_count})**",
                            colour=Colour.SOUNDCLOUD
                        )
                    case "spotify":
                        await AtlasMessage(interaction).send(
                            description=f"**Added {data.track_count} song(s) to the queue ({position - data.track_count})**",
                            colour=Colour.SPOTIFY
                        )
                    case "apple_music":
                        await AtlasMessage(interaction).send(
                            description=f"**Added {data.track_count} song(s) to the queue ({position - data.track_count})**",
                            colour=Colour.APPLE_MUSIC
                        )

            else:
                await AtlasMessage(interaction).send_error(description=f"Could not find the song or playlist **{query}**")
                return

        elif not (playlist := RadioDB(interaction.guild.id).playlist(1)):
            await AtlasMessage(interaction).send_error(title="The current playlist is empty")
            return
        else:
            await AtlasMessage(interaction).send(title=f"Now Playing: {playlist[0]['author']} | {playlist[0]['title']}", colour=Colour.RADIO)

        playlist = RadioDB(interaction.guild.id).playlist(8)
        if player.message:
            await AtlasPlayerControl(player, playlist).update_player_controls()
        else:
            await self.play_song(player, playlist)

    @app_commands.command(name="remove")
    @app_commands.checks.cooldown(rate=1, per=1)
    @app_commands.guild_only()
    @has_permissions(Roles.RADIO)
    @verify_channel(Module.RADIO)
    async def _remove(self, interaction: discord.Interaction, position: int):
        """Removes a song from the playlist."""
        player = interaction.guild.voice_client
        if not await self.is_user_connected(interaction, player):
            return

        song = RadioDB(interaction.guild.id).remove(abs(position)-1)
        if not song:
            await AtlasMessage(interaction).send_error(title="Invalid index")
            return

        if player:
            await AtlasPlayerControl(player, RadioDB(interaction.guild.id).playlist(8)).update_player_controls()
        await AtlasMessage(interaction).send(title=f"Removed song {song['title']}", colour=Colour.RADIO)

    @app_commands.command(name="jump")
    @app_commands.checks.cooldown(rate=1, per=1)
    @app_commands.guild_only()
    @has_permissions(Roles.RADIO)
    @verify_channel(Module.RADIO)
    async def _jump(self, interaction: discord.Interaction, position: int):
        """Jumps to a song from the playlist."""
        player = interaction.guild.voice_client
        if not await self.is_player_ready(interaction, player):
            return
        if not await self.is_user_connected(interaction, player):
            return

        if position > 1:
            RadioDB(interaction.guild.id).jump(abs(position) - 2)
            await player.stop()
        song = RadioDB(interaction.guild.id).playlist(1)[0]
        await AtlasMessage(interaction).send(title=f"Now Playing: {song['author']} | {song['title']}", colour=Colour.RADIO)

    @app_commands.command(name="move")
    @app_commands.checks.cooldown(rate=1, per=1)
    @app_commands.guild_only()
    @has_permissions(Roles.RADIO)
    @verify_channel(Module.RADIO)
    async def _move(self, interaction: discord.Interaction, index1: int, index2: int):
        """Moves tracks in the playlist."""
        player = interaction.guild.voice_client
        if not await self.is_user_connected(interaction, player):
            return

        if index1 in {0, 1} or index2 in {0, 1}:
            await AtlasMessage(interaction).send_error(title=f"Cannot move currently playing track")

        RadioDB(interaction.guild.id).swap(index1 - 1, index2 - 1)
        if player:
            await AtlasPlayerControl(player, RadioDB(interaction.guild.id).playlist(8)).update_player_controls()
        await AtlasMessage(interaction).send(title=f"Moved song ({index1} -> {index2})", colour=Colour.RADIO)

    @app_commands.command(name="clear")
    @app_commands.checks.cooldown(rate=1, per=1)
    @app_commands.guild_only()
    @has_permissions(Roles.RADIO)
    @verify_channel(Module.RADIO)
    async def _clear(self, interaction: discord.Interaction):
        """Clears the current playlist."""
        player = interaction.guild.voice_client
        RadioDB(interaction.guild.id).clear()

        if player:
            await player.stop()
        await AtlasMessage(interaction).send(title=f"Cleared Queue!", colour=Colour.RADIO)

    @app_commands.command(name="pause")
    @app_commands.checks.cooldown(rate=1, per=2)
    @app_commands.guild_only()
    @has_permissions(Roles.RADIO)
    @verify_channel(Module.RADIO)
    async def _pause(self, interaction: discord.Interaction):
        """Pauses the player."""
        player = interaction.guild.voice_client
        if not await self.is_player_ready(interaction, player):
            return
        if not await self.is_user_connected(interaction, player):
            return

        await player.set_pause(not player.is_paused)
        await AtlasMessage(interaction).send(title="Now Paused!" if player.is_paused else "Now Playing!", colour=Colour.RADIO)

    @app_commands.command(name="loop")
    @app_commands.checks.cooldown(rate=1, per=2)
    @app_commands.guild_only()
    @has_permissions(Roles.RADIO)
    @verify_channel(Module.RADIO)
    async def _loop(self, interaction: discord.Interaction, type: str = ""):
        """Loop the playlist."""
        player = interaction.guild.voice_client
        if not await self.is_user_connected(interaction, player):
            return

        # probably a better way to do this whole command
        match type.lower():
            case "playlist":
                RadioDB(interaction.guild.id).set_loop("playlist_repeat")
            case "track":
                RadioDB(interaction.guild.id).set_loop("track_repeat")
            case "none" | "stop" | "disable":
                RadioDB(interaction.guild.id).set_loop("no_repeat")
            case _:
                RadioDB(interaction.guild.id).cycle_loop()

        match RadioDB(interaction.guild.id).get_loop():
            case "playlist_repeat":
                await AtlasMessage(interaction).send(title="Now Looping Playlist", colour=Colour.RADIO)
            case "track_repeat":
                await AtlasMessage(interaction).send(title="Now Looping Track", colour=Colour.RADIO)
            case "no_repeat":
                await AtlasMessage(interaction).send(title="No Longer Looping", colour=Colour.RADIO)

    @app_commands.command(name="shuffle")
    @app_commands.checks.cooldown(rate=1, per=2)
    @app_commands.guild_only()
    @has_permissions(Roles.RADIO)
    @verify_channel(Module.RADIO)
    async def _shuffle(self, interaction: discord.Interaction):
        """Shuffles the playlist."""
        player = interaction.guild.voice_client
        if not await self.is_user_connected(interaction, player):
            return

        RadioDB(interaction.guild.id).shuffle()
        if player:
            await player.stop()
        await AtlasMessage(interaction).send(title="Playlist Shuffled!", colour=Colour.RADIO)

    @app_commands.command(name="queue")
    @app_commands.checks.cooldown(rate=1, per=2)
    @app_commands.guild_only()
    @verify_channel(Module.RADIO)
    async def _queue(self, interaction: discord.Interaction):
        """Show the current playlist queue."""
        length, playlist = RadioDB(interaction.guild.id).playlist()
        playlist_length = RadioDB(interaction.guild.id).playlist_length()

        def playlist_formatted():
            for i, track in enumerate(playlist, start=1):
                yield (
                    f"{i}) {track['author']} | {track['title']} [{self.format_track_time(track['length']) if track['length'] else '∞'}]\n{track['url']}",
                    f"by <@{track['user']}>"
                )

        await AtlasMessage(interaction).send_page(
            title=f"Radio Queue for {interaction.guild.name}",
            description=f"**Queue Length: {self.format_track_time(playlist_length)}**",
            colour=Colour.RADIO,
            length=length, data=playlist_formatted()
        )

    @app_commands.command(name="volume")
    @app_commands.checks.cooldown(rate=1, per=3)
    @app_commands.guild_only()
    @has_permissions(Roles.RADIO)
    @verify_channel(Module.RADIO)
    async def _volume(self, interaction: discord.Interaction, volume: int = None):
        """Sets the volume of the player."""
        player = interaction.guild.voice_client
        if not await self.is_user_connected(interaction, player):
            return
        if not await self.is_player_ready(interaction, player):
            return

        player = interaction.guild.voice_client
        if volume:
            await player.set_volume(clamp(volume, 0, 100))
            await AtlasMessage(interaction).send(title=f"Set volume to {player.volume}!", colour=Colour.RADIO)
        else:
            await AtlasMessage(interaction).send_radio_volume_control()

    @app_commands.command(name="skip")
    @app_commands.checks.cooldown(rate=1, per=1)
    @app_commands.guild_only()
    @has_permissions(Roles.RADIO)
    @verify_channel(Module.RADIO)
    async def _skip(self, interaction: discord.Interaction):
        """Skip a song."""
        player = interaction.guild.voice_client
        if not await self.is_user_connected(interaction, player):
            return
        if not await self.is_player_ready(interaction, player):
            return

        player = interaction.guild.voice_client
        await player.stop()
        await AtlasMessage(interaction).send(title="Skipped!", colour=Colour.RADIO)

    @app_commands.command(name="voteskip")
    @app_commands.checks.cooldown(rate=1, per=1)
    @app_commands.guild_only()
    @verify_channel(Module.RADIO)
    async def _voteskip(self, interaction: discord.Interaction):
        """Vote to skip a song."""
        player = interaction.guild.voice_client
        if not await self.is_user_connected(interaction, player):
            return
        if not await self.is_player_ready(interaction, player):
            return

        await AtlasMessage(interaction).send_radio_voteskip()


async def setup(bot):
    await bot.add_cog(Radio(bot))
