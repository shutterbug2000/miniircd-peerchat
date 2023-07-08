from ..irc_helpers import irc_lower, IRCStatusCode, VALID_CHANNELNAME_REGEXP
from ..pkg4.encoding import dwc_decode, dwc_encode
from ..pkg4.lobby import PkWifiLobby
from ..pkg4.time import LobbyStartTime
from ..pkg4.world_data import LobbyWorldData
import binascii
import struct
from loguru import logger
from typing import List, Union, TYPE_CHECKING

# Avoid Circular Imports
if TYPE_CHECKING:
    from ..connected_client import ConnectedClient


def getchankey_handler(_: str, arguments: List[str], client: "ConnectedClient") -> None:
    if len(arguments) < 4:
        client.reply_not_enough_parameters("GETCHANKEY")
        return

    key = arguments[3]
    channel = client.channels[irc_lower(arguments[0])]
    if not channel:
        client.reply(
            IRCStatusCode.UnknownTarget,
            params=[client.nickname, arguments[0]],
            trailing="No such channel",
        )
        return
    value = None
    # if we bumped to python3.10 we'd get match!!! but people running old stuff
    if key == "\\b_lby_wlddata":
        value = channel.serialized_world_data
    elif key == "\\b_lib_c_lobby":
        value = channel.serialized_lobby
    elif key == "\\b_lib_c_time":
        value = dwc_encode(LobbyStartTime(channel.started_at_time).to_serialized())
    client.reply(
        IRCStatusCode.SuccessfulChanKeyOp,
        params=[client.nickname, channel.name, arguments[1]],
        trailing=f"{key}\\{value}",
    )


def getclientkey_handler(
    _: str, arguments: List[str], client: "ConnectedClient"
) -> None:
    channel = client.channels[irc_lower(arguments[0])]
    if not channel:
        client.reply(
            IRCStatusCode.UnknownTarget,
            params=[client.nickname, arguments[0]],
            trailing="No such channel",
        )
        return
    value = None
    if arguments[4] == "\\b_lib_u_user":
        value = channel.client_keys[(arguments[1], "user")]
    elif arguments[4] == "\\b_lib_u_system":
        value = channel.client_keys[(arguments[1], "system")]
    client.reply(
        IRCStatusCode.SuccessfulClientKeyOp,
        params=[
            client.nickname,
            arguments[0],
            arguments[1],
            arguments[2],
        ],
        trailing=f"\\{value}",
    )


def join_handler(_: str, arguments: List[str], client: "ConnectedClient") -> None:
    if len(arguments) < 1:
        client.reply_not_enough_parameters("JOIN")
        return
    if arguments[0] == "0":
        for channel_name, channel in client.channels.items():
            client.message_channel(channel, "PART", channel_name, True)
            client.channel_log(channel, "left", meta=True)
            client.server.remove_member_from_channel(client, channel_name)
        client.channels = {}
        return
    client.send_names(arguments, for_join=True)


def list_handler(_: str, __: List[str], client: "ConnectedClient") -> None:
    channels = client.server.channels.values()
    sorted_channels = sorted(channels, key=lambda x: x.name)
    for channel in sorted_channels:
        client.reply(
            IRCStatusCode.ReplyListItem,
            params=[client.nickname, channel.name, str(len(channel.members))],
            trailing=channel.topic,
        )
    client.reply(
        IRCStatusCode.ReplyListEnd, params=[client.nickname], trailing="End of LIST"
    )


def part_handler(_: str, arguments: List[str], client: "ConnectedClient") -> None:
    if len(arguments) < 1:
        client.reply_not_enough_parameters("PART")
        return
    if len(arguments) > 1:
        partmsg = arguments[1]
    else:
        partmsg = client.nickname
    for channelname in arguments[0].split(","):
        if not VALID_CHANNELNAME_REGEXP.match(channelname):
            client.reply(
                IRCStatusCode.UnknownChannel,
                params=[client.nickname, channelname],
                trailing="No such channel",
            )
        elif irc_lower(channelname) not in client.channels:
            client.reply(
                IRCStatusCode.NotInChannel,
                params=[client.nickname, channelname],
                trailing="You're not in that channel",
            )
        else:
            channel = client.channels[irc_lower(channelname)]
            client.message_channel(channel, "PART", f"{channelname} :{partmsg}", True)
            client.channel_log(channel, f"left ({partmsg})", meta=True)
            del client.channels[irc_lower(channelname)]
            client.server.remove_member_from_channel(client, channelname)


def setchankey_handler(_: str, arguments: List[str], client: "ConnectedClient") -> None:
    channel = client.channels[irc_lower(arguments[0])]
    if not channel:
        client.reply(
            IRCStatusCode.UnknownTarget,
            params=[client.nickname, arguments[0]],
            trailing="No such channel",
        )
        return
    if arguments[1][:13] == "\\b_lib_c_time":
        # This is fine, we don't need to take their start time.
        #
        # We've got our own.
        pass
    elif arguments[1][:14] == "\\b_lib_c_lobby":
        serialized = arguments[1][14:]
        # Ensure someone doesn't try to overflow games internal receive buffer
        if len(serialized) > 384:
            client.disconnect("WifiPlaza lobby data too long.")
            return
        try:
            decoded = dwc_decode(serialized)
            _deserialized = PkWifiLobby.from_serialized(decoded)
        except Union[binascii.Error, struct.error]:
            logger.error(f"Failed to decode \\b_lib_c_lobby data: {serialized}")
        channel.serialized_lobby = serialized
    elif arguments[1][:13] == "\\b_lby_wlddata":
        serialized = arguments[1][13:]
        if len(serialized) > 8:
            client.disconnect("Lobby World Data too long")
            return
        try:
            decoded = dwc_decode(serialized)
            _deserialized = LobbyWorldData.from_serialized(decoded)
        except Union[binascii.Error, struct.error]:
            logger.error(f"Failed to decode \\b_lby_wlddata data: {serialized}")
        channel.serialized_world_data = serialized
    for i in range(0, len(list(channel.members))):
        list(channel.members)[i].reply(
            IRCStatusCode.SuccessfulChanKeyOp,
            params=[arguments[0], arguments[0], "BCAST"],
            trailing=arguments[1],
        )


def setclientkey_handler(
    _: str, arguments: List[str], client: "ConnectedClient"
) -> None:
    channel = client.channels[irc_lower(arguments[0])]
    if not channel:
        client.reply(
            IRCStatusCode.UnknownTarget,
            params=[client.nickname, arguments[0]],
            trailing="No such channel",
        )
        return
    if arguments[2][:13] == "\\b_lib_u_user":
        value = arguments[2][14:]
        if len(value) != 200:
            client.disconnect("b_lib_u_user too long!!")
            return
        # The `b_lib_u_user` is the same sent to `checkProfile.asp` on the web.
        #
        # I don't wanna port this yet :(
        try:
            _decoded = dwc_decode(value)
        except binascii.Error:
            logger.error(f"Failed to decode \\b_lib_u_user data: {value}")
        channel.client_keys[(client.nickname or "", "user")] = value
    elif arguments[2][:15] == "\\b_lib_u_system":
        value = arguments[2][16:]
        if len(value) > 24:
            client.disconnect("b_lib_u_system too long!")
            return
        # The system data is just some values, nothing important
        # seemingly some timestamps, channel types, and some unknown data.
        #
        # I haven't spent a whle bunch of time validating it yet. Sorry
        try:
            _decoded = dwc_decode(value)
        except binascii.Error:
            logger.error(f"Failed to decode \\b_lib_u_system data: {value}")
        channel.client_keys[(client.nickname or "", "system")] = value
    channel = client.channels[irc_lower(arguments[0])]
    for i in range(0, len(list(channel.members))):
        list(channel.members)[i].reply(
            IRCStatusCode.SuccessfulClientKeyOp,
            params=[arguments[0], arguments[0], arguments[1], "BCAST"],
            trailing=arguments[2],
        )


def topic_handler(_: str, arguments: List[str], client: "ConnectedClient") -> None:
    if len(arguments) < 1:
        client.reply_not_enough_parameters("TOPIC")
        return
    channelname = arguments[0]
    channel = client.channels.get(irc_lower(channelname))
    if channel:
        if len(arguments) > 1:
            newtopic = arguments[1]
            channel.topic = newtopic
            client.message_channel(channel, "TOPIC", f"{channelname} :{newtopic}", True)
            client.channel_log(channel, f"set topic to {newtopic}", meta=True)
        else:
            if channel.topic:
                client.reply(
                    IRCStatusCode.ReplyTopic,
                    params=[client.nickname, channel.name],
                    trailing=channel.topic,
                )
            else:
                client.reply(
                    IRCStatusCode.ReplyNoTopic,
                    params=[client.nickname, channel.name],
                    trailing="No topic is set.",
                )
    else:
        client.reply(
            IRCStatusCode.NotInChannel,
            params=[channelname],
            trailing="You're not in that channel",
        )
