from discord import app_commands
from scripts.database import ModuleDB, RoleDB


class ModuleDisabled(app_commands.errors.AppCommandError):
    pass


class PermissionError(app_commands.errors.AppCommandError):
    pass


class ChannelError(app_commands.errors.AppCommandError):
    def __init__(self, message: str | None = None, *args, channel_id: int) -> None:
        self.channel_id = channel_id
        super().__init__(message, *args)


class AtlasPermissions:
    @staticmethod
    def verify_channel(module):
        def predicate(ctx):
            if (channel_id := ModuleDB(ctx.guild.id).get_config(module, "channel")) != ctx.channel.id:
                raise ChannelError(channel_id=channel_id)
            return True
        return app_commands.check(predicate)

    @staticmethod
    def verify_level(role):
        def predicate(interaction):
            if not RoleDB(interaction.guild.id).permission_level(interaction.user) >= role.value:
                raise PermissionError
            return True
        return app_commands.check(predicate)
