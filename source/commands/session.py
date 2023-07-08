from ..irc_helpers import IRCStatusCode, VALID_NICKNAME_REGEXP
from loguru import logger
from typing import List, TYPE_CHECKING

# Avoid Circular Imports
if TYPE_CHECKING:
    from ..connected_client import ConnectedClient


def away_handler(command: str, arguments: List[str], _: "ConnectedClient") -> None:
    logger.trace(f"{command} reached away handler - {arguments}")


def ison_handler(_: str, arguments: List[str], client: "ConnectedClient") -> None:
    if len(arguments) < 1:
        client.reply_not_enough_parameters("ISON")
        return
    nicks = arguments
    online = [n for n in nicks if client.server.get_client(n)]
    client.reply(
        IRCStatusCode.ReplyIsOn, params=[client.nickname], trailing=" ".join(online)
    )


def nick_handler(_: str, arguments: List[str], client: "ConnectedClient") -> None:
    if len(arguments) < 1:
        client.reply(IRCStatusCode.NoNicknameGiven, trailing="No nickname given")
        return
    newnick = arguments[0]
    new_client = client.server.get_client(newnick)
    if newnick == new_client.nickname if new_client is not None else "":
        pass
    elif new_client and new_client is not client:
        client.reply(
            IRCStatusCode.NicknameInUse,
            params=[client.nickname, new_client.nickname],
            trailing="Nickname is already in use",
        )
    elif not VALID_NICKNAME_REGEXP.match(newnick):
        client.reply(
            IRCStatusCode.NicknameInvalid,
            params=[client.nickname, newnick],
            trailing="Erroneous Nickname",
        )
    else:
        for channel in client.channels.values():
            client.channel_log(channel, f"changed nickname to {newnick}", meta=True)
        oldnickname = client.nickname
        client.message_related(f"NICK {newnick}", True)
        client.nickname = newnick
        client.server.client_changed_nickname(client, oldnickname, newnick)


def quit_handler(_: str, arguments: List[str], client: "ConnectedClient") -> None:
    if len(arguments) < 1:
        quitmsg = client.nickname
    else:
        quitmsg = arguments[0]
    client.disconnect(quitmsg)
