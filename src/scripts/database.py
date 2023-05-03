import random
import pymongo

from utils.enums import Roles, Module


class MongoDB:
    """Base class to establish a connection with the Mongo Database and a few helper functions"""
    def __init__(self, guild: int, collection: str, schema: dict = {}) -> None:
        self.client = pymongo.MongoClient("mongodb://mongo:27017/")
        self.data = self.client["discordbot"][collection]
        self.guild = guild
        self._new_guild(schema)

    def _new_guild(self, schema: dict) -> None:
        schema.update({"_id": self.guild})
        try:
            self.data.insert_one(schema)
        except pymongo.errors.DuplicateKeyError:
            pass

    def _exists(self, object: str) -> bool:
        return bool(self.data.find_one({"_id": self.guild, object: {"$exists": True}}))

    def _get_object(self, key: str, filter: dict = {}) -> None:
        return self.data.find_one({"_id": self.guild}, filter).get(key)

    def _set_object(self, document: dict = {}, filter: dict = {}):
        filter.update({"_id": self.guild})
        self.data.update_one(filter, {"$set": document})

    def _get_array_element_by_index(self, array: str, index: int):
        return next(self.data.aggregate([
            {"$match": {"_id": self.guild}},
            {"$project": {"object": {"$arrayElemAt": [f"${array}", index]}}}
        ])).get("object")

    def _remove_array_element_by_index(self, array: str, index: int):
        index = abs(index)
        if (val := self._get_array_element_by_index(array, index)):
            # https://jira.mongodb.org/browse/SERVER-1014 :D
            self.data.update_one({"_id": self.guild}, [
                {"$set": {f"{array}": {"$concatArrays": [{"$slice": [f"${array}", index]}, {"$slice": [f"${array}", index+1, {"$size": f"${array}"}]}]}}}
            ])
        return val

    def _get_array_length(self, array: str) -> int:
        if not self._exists(array):
            return 0
        return next(self.data.aggregate([
            {"$match": {"_id": self.guild}},
            {"$project": {"length": {"$size": f"${array}"}}}
        ])).get("length")

    def _push(self, data: dict) -> None:
        self.data.update_one({"_id": self.guild}, {"$push": data})


class ModuleDB(MongoDB):
    def __init__(self, guild: int) -> None:
        super().__init__(guild, collection="modules", schema={"modules": []})

    def enable(self, module: Module, config: dict={}) -> None:
        if not self.data.find_one({"_id": self.guild, "modules.name": module.value}):
            self._push({"modules": {"name": module.value, "config": config}})
        else:
            self._set_object({"modules.$.config": config}, {"modules.name": module.value})

    def disable(self, module: Module) -> None:
        self.data.update_one({"_id": self.guild}, {"$pull": {"modules": {"name": module.value}}})

    def is_enabled(self, module: Module) -> bool:
        if not self.data.find_one({"_id": self.guild, "modules.name": module.value}):
            return False
        return True

    def get_config(self, module: Module, data: str) -> dict | None:
        return next(self.data.aggregate([
            {"$unwind": "$modules"},
            {"$match": {"_id": self.guild, "modules.name": module.value}},
            {"$project": {"_id": False, "config": "$modules.config"}}
        ])).get("config").get(data)

    def fetch_enabled_name(self) -> list:
        return [module["name"] for module in self._get_object("modules")]

    def get_guilds_enabled(self, module: Module) -> list:
        return self.data.aggregate([
            {"$unwind": "$modules"},
            {"$match": {"modules.name": module.value}},
            {"$project": {"_id": False, "guild": "$_id", "config": "$modules.config"}}
        ])


class BlameDB(MongoDB):
    def __init__(self, guild: int) -> None:
        super().__init__(guild, collection="blame")

    def push(self, user: int, blamer: int, reason: str) -> None:
        self._push({f"n{user}": {"blamer": blamer, "reason": reason}})

    def list(self, user: int) -> tuple[int, list]:
        if not self.data.find_one({"_id": self.guild}):
            return 
        blames = next(self.data.aggregate([
            {"$match": {"_id": self.guild}},
            {"$project": {"blames": {"$filter": {"input": f"$n{user}", "as": "buffer", "cond": {"$ne": ["$$buffer.reason", None]}}}}}
        ])).get("blames")
        length = next(self.data.aggregate([
            {"$match": {"_id": self.guild}},
            {"$project": {"length": {"$size": {"$filter": {"input": f"$n{user}", "as": "buffer", "cond": {"$ne": ["$$buffer.reason", None]}}}}}}
        ])).get("length")
        return length, blames

    def count(self, user: int) -> int:
        return self._get_array_length(f"n{user}")


class QotdDB(MongoDB):
    def __init__(self, guild: int) -> None:
        super().__init__(guild, collection="qotd", schema={"pending": [], "accepted": []})

    def suggest(self, question: str, user: int) -> None:
        self._push({"pending": {"$each": [{"question": f"{question}", "user": user}]}})

    def decline(self, index: int) -> str | None:
        return self._remove_array_element_by_index("pending", index)

    def accept(self, index: int) -> str | None:
        if question := self._remove_array_element_by_index("pending", index):
            self._push({"accepted": question})
        return question

    def fetch(self) -> str | None:
        if question := self._remove_array_element_by_index("accepted", 0):
            return question

    def get_pending(self) -> tuple[int, list]:
        return self._get_array_length("pending"), self._get_object("pending")

    def get_accepted(self) -> tuple[int, list]:
        return self._get_array_length("accepted"), self._get_object("accepted")


class RadioDB(MongoDB):
    def __init__(self, guild: int) -> None:
        super().__init__(guild, collection="radio", schema={"loop": "playlist_repeat", "playlist": []})

    def playlist(self, limit: int = None) -> tuple[int, list] | list:
        if limit:
            return self._get_object("playlist", filter={"playlist": {"$slice": limit}})
        return self._get_array_length("playlist"), self._get_object("playlist")

    def playlist_length(self) -> int:
        return next(self.data.aggregate([
            {"$match": {"_id": self.guild}},
            {"$project": {"length": {"$sum": "$playlist.length"}}}
        ])).get("length")

    def push(self, tracks: list[dict]) -> int:
        self._push({"playlist": {"$each": tracks}})
        return self.position()

    def position(self) -> int:
        return next(self.data.aggregate([
            {"$match": {"_id": self.guild}},
            {"$project": {"position": {"$size": "$playlist"}}}
        ])).get("position")

    def remove(self, index: int) -> dict | None:
        return self._remove_array_element_by_index("playlist", index)

    def update(self) -> None:
        if not (track := self._get_array_element_by_index("playlist", 0)):
            return

        match self.get_loop():
            case "playlist_repeat":
                self._remove_array_element_by_index("playlist", 0)
                self.push([track])
            case "track_repeat":
                pass
            case "no_repeat":
                self._remove_array_element_by_index("playlist", 0)

    def clear(self) -> None:
        self._set_object({"playlist": []})

    def jump(self, index: int) -> None:
        self.data.update_one({"_id": self.guild}, [
            {"$set": {"playlist": {"$concatArrays": [{"$slice": ["$playlist", index, {"$size": "$playlist"}]}, {"$slice": ["$playlist", index]}]}}}
        ])

    def swap(self, first: int, second: int) -> None:
        track1 = self._get_array_element_by_index("playlist", first)
        track2 = self._get_array_element_by_index("playlist", second)
        self._set_object({f"playlist.{first}": track2})
        self._set_object({f"playlist.{second}": track1})

    def get_loop(self) -> bool:
        return self._get_object("loop")

    def set_loop(self, loop_type: str) -> bool:
        self._set_object({"loop": loop_type})

    def cycle_loop(self) -> bool:
        loops = ["playlist_repeat", "track_repeat", "no_repeat", "playlist_repeat"]
        loop = loops[loops.index(self.get_loop()) + 1]
        self._set_object({"loop": loop})
        return loop

    def shuffle(self) -> None:
        playlist = list(self.playlist()[1])
        random.shuffle(playlist)
        self._set_object({"playlist": playlist})


class RoleDB(MongoDB):
    def __init__(self, guild: int) -> None:
        super().__init__(guild, collection="roles")

    def insert(self, id: int, role: str) -> None:
        self._set_object({role: id})

    def remove(self, role: str) -> int:
        id = self.get(role)
        self.data.update_one({"_id": self.guild}, {"$unset": {role: True}})
        return id

    def get(self, role: str) -> int:
        if not (role := self._get_object(role)):
            role = 0
        return role

    def permission_level(self, member) -> int:
        if member.guild_permissions.administrator:
            return Roles.ADMINISTRATOR.value

        guild_roles = self.data.find_one({"_id": self.guild}, {"_id": False}).items()
        user_roles = [role.id for role in member.roles]
        return max((Roles[name.upper()].value for name, role in guild_roles if role in user_roles), default=0)

    def list(self) -> dict:
        return self.data.find_one({"_id": self.guild}, {"_id": False})
