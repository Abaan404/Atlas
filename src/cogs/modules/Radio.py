import discord, asyncio, pomice
import os

from discord.ext import commands

from scripts.pomice import AtlasPlayer, AtlasNodePool
from scripts.pagifier import Pagifier, PlayerMessage, VolumeMessage
from scripts.embeds import Colour, Embeds
from scripts.database import ModuleDB, RadioDB
from utils.errors import DMBlocked, ModuleNotFound
from utils.enums import Module
from utils.functions import clamp, verify_channel, has_permissions, decay_send, stringify, format_track_time
from utils.enums import Roles

class RadioCore(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.pomice = AtlasNodePool()
        bot.loop.create_task(self.connect_nodes())

    async def connect_nodes(self):
        await self.pomice.create_node(
            bot=self.bot, host='lavalink',
            port=2333, password=os.getenv("LAVALINK_PASSWORD"), identifier="MAIN",
            spotify_client_id=os.getenv("SPOTIFY_CLIENT_ID"), spotify_client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
            apple_music=True
        )
        print(f'and pomice is ready!')

    async def play_song(self, player, playlist):
        if not player: # idk it stops working if i remove this
            return
        if not playlist:
            await player.destroy()
            return
        self.bot.loop.create_task(PlayerMessage(player, playlist).update_player_message())
        song = await player.get_tracks(query=playlist[0]["url"])
        await player.play(track=song[0])

    @commands.Cog.listener()
    async def on_error(ctx, error):
        if isinstance(error, (pomice.exceptions.SpotifyAlbumLoadFailed, pomice.exceptions.SpotifyPlaylistLoadFailed, pomice.exceptions.SpotifyTrackLoadFailed)):
            await ctx.send(embed = Embeds.default(
                    user=ctx.author,
                    description=f"Could not find the song or playlist",
                    colour=Colour.ERROR
                ))

    @commands.Cog.listener()
    async def on_pomice_track_end(self, player , track, _):
        RadioDB(player.guild.id).update()
        playlist = RadioDB(player.guild.id).playlist(8)
        await self.play_song(player, playlist)

    @commands.Cog.listener("on_voice_state_update")
    async def afk_check(self, member, before, after):
        if not member.guild:
            return
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

    async def is_player_ready(self, ctx):
        if not ctx.voice_client:
            await decay_send(ctx, embed=Embeds.default(
                user=ctx.author,
                title="The radio isn't currently active",
                colour=Colour.ERROR
            ))
            return False
        elif not ctx.voice_client.is_playing:
            await decay_send(ctx, embed=Embeds.default(
                user=ctx.author,
                title="The radio isn't currently playing anything",
                colour=Colour.ERROR
            ))
            return False
        return True

    async def is_user_connected(self, ctx):
        if not ctx.author.voice:
            await decay_send(ctx, embed=Embeds.default(
                user=ctx.author,
                title="You're not connected to the voice channel",
                colour=Colour.ERROR
            ))
            return False
        if ctx.voice_client and ctx.author.voice.channel != ctx.voice_client.channel:
            await decay_send(ctx, embed=Embeds.default(
                user=ctx.author,
                title="You're not connected to the bot's channel",
                colour=Colour.ERROR
            ))
            return False
        return True

    @commands.command(name="join", aliases=["start", "connect", "j"])
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.member)
    @commands.guild_only()
    @verify_channel(Module.RADIO)
    async def _join(self, ctx, channel: discord.VoiceChannel = None):
        """Joins a vc and start playing."""
        if not await self.is_user_connected(ctx):
            return

        channel = ctx.author.voice.channel if not channel else channel

        if not ctx.voice_client:
            player = await channel.connect(cls=AtlasPlayer)
        elif ctx.voice_client.channel != channel:
            await self._leave(ctx)
            player = await channel.connect(cls=AtlasPlayer)
        player.text_channel = ctx.channel

        if not (playlist := RadioDB(ctx.guild.id).playlist(8)):
            await decay_send(ctx, embed=Embeds.default(
                user=ctx.author,
                title="The current playlist is empty",
                colour=Colour.ERROR
            ))
            return

        await self.play_song(player, playlist)
        await ctx.message.add_reaction("✅")

    @commands.command(name="leave", aliases=["stop", "disconnect"])
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.member)
    @commands.guild_only()
    @verify_channel(Module.RADIO)
    async def _leave(self, ctx):
        """Disconnects from the voice channel."""
        player = ctx.voice_client
        if player:
            await player.destroy()
        await ctx.message.add_reaction("✅")

    @commands.command(name="play", aliases=["add", "pl"])
    @commands.cooldown(rate=1, per=1, type=commands.BucketType.member)
    @commands.guild_only()
    @has_permissions(Roles.RADIO)
    @verify_channel(Module.RADIO)
    async def _play(self, ctx, *query):
        """Add a song into the playlist."""
        player = ctx.voice_client
        if not await self.is_user_connected(ctx):
            return

        if not player:
            player = await ctx.author.voice.channel.connect(cls=AtlasPlayer)
        elif player.channel != ctx.author.voice.channel:
            await self._leave(ctx)
            player = await ctx.author.voice.channel.connect(cls=AtlasPlayer)
        player.text_channel = ctx.channel

        if query:
            data = await player.get_tracks(stringify(query))
            if isinstance(data, list):
                data = data[0]
                position = RadioDB(ctx.guild.id).push([{"url" : data.uri, "title" : data.title, "author": data.author, "user" : ctx.author.id, "length" : 0 if data.is_stream else data.length}])
                match data.track_type.value:
                    case "youtube_track":
                        await ctx.send(embed = Embeds.default(
                            user=ctx.author,
                            description=f"**Added [{data.title}]({data.uri}) [{'∞' if data.is_stream else format_track_time(data.length)}] to the queue ({position})**",
                            colour = Colour.YOUTUBE
                        ))
                    case "soundcloud_track":
                        await ctx.send(embed = Embeds.default(
                            user=ctx.author,
                            description=f"**Added [{data.title}]({data.uri}) [{data.length}] to the queue ({position})**",
                            colour = Colour.SOUNDCLOUD
                        ))
                    case "spotify_track":
                        await ctx.send(embed = Embeds.default(
                            user=ctx.author,
                            description=f"**Added [{data.title}]({data.uri}) [{data.length}] to the queue ({position})**",
                            colour = Colour.SPOTIFY
                        ))
                    case "apple_music_track":
                        await ctx.send(embed = Embeds.default(
                            user=ctx.author,
                            description=f"**Added [{data.title}]({data.uri}) [{data.length}] to the queue ({position})**",
                            colour = Colour.APPLE_MUSIC
                        ))
                    case "twitch_track":
                        await ctx.send(embed = Embeds.default(
                            user=ctx.author,
                            description=f"**Twitch Stream playback is currently disabled.\nSee [here](https://github.com/Walkyst/lavaplayer-fork/issues/76)**",
                            colour = Colour.TWITCH
                        ))
                        return

            elif isinstance(data, pomice.Playlist):
                position = RadioDB(ctx.guild.id).push([{"url" : track.uri, "title" : track.title, "author": track.author, "user" : ctx.author.id, "length" : 0 if track.is_stream else track.length} for track in data.tracks])
                match data.playlist_type.value:
                    case "youtube_playlist":
                        await ctx.send(embed = Embeds.default(
                            user=ctx.author,
                            description=f"**Added {data.track_count} song(s) to the queue ({position - data.track_count})**",
                            colour=Colour.YOUTUBE
                        ))
                    case "soundcloud_playlist":
                        await ctx.send(embed = Embeds.default(
                            user=ctx.author,
                            description=f"**Added {data.track_count} song(s) to the queue ({position - data.track_count})**",
                            colour = Colour.SOUNDCLOUD
                        ))
                    case "spotify_playlist":
                        await ctx.send(embed = Embeds.default(
                            user=ctx.author,
                            description=f"**Added {data.track_count} song(s) to the queue ({position - data.track_count})**",
                            colour=Colour.SPOTIFY
                        ))
                    case "apple_music_playlist":
                        await ctx.send(embed = Embeds.default(
                            user=ctx.author,
                            description=f"**Added {data.track_count} song(s) to the queue ({position - data.track_count})**",
                            colour=Colour.APPLE_MUSIC
                        ))

            else:
                await ctx.send(embed = Embeds.default(
                    user=ctx.author,
                    description=f"Could not find the song or playlist **{stringify(query)}**",
                    colour=Colour.ERROR
                ))
                return


        if not (playlist := RadioDB(ctx.guild.id).playlist(8)):
            await decay_send(ctx, embed=Embeds.default(
                user=ctx.author,
                title="The current playlist is empty",
                colour=Colour.ERROR
            ))
            return

        if player.message: # if player controls already exists
            await PlayerMessage(player, playlist).update_player_message()
        else:
            await self.play_song(player, playlist) # entrypoint

    @commands.command(name="remove", aliases=["delete"])
    @commands.cooldown(rate=1, per=1, type=commands.BucketType.member)
    @commands.guild_only()
    @has_permissions(Roles.RADIO)
    @verify_channel(Module.RADIO)
    async def _remove(self, ctx, position: int):
        """Removes a song from the playlist."""
        player = ctx.voice_client
        if not await self.is_user_connected(ctx):
            return

        song = RadioDB(ctx.guild.id).remove(abs(position)-1)
        if not song:
            await decay_send(ctx, embed=Embeds.default(
                user=ctx.author,
                title="Invalid index",
                colour=Colour.ERROR
            ))
            return
        if player:
            await PlayerMessage(player, RadioDB(ctx.guild.id).playlist(8)).update_player_message()

        await ctx.send(embed=Embeds.default(
            user=ctx.author,
            title=f"Removed song {song['title']}",
            colour=Colour.RADIO
        ))

    @commands.command(name="jump", aliases=[])
    @commands.cooldown(rate=1, per=1, type=commands.BucketType.member)
    @commands.guild_only()
    @has_permissions(Roles.RADIO)
    @verify_channel(Module.RADIO)
    async def _jump(self, ctx, position: int):
        """Jumps to a song from the playlist."""
        player = ctx.voice_client
        if not await self.is_player_ready(ctx):
            return
        if not await self.is_user_connected(ctx):
            return

        if position not in [0, 1]:
            RadioDB(ctx.guild.id).jump(abs(position) - 2) # jump one track early to allow skip
            await player.stop()
        await ctx.message.add_reaction("✅")

    @commands.command(name="move", aliases=["swap"])
    @commands.cooldown(rate=1, per=1, type=commands.BucketType.member)
    @commands.guild_only()
    @has_permissions(Roles.RADIO)
    @verify_channel(Module.RADIO)
    async def _move(self, ctx, index1: int, index2: int):
        """Moves tracks in the playlist."""
        player = ctx.voice_client
        if not await self.is_user_connected(ctx):
            return

        if index1 in [0, 1] or index2 in [0, 1]:
            await ctx.send(embed=Embeds.default(
                user=ctx.author,
                title=f"Cannot move currently playing track", # not really, im just lazy
                colour=Colour.ERROR
            ))

        RadioDB(ctx.guild.id).swap(index1 - 1, index2 - 1)
        if player:
            await PlayerMessage(player, RadioDB(ctx.guild.id).playlist(8)).update_player_message()
        await ctx.message.add_reaction("✅")

    @commands.command(name="clear", aliases=["cl"])
    @commands.cooldown(rate=1, per=1, type=commands.BucketType.member)
    @commands.guild_only()
    @has_permissions(Roles.RADIO)
    @verify_channel(Module.RADIO)
    async def _clear(self, ctx):
        """Clears the current playlist."""
        if not await self.is_user_connected(ctx):
            return

        player = ctx.voice_client
        RadioDB(ctx.guild.id).clear()
        if player:
            await player.stop()
        await ctx.message.add_reaction("✅")

    @commands.command(name="pause", aliases=["p"])
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.member)
    @commands.guild_only()
    @has_permissions(Roles.RADIO)
    @verify_channel(Module.RADIO)
    async def _pause(self, ctx):
        """Pauses the player."""
        player = ctx.voice_client
        if not await self.is_player_ready(ctx):
            return
        if not await self.is_user_connected(ctx):
            return

        await player.set_pause(not player.is_paused)
        await ctx.message.add_reaction("✅")

    @commands.command(name="loop", aliases=["repeat"])
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.member)
    @commands.guild_only()
    @has_permissions(Roles.RADIO)
    @verify_channel(Module.RADIO)
    async def _loop(self, ctx, type=None):
        """Loop the playlist."""
        if not await self.is_user_connected(ctx):
            return

        # probably a better way to do this whole command
        match type.lower():
            case "playlist":
                RadioDB(ctx.guild.id).set_loop("playlist_repeat")
            case "track":
                RadioDB(ctx.guild.id).set_loop("track_repeat")
            case "none" | "stop" | "disable":
                RadioDB(ctx.guild.id).set_loop("no_repeat")
            case _:
                RadioDB(ctx.guild.id).cycle_loop()

        match RadioDB(ctx.guild.id).get_loop():
            case "playlist_repeat":
                await ctx.send(embed=Embeds.default(
                    user=ctx.author,
                    title="Now Looping Playlist",
                    colour=Colour.RADIO
                ))
            case "track_repeat":
                await ctx.send(embed=Embeds.default(
                    user=ctx.author,
                    title="Now Looping Track",
                    colour=Colour.RADIO
                ))
            case "no_repeat":
                await ctx.send(embed=Embeds.default(
                    user=ctx.author,
                    title="No Longer Looping",
                    colour=Colour.RADIO
                ))

    @commands.command(name="shuffle")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.member)
    @commands.guild_only()
    @has_permissions(Roles.RADIO)
    @verify_channel(Module.RADIO)
    async def _shuffle(self, ctx):
        """Shuffles the playlist."""
        if not await self.is_user_connected(ctx):
            return

        RadioDB(ctx.guild.id).shuffle()
        await ctx.message.add_reaction("✅")

    @commands.command(name="queue", aliases=["q"])
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.member)
    @commands.guild_only()
    @verify_channel(Module.RADIO)
    async def _queue(self, ctx):
        """Show the current playlist queue."""
        playlist = RadioDB(ctx.guild.id).playlist()

        total_length = 0
        for i in range(len(playlist)):
            total_length += playlist[i]['length']
            playlist[i] = (
                f"{i+1}) {playlist[i]['author']} | {playlist[i]['title']} [{format_track_time(playlist[i]['length']) if playlist[i]['length'] else '∞'}]\n{playlist[i]['url']}",
                f"by <@{playlist[i]['user']}>"
            )

        msg = await ctx.send(embed=Embeds.default(
            user=ctx.author,
            title=f"Radio Queue for {ctx.guild.name}",
            description=f"**Queue Length: {format_track_time(total_length)}**",
            colour=Colour.RADIO
        ))
        pages = Pagifier(playlist, self.bot, ctx.author, msg)
        await pages.generate_page_controls()

    @commands.command(name="volume", aliases=["vol"])
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.member)
    @commands.guild_only()
    @has_permissions(Roles.RADIO)
    @verify_channel(Module.RADIO)
    async def _volume(self, ctx, volume: int = None):
        """Sets the volume of the player."""
        if not await self.is_user_connected(ctx):
            return
        if not await self.is_player_ready(ctx):
            return

        player = ctx.voice_client
        if volume:
            await player.set_volume(clamp(volume, 0, 100))
            await ctx.message.add_reaction("✅")
        else:
            await VolumeMessage(player).create_volume_controls()

    @commands.command(name="skip", aliases=["next", "s"])
    @commands.cooldown(rate=1, per=1, type=commands.BucketType.member)
    @commands.guild_only()
    @has_permissions(Roles.RADIO)
    @verify_channel(Module.RADIO)
    async def _skip(self, ctx):
        """Skip a song."""
        if not await self.is_user_connected(ctx):
            return
        if not await self.is_player_ready(ctx):
            return

        player = ctx.voice_client
        await player.stop()
        await ctx.message.add_reaction("✅")

    @commands.command(name="voteskip", aliases=["vskip", "vs"])
    @commands.cooldown(rate=1, per=1, type=commands.BucketType.member)
    @commands.guild_only()
    @verify_channel(Module.RADIO)
    async def _voteskip(self, ctx):
        """Vote to skip a song."""
        if not await self.is_user_connected(ctx):
            return
        if not await self.is_player_ready(ctx):
            return

        player = ctx.voice_client
        if len(ctx.author.voice.channel.members) == 2:
            await player.stop()
            await ctx.message.add_reaction("✅")
            return

        msg = await ctx.send(embed=Embeds.default(
            user=ctx.author,
            title="Vote to skip! (50% skip votes needed)",
            colour=Colour.RADIO
        ))
        await msg.add_reaction("⏭️")
        while True:
            try:
                await self.bot.wait_for("reaction_add", timeout=60, check=lambda reaction, user: user.guild == ctx.author.guild and str(reaction.emoji) == "⏭️" and reaction.message == msg)
                if not player.is_playing:
                    await ctx.message.add_reaction("❌")
                    break
            except asyncio.TimeoutError:
                await ctx.message.add_reaction("❌")
                break
            users_voice = ctx.author.voice.channel.members
            users_reacted = [user async for user in (await ctx.channel.fetch_message(msg.id)).reactions[0].users()] # :D
            users_skipped = len([user for user in users_reacted if user in users_voice and user != self.bot.user])
            if (len(users_voice) - 1)/2 <= users_skipped:
                await player.stop()
                await msg.edit(embed=Embeds.default(ctx.author, title="Skipped!", colour=Colour.RADIO))
                await ctx.message.add_reaction("✅")
                break
        await msg.delete(delay=5)

async def setup(bot):
    await bot.add_cog(Radio(bot))
