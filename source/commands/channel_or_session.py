from ..irc_helpers import IRCStatusCode, irc_lower
from ..pkg4.user_message import UTMMessage
from loguru import logger
from typing import List, TYPE_CHECKING

# Avoid Circular Imports
if TYPE_CHECKING:
    from ..connected_client import ConnectedClient


def mode_handler(_: str, arguments: List[str], client: "ConnectedClient") -> None:
    if len(arguments) < 1:
        client.reply_not_enough_parameters("MODE")
        return
    targetname = arguments[0]
    if client.server.has_channel(targetname):
        channel = client.server.get_channel(targetname)
        if len(arguments) < 2:
            if channel.key:
                modes = "+k"
                if irc_lower(channel.name) in client.channels:
                    modes += " %s" % channel.key
            else:
                modes = "+"
            client.reply(
                IRCStatusCode.ReplyMode, params=[client.nickname, targetname, modes]
            )
            return
        flag = arguments[1]
        if flag == "+k":
            if len(arguments) < 3:
                client.reply_not_enough_parameters("MODE")
                return
            key = arguments[2]
            if irc_lower(channel.name) in client.channels:
                channel.key = key
                client.message_channel(
                    channel, "MODE", f"{channel.name} +k {key}", True
                )
                client.channel_log(channel, f"set channel key to {key}", meta=True)
            else:
                client.reply(
                    IRCStatusCode.NotInChannel,
                    params=[targetname],
                    trailing="You're not in that channel",
                )
        elif flag == "-k":
            if irc_lower(channel.name) in client.channels:
                channel.key = None
                client.message_channel(channel, "MODE", f"{channel.name} -k", True)
                client.channel_log(channel, "removed channel key", meta=True)
            else:
                client.reply(
                    IRCStatusCode.NotInChannel,
                    params=[targetname],
                    trailing="You're not in that channel",
                )
        else:
            print("lolnope")
            client.raw_add_to_write_buffer(
                f"MODE {arguments[0]} {arguments[1]} {arguments[2]}"
            )
            # self.reply("472 %s %s :Unknown MODE flag"
            #           % (self.nickname, flag))
    elif targetname == client.nickname:
        if len(arguments) == 1:
            client.reply(IRCStatusCode.ReplyClientMode, params=[client.nickname, "+"])
        else:
            client.reply(
                IRCStatusCode.UnknownMode,
                params=[client.nickname],
                trailing="Unknown MODE flag",
            )
    else:
        client.reply_not_enough_parameters(targetname)


def notice_and_privmsg_handler(
    command: str, arguments: List[str], client: "ConnectedClient"
) -> None:
    if len(arguments) == 0:
        client.reply(
            IRCStatusCode.NoReceipent,
            params=[client.nickname],
            trailing=f"No receipient given ({command})",
        )
        return
    if len(arguments) == 1:
        client.reply(
            IRCStatusCode.NoMessage,
            params=[client.nickname],
            trailing="No text to send",
        )
        return
    targetname = arguments[0]
    message = arguments[1]
    new_client = client.server.get_client(targetname)
    if new_client:
        new_client.raw_add_to_write_buffer(
            f":{client.get_prefix()} {command} {targetname} :{message}"
        )
    elif client.server.has_channel(targetname):
        channel = client.server.get_channel(targetname)
        client.message_channel(channel, command, f"{channel.name} :{message}")
        client.channel_log(channel, message)
    else:
        client.reply(
            IRCStatusCode.UnknownTarget,
            params=[client.nickname, targetname],
            trailing="No such nick/channel",
        )


def utm_handler(_: str, arguments: List[str], client: "ConnectedClient") -> None:
    if len(arguments) < 2:
        client.reply_not_enough_parameters("UTM")
        return
    try:
        UTMMessage(arguments[1])
    except Exception as cause:
        logger.error(f"Failed to parse UTM message: {arguments[1]} / {cause}")
    if arguments[0][0] != "#":
        for j in range(0, len(client.channels)):
            channel = client.channels[list(client.channels)[j]]
            for i in range(0, len(list(channel.members))):
                if list(channel.members)[i].nickname == arguments[0]:
                    list(channel.members)[i].raw_add_to_write_buffer(
                        f":{client.get_prefix()} UTM {arguments[0]} :{arguments[1]}"
                    )
    if arguments[0][0] == "#":
        channel = client.channels[irc_lower(arguments[0])]
        for i in range(0, len(list(channel.members))):
            list(channel.members)[i].raw_add_to_write_buffer(
                f":{client.get_prefix()} UTM {arguments[0]} :{arguments[1]}"
            )
