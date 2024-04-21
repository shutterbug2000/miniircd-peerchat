from ..irc_helpers import IRCStatusCode
from loguru import logger
from typing import List, TYPE_CHECKING

# Avoid Circular Imports
if TYPE_CHECKING:
    from ..connected_client import ConnectedClient


def lusers_handler(_: str, __: List[str], client: "ConnectedClient") -> None:
    client.send_lusers()


def motd_handler(_: str, __: List[str], client: "ConnectedClient") -> None:
    client.send_motd()


def names_handler(_: str, arguments: List[str], client: "ConnectedClient") -> None:
    client.send_names(arguments)


def ping_handler(_: str, arguments: List[str], client: "ConnectedClient") -> None:
    if len(arguments) < 1:
        client.reply(
            IRCStatusCode.NoOrigin,
            params=[client.nickname],
            trailing="No origin specified",
        )
        return
    client.raw_add_to_write_buffer(
        f"PONG {client.server.name} :{arguments[0].rstrip()}"
    )


def pong_handler(command: str, arguments: List[str], _: "ConnectedClient") -> None:
    logger.trace(f"{command} reached away handler - {arguments}")


def wallops_handler(_: str, arguments: List[str], client: "ConnectedClient") -> None:
    if len(arguments) < 1:
        client.reply_not_enough_parameters("WALLOPS")
        return
    message = arguments[0]
    for other_client in client.server.clients.values():
        other_client.raw_add_to_write_buffer(
            f":{client.get_prefix()} NOTICE {client.nickname} :Global notice: {message}"
        )


def who_handler(_: str, arguments: List[str], client: "ConnectedClient"):
    if len(arguments) < 1:
        return
    targetname = arguments[0]
    if client.server.has_channel(targetname):
        channel = client.server.get_channel(targetname)
        for member in channel.members:
            client.reply(
                IRCStatusCode.ReplyWhoMember,
                params=[
                    client.nickname,
                    targetname,
                    member.user,
                    member.host,
                    client.server.name,
                    member.nickname,
                    "H",
                ],
                trailing=f"0 {member.realname}",
            )
        client.reply(
            IRCStatusCode.ReplyWhoEnd,
            params=[client.nickname, targetname],
            trailing="End of WHO list",
        )


def whois_handler(_: str, arguments: List[str], client: "ConnectedClient"):
    if len(arguments) < 1:
        return
    username = arguments[0]
    user = client.server.get_client(username)
    if user:
        client.reply(
            IRCStatusCode.ReplyWhoIsUser,
            params=[client.nickname, user.nickname, user.user, user.host, "*"],
            trailing=user.realname,
        )
        client.reply(
            IRCStatusCode.ReplyWhoIsServer,
            params=[client.nickname, user.nickname, client.server.name],
            trailing=user.server.name,
        )
        client.reply(
            IRCStatusCode.ReplyWhoIsChannels,
            params=[client.nickname, user.nickname],
            trailing=" ".join(user.channels),
        )
        client.reply(
            IRCStatusCode.ReplyWhoIsEnd,
            params=[client.nickname, user.nickname],
            trailing="End of WHOIS list",
        )
    else:
        client.reply(
            IRCStatusCode.UnknownTarget,
            params=[client.nickname, username],
            trailing="No such nick",
        )
