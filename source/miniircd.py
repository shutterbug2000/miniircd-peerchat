#!/usr/bin/env python

from .server import Server
from .version import VERSION
from loguru import logger
from optparse import OptionParser
import os
import re
import sys


def start():
    op = OptionParser(
        version=VERSION, description="miniircd is a small and limited IRC server."
    )
    op.add_option(
        "--channel-log-dir", metavar="X", help="store channel log in directory X"
    )
    op.add_option(
        "-d", "--daemon", action="store_true", help="fork and become a daemon"
    )
    op.add_option("--ipv6", action="store_true", help="use IPv6")
    op.add_option("--debug", action="store_true", help="print debug messages to stdout")
    op.add_option("--listen", metavar="X", help="listen on specific IP address X")
    op.add_option(
        "--respect-web",
        action="store_true",
        help="don't completely stomp over the web's responses for the lobby & room",
    )
    op.add_option(
        "--log-count",
        metavar="X",
        default=10,
        type="int",
        help="keep X log files; default: %default",
    )
    op.add_option("--log-file", metavar="X", help="store log in file X")
    op.add_option(
        "--log-max-size",
        metavar="X",
        default=10,
        type="int",
        help="set maximum log file size to X MiB; default: %default MiB",
    )
    op.add_option("--motd", metavar="X", help="display file X as message of the day")
    op.add_option("--pid-file", metavar="X", help="write PID to file X")
    op.add_option(
        "-p",
        "--password",
        metavar="X",
        help="require connection password X; default: no password",
    )
    op.add_option(
        "--password-file",
        metavar="X",
        help=("require connection password stored in file X;" " default: no password"),
    )
    op.add_option(
        "--ports",
        metavar="X",
        help="listen to ports X (a list separated by comma or whitespace);"
        " default: 6667 or 6697 if SSL is enabled",
    )
    op.add_option(
        "-s",
        "--ssl-pem-file",
        metavar="FILE",
        help="enable SSL and use FILE as the .pem certificate+key",
    )
    op.add_option(
        "--state-dir",
        metavar="X",
        help="save persistent channel state (topic, key) in directory X",
    )
    op.add_option(
        "--verbose",
        action="store_true",
        help="be verbose (print some progress messages to stdout)",
    )
    if os.name == "posix":
        op.add_option(
            "--chroot",
            metavar="X",
            help="change filesystem root to directory X after startup"
            " (requires root)",
        )
        op.add_option(
            "--setuid",
            metavar="U[:G]",
            help="change process user (and optionally group) after startup"
            " (requires root)",
        )

    (options, _args) = op.parse_args(sys.argv[1:])
    if options.debug:
        options.verbose = True
    if options.ports is None:
        if options.ssl_pem_file is None:
            options.ports = "6667"
        else:
            options.ports = "6697"
    if options.chroot:
        if os.getuid() != 0:
            op.error("Must be root to use --chroot")
    if options.setuid:
        from pwd import getpwnam
        from grp import getgrnam

        if os.getuid() != 0:
            op.error("Must be root to use --setuid")
        matches = options.setuid.split(":")
        if len(matches) == 2:
            options.setuid = (getpwnam(matches[0]).pw_uid, getgrnam(matches[1]).gr_gid)
        elif len(matches) == 1:
            options.setuid = (getpwnam(matches[0]).pw_uid, getpwnam(matches[0]).pw_gid)
        else:
            op.error(
                "Specify a user, or user and group separated by a colon,"
                " e.g. --setuid daemon, --setuid nobody:nobody"
            )
    if (os.getuid() == 0 or os.getgid() == 0) and not options.setuid:
        op.error(
            "Running this service as root is not recommended. Use the"
            " --setuid option to switch to an unprivileged account after"
            " startup. If you really intend to run as root, use"
            ' "--setuid root".'
        )

    ports = []
    for port in re.split(r"[,\s]+", options.ports):
        try:
            ports.append(int(port))
        except ValueError:
            op.error("bad port: %r" % port)
    options.ports = ports

    server = Server(options)
    if options.daemon:
        server.daemonize()
    if options.pid_file:
        server.make_pid_file(options.pid_file)
    try:
        server.start()
    except KeyboardInterrupt:
        logger.error("Interrupted.")
