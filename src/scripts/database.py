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
    def _new_guild(self, schema: dict = {}) -> None:
        schema.update({"_id": self.guild})
        try:
            self.data.insert_one(schema)
        except pymongo.errors.DuplicateKeyError:
            pass

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
        if (val := self._get_array_element_by_index(array, index)):
            # https://jira.mongodb.org/browse/SERVER-1014 :D
            self.data.update_one({"_id": self.guild}, [
                {"$set": {f"{array}": {"$concatArrays": [{"$slice": [f"${array}", index]}, {"$slice": [f"${array}", index+1, {"$size": f"${array}"}]}]}}}
            ])
        return val

    def _push(self, data: dict) -> None:
        self.data.update_one({"_id": self.guild}, {"$push": data})


class ModuleDB(MongoHelper):  # TODO
    def __init__(self, guild):
        self.mongo = MongoDB.get_instance()
        self.data = self.mongo.collection("modules")
        self.guild = guild

        self._new_guild({"modules": []})

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

    def get_config(self, module) -> Union[None, dict]:
        return list(self.data.aggregate([
            {"$unwind": "$modules"},
            {"$match": {"_id": self.guild, "modules.name": module.value}},
            {"$project": {"_id": False, "config": "$modules.config"}}
        ]))[0]["config"]

    def fetch_enabled_name(self) -> list:
        return [module["name"] for module in self._get_object("modules")]

    def get_guilds_enabled(self, module) -> list:
        return self.data.aggregate([
            {"$unwind": "$modules"},
            {"$match": {"modules.name": module.value}},
            {"$project": {"_id": False, "guild": "$_id", "config": "$modules.config"}}
        ])


class BlameDB(MongoHelper):
    def __init__(self, guild):
        self.mongo = MongoDB.get_instance()
        self.data = self.mongo.collection("blame")
        self.guild = guild
        self._new_guild()

    def push(self, user, blamer, reason=None) -> None:
        self._push({f"n{user}": {"blamer": blamer, "reason": reason}})

    def list(self, user) -> list:
        blames = self._get_object(f"n{user}")
        # Filter out blames with null reason
        return [blame.values() for blame in blames if blame["reason"]]

    def count(self, user) -> int:
        return len(self._get_object(f"n{user}"))

class QotdDB(MongoHelper):
    def __init__(self, guild):
        self.mongo = MongoDB.get_instance()
        self.data = self.mongo.collection("qotd")
        self.guild = guild
        self._new_guild({"pending": [], "accepted": []})

    def suggest(self, question, user) -> None:
        self._push(
            {"pending": {"$each": [{"question": f"{question}", "user": user}]}})

    def decline(self, index) -> Union[None, str]:
        self._remove_array_element_by_index("pending", index)

    def accept(self, index) -> Union[None, str]:
        if question := self._get_array_element_by_index("pending", index):
            self._remove_array_element_by_index("pending", index)
            self._push({"accepted": question})
            return question

    def fetch(self) -> Union[None, str]:
        if question := self._get_array_element_by_index("accepted", 0):
            self._remove_array_element_by_index("accepted", 0)
            return question

    def get_pending(self) -> list:
        return self._get_object("pending")

    def get_accepted(self) -> list:
        return self._get_object("accepted")


class RadioDB(MongoHelper):
    def __init__(self, guild):
        self.mongo = MongoDB.get_instance()
        self.data = self.mongo.collection("radio")
        self.guild = guild
        self._new_guild({"loop": "playlist_repeat", "playlist": []})

    def playlist(self, limit: int = None) -> list:
        if limit:
            return self._get_object("playlist", filter={"playlist": {"$slice": limit}})
        return self._get_object("playlist")

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
        self._set_object({"loop", loop_type})

    def cycle_loop(self) -> bool:
        loops = ["playlist_repeat", "track_repeat",
                 "no_repeat", "playlist_repeat"]
        loop = loops[loops.index(self.get_loop()) + 1]
        self._set_object({"loop": loop})
        return loop

    def shuffle(self) -> None:
        playlist = self.playlist()
        self._set_object({"playlist": random.shuffle(playlist)})


class RoleDB(MongoHelper):
    def __init__(self, guild):
        self.mongo = MongoDB.get_instance()
        self.data = self.mongo.collection("roles")
        self.guild = guild
        self._new_guild()

    def insert(self, id, role) -> None:
        self._set_object({role: id})

    def remove(self, role) -> int:
        id = self.get(role, mention=False)
        self.data.update_one({"_id": self.guild}, {"$unset": {role: True}})
        return id

    def get(self, role, mention=True) -> Union[str, int]:
        if not (role := self._get_object(role)):
            role = 0
        if mention:
            return f'<@&{role}>'
        return role

    def permission_level(self, member) -> int: #TODO test
        if member.guild_permissions.administrator:
            return Roles.ADMINISTRATOR.value

        guild_roles = self.data.find_one(
            {"_id": self.guild}, {"_id": False}).items()
        user_roles = [role.id for role in member.roles]
        user_levels = [
            Roles[role[0]].value for role in guild_roles if role[1] in user_roles]
        if user_levels:
            return max(user_levels)
        else:
            return 0

    def list(self) -> dict:
        return self.data.find_one({"_id": self.guild}, {"_id": False})
