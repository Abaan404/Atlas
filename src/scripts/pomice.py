import re
import pomice

from enum import Enum
from urllib.parse import quote

class AtlasPlayer(pomice.Player):
    text_channel = None
    message = None

    async def destroy(self):
        self.text_channel = None
        self.message = None
        return await super().destroy()

class TrackType(Enum):
    TWITCH = "twitch_track"

class AtlasNode(pomice.Node):
    async def get_tracks(self, query: str, *, ctx = None, search_type = pomice.SearchType.ytsearch, filters = None):
        if re.match("^https://(|www\.|go\.)twitch.tv/([^/]+)$", query):
            data: dict = await self.send(method="GET", path="loadtracks", query=f"identifier={quote(query)}")

            if not (track := data.get("tracks")):
                return
            track: dict = track[0]
            info: dict = track.get("info")

            return [
                pomice.Track(
                    track_id=track["track"],
                    info={
                        "title": info.get("title"),
                        "author": info.get("author"),
                        "length": info.get("length"),
                        "uri": info.get("uri"),
                        "position": info.get("position"),
                        "identifier": info.get("identifier"),
                        "isStream": info.get("isStream")
                    },
                    ctx=ctx,
                    track_type=TrackType.TWITCH,
                    filters=filters
                )
            ]
        elif pomice.URLRegex.DISCORD_MP3_URL.match(query): # disable discord playback
            return None

        return await super().get_tracks(query, ctx=ctx, search_type=search_type, filters=filters)

class AtlasNodePool(pomice.NodePool):
    def __init__(self) -> None:
        super().__init__()

    @classmethod
    async def create_node(cls, *, bot, host: str, port: str, password: str, identifier: str, secure: bool = False, heartbeat: int = 30, spotify_client_id = None, spotify_client_secret = None, session = None, apple_music: bool = False):
        if identifier in cls._nodes.keys():
            raise pomice.NodeCreationError(f"A node with identifier '{identifier}' already exists.")

        node = AtlasNode(
            pool=cls, bot=bot, host=host, port=port, password=password,
            identifier=identifier, secure=secure, heartbeat=heartbeat,
            spotify_client_id=spotify_client_id,
            session=session, spotify_client_secret=spotify_client_secret,
            apple_music=apple_music
        )

        await node.connect()
        cls._nodes[node._identifier] = node
        return node