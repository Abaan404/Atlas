from discord.ext.commands.errors import CommandError


class ModuleNotFound(CommandError):
    def __init__(self, message=None):
        self.message = message


class PermissionError(CommandError):
    def __init__(self, message=None):
        self.message = message


class DMBlocked(CommandError):
    def __init__(self, message=None):
        self.message = message
