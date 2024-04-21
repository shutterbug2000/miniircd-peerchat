from __future__ import annotations
from .commands.channel import (
    getchankey_handler,
    getclientkey_handler,
    join_handler,
    list_handler,
    part_handler,
    setchankey_handler,
    setclientkey_handler,
    topic_handler,
)
from .commands.channel_or_session import (
    mode_handler,
    notice_and_privmsg_handler,
    utm_handler,
)
from .commands.global_commands import (
    lusers_handler,
    motd_handler,
    names_handler,
    ping_handler,
    pong_handler,
    wallops_handler,
    who_handler,
    whois_handler,
)
from .commands.session import (
    away_handler,
    ison_handler,
    nick_handler,
    quit_handler,
)
from .irc_helpers import (
    IRCStatusCode,
    irc_lower,
    LINESEP_REGEXP,
    VALID_CHANNELNAME_REGEXP,
    VALID_NICKNAME_REGEXP,
)
from .version import VERSION
from datetime import datetime
from loguru import logger
from socket import socket
from time import time
from typing import Callable, List, TYPE_CHECKING

# Avoid Circular imports.
if TYPE_CHECKING:
    from .channel import Channel
    from .server import Server


class ConnectedClient(object):
    def __init__(self, server: Server, socket: socket):
        self.server: Server = server
        self.socket = socket
        # irc_lower(Channel name) --> Channel
        self.channels: dict[str, "Channel"] = {}
        self.nickname: str | None = None
        self.user: str | None = None
        self.realname: str | None = None
        if self.server.ipv6:
            (self.host, self.port, _, _) = socket.getpeername()
        else:
            (self.host, self.port) = socket.getpeername()
        self.__timestamp = time()
        self.__readbuffer = ""
        self.__writebuffer = ""
        self.__sent_ping = False
        if self.server.password:
            self.__handle_command = self.__pass_handler
        else:
            self.__handle_command = self.__registration_handler

    def channel_log(self, channel: "Channel", message: str, meta=False) -> None:
        if not self.server.channel_log_dir:
            return
        if meta:
            format = "[%s] * %s %s\n"
        else:
            format = "[%s] <%s> %s\n"
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        logname = channel.name.replace("_", "__").replace("/", "_")
        fp = open(f"{self.server.channel_log_dir}/{logname}.log", "a")
        fp.write(format % (timestamp, self.nickname, message))
        fp.close()

    def check_aliveness(self) -> None:
        now = time()
        if self.__timestamp + 180 < now:
            self.disconnect("ping timeout")
            return
        if not self.__sent_ping and self.__timestamp + 90 < now:
            if self.__handle_command == self.__command_handler:
                # Registered.
                self.raw_add_to_write_buffer(f"PING :{self.server.name}")
                self.__sent_ping = True
            else:
                # Not registered.
                self.disconnect("ping timeout")

    def disconnect(self, quitmsg) -> None:
        self.raw_add_to_write_buffer(f"ERROR :{quitmsg}")
        logger.info(
            f"Disconnected connection from {self.host}:{self.port} ({quitmsg})."
        )
        self.socket.close()
        self.server.remove_client(self, quitmsg)

    def get_prefix(self) -> str:
        return f"{self.nickname}!{self.user}@{self.host}"

    def send_lusers(self) -> None:
        self.reply(
            IRCStatusCode.ReplyLUsers,
            params=[self.nickname],
            trailing=f"There are {len(self.server.clients)} "
            + "user and 0 services on 1 server",
        )

    def message_channel(
        self, channel: "Channel", command: str, message: str, include_self=False
    ) -> None:
        line = ":%s %s %s" % (self.get_prefix(), command, message)
        for client in channel.members:
            if client != self or include_self:
                client.raw_add_to_write_buffer(line)

    def message_related(self, msg: str, include_self=False) -> None:
        clients = set()
        for channel in self.channels.values():
            clients |= channel.members
        if not include_self:
            clients.discard(self)
        for client in clients:
            client.raw_add_to_write_buffer(f":{self.get_prefix()} {msg}")

    def reply(
        self,
        status: IRCStatusCode,
        params: List[str | None] = [],
        trailing: str | None = "",
    ) -> None:
        status_code = str(status.value).zfill(3)
        message = f":s {status_code}"
        for parameter in params:
            if parameter is not None:
                message += f" {parameter.rstrip()}"
            else:
                message += " *"
        if trailing is not None and len(trailing) > 0:
            message += f" :{trailing.rstrip()}"
        self.raw_add_to_write_buffer(message)

    def reply_not_enough_parameters(self, command: str) -> None:
        nickname = self.nickname or "*"
        self.reply(
            IRCStatusCode.NotEnoughParameters,
            params=[nickname, command],
            trailing="Not Enough Parameters",
        )

    def send_motd(self) -> None:
        server = self.server
        motdlines = server.get_motd_lines()
        if motdlines:
            self.reply(
                IRCStatusCode.MOTDStart,
                params=[self.nickname],
                trailing=f"- {server.name} Message of the day-",
            )
            for line in motdlines:
                self.reply(
                    IRCStatusCode.MOTDPart,
                    params=[self.nickname],
                    trailing=f"- {line.rstrip()}",
                )
            self.reply(
                IRCStatusCode.MOTDEnd,
                params=[self.nickname],
                trailing="End of /MOTD command",
            )
        else:
            self.reply(
                IRCStatusCode.NoMOTD,
                params=[self.nickname],
                trailing="MOTD File is missing",
            )

    def send_names(self, arguments: List[str], for_join=False) -> None:
        server = self.server
        valid_channel_re = VALID_CHANNELNAME_REGEXP
        if len(arguments) > 0:
            channelnames = arguments[0].split(",")
        else:
            channelnames = sorted(self.channels.keys())
        if len(arguments) > 1:
            keys: List[str | None] = list(arguments[1].split(","))
        else:
            keys: List[str | None] = []
        keys.extend((len(channelnames) - len(keys)) * [None])
        for idx, channel_name in enumerate(channelnames):
            if for_join and irc_lower(channel_name) in self.channels:
                continue
            if not valid_channel_re.match(channel_name):
                self.__reply_unknown_channel(channel_name)
                continue
            channel = server.get_channel(channel_name)
            if channel.key is not None and channel.key != keys[idx]:
                self.reply(
                    IRCStatusCode.IncorrectKey,
                    params=[self.nickname, channel_name],
                    trailing="Cannot join channel (+k) - bad key",
                )
                continue
            if for_join:
                channel.add_member(self)
                self.channels[irc_lower(channel_name)] = channel
                self.message_channel(channel, "JOIN", channel_name, True)
                self.channel_log(channel, "joined", meta=True)
                if channel.topic:
                    self.reply(
                        IRCStatusCode.ReplyTopic,
                        params=[self.nickname, channel.name],
                        trailing=channel.topic,
                    )
                else:
                    self.reply(
                        IRCStatusCode.ReplyNoTopic,
                        params=[self.nickname, channel.name],
                        trailing="No topic is set",
                    )
            names_prefix = "353 %s = %s :" % (self.nickname, channel_name)
            names = ""
            # Max length: reply prefix ":server_name(space)" plus CRLF in
            # the end.
            names_max_len = 512 - (len(server.name) + 2 + 2)
            for name in sorted(x.nickname or "" for x in channel.members):
                if name == "":
                    continue
                if not names:
                    names = names_prefix + name
                # Using >= to include the space between "names" and "name".
                elif len(names) + len(name) >= names_max_len:
                    self.raw_add_to_write_buffer(names)
                    names = names_prefix + name
                else:
                    names += " " + name
            if names:
                self.raw_add_to_write_buffer(names)
            self.reply(
                IRCStatusCode.ReplyEndOfNames,
                params=[self.nickname, channel_name],
                trailing="End of NAMES list",
            )

    def socket_readable_notification(self) -> None:
        try:
            data = self.socket.recv(2**10)
            logger.debug(f"[{self.host}:{self.port}] -> {data}")
            quitmsg = "EOT"
        except OSError as cause:
            data = ""
            quitmsg = cause
        if data:
            self.__readbuffer += self.__socket_to_buffer(data)
            self.__parse_read_buffer()
            self.__timestamp = time()
            self.__sent_ping = False
        else:
            self.disconnect(quitmsg)

    def socket_writable_notification(self) -> None:
        try:
            sent = self.socket.send(self.__buffer_to_socket(self.__writebuffer))
            logger.debug(f"[{self.host}:{self.port}] <- {self.__writebuffer[:sent]}")
            self.__writebuffer = self.__writebuffer[sent:]
        except OSError as cause:
            self.disconnect(cause)

    def write_queue_size(self) -> int:
        return len(self.__writebuffer)

    def raw_add_to_write_buffer(self, msg: str) -> None:
        self.__writebuffer += msg.replace("\r\n", "").replace("\n", "") + "\r\n"

    def __buffer_to_socket(self, msg: str) -> bytes:
        return msg.encode()

    def __command_handler(self, command: str, arguments: List[str]) -> None:
        handler_table: dict[str, Callable[[str, List[str], ConnectedClient], None]] = {
            "AWAY": away_handler,
            "GETCHANKEY": getchankey_handler,
            "GETCKEY": getclientkey_handler,
            "ISON": ison_handler,
            "JOIN": join_handler,
            "LIST": list_handler,
            "LUSERS": lusers_handler,
            "MODE": mode_handler,
            "MOTD": motd_handler,
            "NAMES": names_handler,
            "NOTICE": notice_and_privmsg_handler,
            "NICK": nick_handler,
            "PART": part_handler,
            "PING": ping_handler,
            "PONG": pong_handler,
            "PRIVMSG": notice_and_privmsg_handler,
            "QUIT": quit_handler,
            "SETCHANKEY": setchankey_handler,
            "SETCKEY": setclientkey_handler,
            "TOPIC": topic_handler,
            "UTM": utm_handler,
            "WALLOPS": wallops_handler,
            "WHO": who_handler,
            "WHOIS": whois_handler,
        }
        try:
            handler_table[command.upper()](command, arguments, self)
        except KeyError:
            logger.debug(f"421 {self.nickname} {command} :Unknown command")
            self.reply(
                IRCStatusCode.UnknownCommand,
                params=[self.nickname, command],
                trailing="Unknown command",
            )

    def __parse_read_buffer(self) -> None:
        lines = LINESEP_REGEXP.split(self.__readbuffer)
        self.__readbuffer = lines[-1]
        lines = lines[:-1]
        for line in lines:
            if not line:
                # Empty line. Ignore.
                continue
            x = line.split(" ", 1)
            command = x[0].upper()
            if len(x) == 1:
                arguments = []
            else:
                if len(x[1]) > 0 and x[1][0] == ":":
                    arguments = [x[1][1:]]
                else:
                    y = x[1].split(" :", 1)
                    arguments = y[0].split()
                    if len(y) == 2:
                        arguments.append(y[1])
            self.__handle_command(command, arguments)

    def __pass_handler(self, command: str, arguments: List[str]) -> None:
        server = self.server
        if command == "PASS":
            if len(arguments) == 0:
                self.reply_not_enough_parameters("PASS")
            else:
                if arguments[0].lower() == server.password:
                    self.__handle_command = self.__registration_handler
                else:
                    self.reply(
                        IRCStatusCode.PasswordIncorrect, trailing="Password incorrect"
                    )
        elif command == "QUIT":
            self.disconnect("Client quit")

    def __registration_handler(self, command: str, arguments: List[str]) -> None:
        server = self.server
        if command == "NICK":
            if len(arguments) < 1:
                self.reply(IRCStatusCode.NoNicknameGiven, trailing="No nickname given")
                return
            nick = arguments[0]
            if server.get_client(nick):
                self.reply(
                    IRCStatusCode.NicknameInUse,
                    params=["*", nick],
                    trailing="Nickname is already in use",
                )
            elif not VALID_NICKNAME_REGEXP.match(nick):
                self.reply(
                    IRCStatusCode.NicknameInvalid,
                    params=["*", nick],
                    trailing="Erroneous nickname",
                )
            else:
                self.nickname = nick
                server.client_changed_nickname(self, None, self.nickname)
        elif command == "USER":
            if len(arguments) < 4:
                self.reply_not_enough_parameters("USER")
                return
            self.user = arguments[0]
            self.realname = arguments[3]
        elif command == "QUIT":
            self.disconnect("Client quit")
            return
        if self.nickname and self.user:
            self.reply(
                IRCStatusCode.ReplyWelcome,
                params=[self.nickname],
                trailing="Hi, welcome to IRC",
            )
            self.reply(
                IRCStatusCode.ReplySendHost,
                params=[self.nickname],
                trailing=f"Your host is {server.name}, running version "
                + f"miniircd-{VERSION}",
            )
            self.reply(
                IRCStatusCode.ReplyServerCreatedAt,
                params=[self.nickname],
                trailing="This server was created sometime",
            )
            self.reply(
                IRCStatusCode.ReplyMyInfo,
                params=[self.nickname, server.name, f"miniircd-{VERSION}", "o", "o"],
            )
            self.send_lusers()
            self.send_motd()
            self.__handle_command = self.__command_handler

    def __reply_unknown_channel(self, channel: str) -> None:
        self.reply(
            IRCStatusCode.UnknownChannel,
            params=[self.nickname, channel],
            trailing="No such channel",
        )

    def __socket_to_buffer(self, buf: bytes) -> str:
        return buf.decode(errors="ignore")
