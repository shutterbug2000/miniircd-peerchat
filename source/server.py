from __future__ import annotations
from .channel import Channel
from .connected_client import ConnectedClient
from .irc_helpers import irc_lower
from loguru import logger
from optparse import Values
from select import select
from time import time
from typing import List
import os
import socket
import sys


class Server(object):
    def __init__(self, options: Values):
        self.ports: List[int] = options.ports or []
        self.password: str | None = options.password
        self.ssl_pem_file: str | None = options.ssl_pem_file
        self.motdfile: str | None = options.motd
        self.verbose: bool = options.verbose or False
        self.ipv6: bool = options.ipv6 or False
        self.debug: bool = options.debug or False
        self.channel_log_dir: str | None = options.channel_log_dir
        self.chroot: str | None = options.chroot
        self.setuid: List[int] | None = options.setuid
        self.state_dir: str | None = options.state_dir
        self.log_file: str | None = options.log_file
        self.log_max_bytes: int = options.log_max_size * 1024 * 1024
        self.log_count: int = options.log_count or 0
        self.respect_web: bool = options.respect_web or False

        if options.password_file:
            with open(options.password_file, "r") as fp:
                self.password = fp.read().strip("\n")

        if self.ssl_pem_file:
            self.ssl = __import__("ssl")

        # Find certificate after daemonization if path is relative:
        if self.ssl_pem_file and os.path.exists(self.ssl_pem_file):
            self.ssl_pem_file = os.path.abspath(self.ssl_pem_file)
        # else: might exist in the chroot jail, so just continue

        if options.listen and self.ipv6:
            self.address: str = socket.getaddrinfo(
                options.listen, None, proto=socket.IPPROTO_TCP
            )[0][4][0]
        elif options.listen:
            self.address: str = socket.gethostbyname(options.listen)
        else:
            self.address: str = ""
        server_name_limit: int = 63  # From the RFC.
        self.name: str = socket.getfqdn(self.address)[:server_name_limit]

        self.channels: dict[
            str, Channel
        ] = {}  # irc_lower(Channel name) --> Channel instance.
        self.clients: dict[
            socket.socket, ConnectedClient
        ] = {}  # Socket --> Client instance.
        self.nicknames: dict[
            str, ConnectedClient
        ] = {}  # irc_lower(Nickname) --> Client instance.
        if self.channel_log_dir:
            self.__create_directory_if_not_exists(self.channel_log_dir)
        if self.state_dir:
            self.__create_directory_if_not_exists(self.state_dir)

    def client_changed_nickname(
        self,
        client: ConnectedClient,
        old_nickname: str | None,
        new_nickname: str,
    ) -> None:
        if old_nickname:
            del self.nicknames[irc_lower(old_nickname)]
        self.nicknames[irc_lower(new_nickname)] = client

    def daemonize(self) -> None:
        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)
        except OSError:
            sys.exit(1)
        os.setsid()
        try:
            pid = os.fork()
            if pid > 0:
                logger.info("Daemonized PID: {pid}")
                sys.exit(0)
        except OSError:
            sys.exit(1)
        os.chdir("/")
        os.umask(0)
        dev_null = open("/dev/null", "r+")
        os.dup2(dev_null.fileno(), sys.stdout.fileno())
        os.dup2(dev_null.fileno(), sys.stderr.fileno())
        os.dup2(dev_null.fileno(), sys.stdin.fileno())

    def get_channel(self, channel_name: str) -> Channel:
        if irc_lower(channel_name) in self.channels:
            channel = self.channels[irc_lower(channel_name)]
        else:
            channel = Channel(self, channel_name)
            self.channels[irc_lower(channel_name)] = channel
        return channel

    def get_client(self, nickname) -> ConnectedClient | None:
        return self.nicknames.get(irc_lower(nickname))

    def get_motd_lines(self) -> List[str]:
        if self.motdfile:
            try:
                return open(self.motdfile).readlines()
            except IOError:
                return ["Could not read MOTD file %r." % self.motdfile]
        else:
            return []

    def has_channel(self, name: str) -> bool:
        return irc_lower(name) in self.channels

    def make_pid_file(self, filename: str) -> None:
        try:
            fd = os.open(filename, os.O_RDWR | os.O_CREAT | os.O_EXCL, 0o644)
            os.write(fd, f"{os.getpid()}\n".encode("utf-8"))
            os.close(fd)
        except OSError:
            logger.exception("Could not create PID file {filename}")
            sys.exit(1)

    def remove_client(self, client: ConnectedClient, quitmsg: str) -> None:
        client.message_related(f"QUIT :{quitmsg}")
        for x in client.channels.values():
            client.channel_log(x, "quit (%s)" % quitmsg, meta=True)
            x.remove_client(client)
        if client.nickname and irc_lower(client.nickname) in self.nicknames:
            del self.nicknames[irc_lower(client.nickname)]
        del self.clients[client.socket]

    def remove_channel(self, channel):
        del self.channels[irc_lower(channel.name)]

    def remove_member_from_channel(
        self, client: ConnectedClient, channel_name: str
    ) -> None:
        if irc_lower(channel_name) in self.channels:
            channel = self.channels[irc_lower(channel_name)]
            channel.remove_client(client)

    def start(self) -> None:
        serversockets: List[socket.socket] = []
        for port in self.ports:
            s = socket.socket(
                socket.AF_INET6 if self.ipv6 else socket.AF_INET, socket.SOCK_STREAM
            )
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind((self.address, port))
            except socket.error as cause:
                logger.critical(f"Could not bind port {port}: {cause}.")
                sys.exit(1)
            s.listen(5)
            serversockets.append(s)
            del s
            logger.success(f"Listening on port {port}.")
        if self.chroot:
            os.chdir(self.chroot)
            os.chroot(self.chroot)
            logger.success(f"Changed root directory to {self.chroot}")
        if self.setuid:
            os.setgid(self.setuid[1])
            os.setuid(self.setuid[0])
            logger.success(f"Set uid:gid to {self.setuid[0]}:{self.setuid[1]}")

        self.__init_logging()
        try:
            self.__run(serversockets)
        except:
            logger.critical("Fatal exception")
            raise

    def __create_directory_if_not_exists(self, path: str) -> None:
        if not os.path.isdir(path):
            os.makedirs(path)

    def __init_logging(self) -> None:
        if not self.log_file:
            return
        log_level = "INFO"
        if self.debug:
            log_level = "TRACE"
        logger.add(
            self.log_file,
            compression=None,
            enqueue=True,
            format="{time:YYYY-MM-DD HH:mm:ss!UTC} - {name}[{process}] "
            + "- {level} - {message}",
            level=log_level,
            rotation=self.log_max_bytes,
            retention=self.log_count,
        )

    def __run(self, serversockets: List[socket.socket]) -> None:
        last_aliveness_check = time()
        while True:
            (iwtd, owtd, _ewtd) = select(
                serversockets + [x.socket for x in self.clients.values()],
                [x.socket for x in self.clients.values() if x.write_queue_size() > 0],
                [],
                10,
            )
            for x in iwtd:
                if x in self.clients:
                    self.clients[x].socket_readable_notification()
                else:
                    (conn, addr) = x.accept()
                    if self.ssl_pem_file:
                        try:
                            conn = self.ssl.wrap_socket(
                                conn,
                                server_side=True,
                                certfile=self.ssl_pem_file,
                                keyfile=self.ssl_pem_file,
                            )
                        except Exception:
                            logger.exception(
                                f"SSL connection error for {addr[0]}:{addr[1]}"
                            )
                            continue
                    try:
                        self.clients[conn] = ConnectedClient(self, conn)
                        logger.info(f"Accepted connection from {addr[0]}:{addr[1]}.")
                    except socket.error as cause:
                        logger.debug(f"socket error: {cause}")
                        try:
                            conn.close()
                        except OSError:
                            pass

            for x in owtd:
                if x in self.clients:  # client may have been disconnected
                    self.clients[x].socket_writable_notification()
            now = time()
            if last_aliveness_check + 10 < now:
                for client in list(self.clients.values()):
                    client.check_aliveness()
                last_aliveness_check = now
