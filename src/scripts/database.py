import random
import pymongo
from typing import Union

from utils.enums import Roles


class MongoDB:
    """Base class to establish a connection with the Mongo Database"""
    __instance = None

    @staticmethod
    def get_instance():
        if not MongoDB.__instance:
            MongoDB.__instance = MongoDB()
        return MongoDB.__instance

    def __init__(self):
        self.client = pymongo.MongoClient("mongodb://mongo:27017/")

    def collection(self, collection):
        return self.client["discordbot"][collection]


class MongoHelper:
    def __init__(self, guild: int, collection: str, schema: dict = {}) -> None:
        self.mongo = MongoDB.get_instance()
        self.data = self.mongo.collection(collection)
        self.guild = guild
        self._new_guild(schema)

    def _new_guild(self, schema) -> None:
        schema.update({"_id": self.guild})
        try:
            self.data.insert_one(schema)
        except pymongo.errors.DuplicateKeyError:
            pass

    def _exists(self, object: str):
        return bool(self.data.find_one({"_id": self.guild, object: {"$exists": True}}))

    def _get_object(self, key, filter: dict = {}) -> list:
        if data := self.data.find_one({"_id": self.guild}, filter).get(key):
            return data
        return list()

    def _set_object(self, document: dict = {}, filter: dict = {}) -> list:
        filter.update({"_id": self.guild})
        return self.data.update_one(filter, {"$set": document})

    def _get_array_element_by_index(self, array: str, index) -> dict:
        return list(self.data.aggregate([
            {"$match": {"_id": self.guild}},
            {"$project": {"array": {"$arrayElemAt": [f"${array}", index]}}}
        ]))[0].get("array")

    def _remove_array_element_by_index(self, array: str, index) -> Union[dict, None]:
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
        return list(self.data.aggregate([
            {"$match": {"_id": self.guild}},
            {"$project": {"length": {"$size": f"${array}"}}}
        ]))[0].get("length")

    def _push(self, data: dict) -> None:
        self.data.update_one({"_id": self.guild}, {"$push": data})


class ModuleDB(MongoHelper):  # TODO
    def __init__(self, guild: int) -> None:
        super().__init__(guild, collection="modules", schema={"modules": []})

    def enable(self, module, config={}) -> None:
        if not self.data.find_one({"_id": self.guild, "modules.name": module.value}):
            self._push({"modules": {"name": module.value, "config": config}})
        else:
            self._set_object({"modules.$.config": config}, {"modules.name": module.value})

    def disable(self, module) -> None:
        self.data.update_one({"_id": self.guild}, {"$pull": {"modules": {"name": module.value}}})

    def is_enabled(self, module) -> bool:
        if not self.data.find_one({"_id": self.guild, "modules.name": module.value}):
            return False
        return True

    def get_config(self, module, data) -> Union[None, dict]:
        return list(self.data.aggregate([
            {"$unwind": "$modules"},
            {"$match": {"_id": self.guild, "modules.name": module.value}},
            {"$project": {"_id": False, "config": "$modules.config"}}
        ]))[0]["config"].get(data)

    def fetch_enabled_name(self) -> list:
        return [module["name"] for module in self._get_object("modules")]

    def get_guilds_enabled(self, module) -> list:
        return self.data.aggregate([
            {"$unwind": "$modules"},
            {"$match": {"modules.name": module.value}},
            {"$project": {"_id": False, "guild": "$_id", "config": "$modules.config"}}
        ])


class BlameDB(MongoHelper):
    def __init__(self, guild: int) -> None:
        super().__init__(guild, collection="blame", schema={"modules": []})

    def push(self, user, blamer, reason) -> None:
        self._push({f"n{user}": {"blamer": blamer, "reason": reason}})

    def list(self, user) -> tuple[int, list]:
        if not self.data.find_one({"_id": self.guild}):
            return 
        blames = list(self.data.aggregate([
            {"$match": {"_id": self.guild}},
            {"$project": {"blames": {"$filter": {"input": f"$n{user}", "as": "buffer", "cond": {"$ne": ["$$buffer.reason", None]}}}}}
        ]))[0].get("blames")
        length = list(self.data.aggregate([
            {"$match": {"_id": self.guild}},
            {"$project": {"length": {"$size": {"$filter": {"input": f"$n{user}", "as": "buffer", "cond": {"$ne": ["$$buffer.reason", None]}}}}}}
        ]))[0].get("length")
        return length, blames

    def count(self, user) -> int:
        return self._get_array_length(f"n{user}")


class QotdDB(MongoHelper):
    def __init__(self, guild: int) -> None:
        super().__init__(guild, collection="qotd", schema={"pending": [], "accepted": []})

    def suggest(self, question, user) -> None:
        self._push({"pending": {"$each": [{"question": f"{question}", "user": user}]}})

    def decline(self, index) -> Union[None, str]:
        return self._remove_array_element_by_index("pending", index)

    def accept(self, index) -> Union[None, str]:
        if question := self._remove_array_element_by_index("pending", index):
            self._push({"accepted": question})
        return question

    def fetch(self) -> Union[None, str]:
        if question := self._remove_array_element_by_index("accepted", 0):
            return question

    def get_pending(self) -> tuple[int, list]:
        return self._get_array_length("pending"), self._get_object("pending")

    def get_accepted(self) -> tuple[int, list]:
        return self._get_array_length("accepted"), self._get_object("accepted")


class RadioDB(MongoHelper):
    def __init__(self, guild: int) -> None:
        super().__init__(guild, collection="radio", schema={"loop": "playlist_repeat", "playlist": []})

    def playlist(self, limit: int = None) -> tuple[int, list] | list:
        if limit:
            return self._get_object("playlist", filter={"playlist": {"$slice": limit}})
        return self._get_array_length("playlist"), self._get_object("playlist")

    def playlist_length(self):
        return list(self.data.aggregate([
            {"$match": {"_id": self.guild}},
            {"$project": {"length": {"$sum": "$playlist.length"}}}
        ]))[0].get("length")

    def push(self, tracks: list[dict]) -> dict:
        self._push({"playlist": {"$each": tracks}})
        return self.position()

    def position(self):
        return list(self.data.aggregate([
            {"$match": {"_id": self.guild}},
            {"$project": {"position": {"$size": "$playlist"}}}
        ]))[0]["position"]

    def remove(self, index: int) -> Union[None, dict]:
        return self._remove_array_element_by_index("playlist", index)

    def update(self) -> Union[None, dict]:
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

    def jump(self, index) -> None: #TODO
        self.data.update_one({"_id": self.guild}, [
            {"$set": {"playlist": {"$concatArrays": [{"$slice": ["$playlist", index, {"$size": "$playlist"}]}, {"$slice": ["$playlist", index]}]}}}
        ])

    def swap(self, first, second) -> None:
        track1 = self._get_array_element_by_index("playlist", first)
        track2 = self._get_array_element_by_index("playlist", second)
        self._set_object({f"playlist.{first}": track2})
        self._set_object({f"playlist.{second}": track1})

    def get_loop(self) -> bool:
        return self._get_object("loop")

    def set_loop(self, loop_type: str) -> bool:
        self._set_object({"loop": loop_type})

    def cycle_loop(self) -> bool:
        loops = ["playlist_repeat", "track_repeat",
                 "no_repeat", "playlist_repeat"]
        loop = loops[loops.index(self.get_loop()) + 1]
        self._set_object({"loop": loop})
        return loop

    def shuffle(self) -> None:
        playlist = list(self.playlist()[1])
        random.shuffle(playlist)
        self._set_object({"playlist": playlist})


class RoleDB(MongoHelper):
    def __init__(self, guild: int) -> None:
        super().__init__(guild, collection="roles")

    def insert(self, id, role) -> None:
        self._set_object({role: id})

    def remove(self, role) -> int:
        id = self.get(role)
        self.data.update_one({"_id": self.guild}, {"$unset": {role: True}})
        return id

    def get(self, role) -> int:
        if not (role := self._get_object(role)):
            role = 0
        return role

    def permission_level(self, member) -> int: #TODO test
        if member.guild_permissions.administrator:
            return Roles.ADMINISTRATOR.value

        guild_roles = self.data.find_one({"_id": self.guild}, {"_id": False}).items()
        user_roles = [role.id for role in member.roles]
        user_levels = [Roles[role[0]].value for role in guild_roles if role[1] in user_roles]
        if user_levels:
            return max(user_levels)
        else:
            return 0

    def list(self) -> dict:
        return self.data.find_one({"_id": self.guild}, {"_id": False})
