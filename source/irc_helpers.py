from enum import Enum
import re2
import string


class IRCStatusCode(Enum):
    """Think HTTP Status Codes, but for IRC commands.

    Some of these are taken from: <https://www.alien.net.au/irc/irc2numerics.html>
    Others are cobbled together from our understanding of what a gamespy client
    interprets them as.
    """

    IncorrectKey = 475
    MOTDStart = 375
    MOTDPart = 372
    MOTDEnd = 376
    NicknameInUse = 433
    NicknameInvalid = 432
    NotEnoughParameters = 461
    NotInChannel = 442
    NoMOTD = 422
    NoNicknameGiven = 431
    NoOrigin = 409
    NoMessage = 412
    NoReceipent = 411
    PasswordIncorrect = 464
    ReplyEndOfNames = 366
    ReplyIsOn = 303
    ReplyListItem = 322
    ReplyListEnd = 323
    ReplyLUsers = 251
    ReplyClientMode = 221
    ReplyMode = 324
    ReplyMyInfo = 4
    ReplyNoTopic = 331
    ReplySendHost = 2
    ReplyServerCreatedAt = 3
    ReplyTopic = 332
    ReplyWelcome = 1
    ReplyWhoIsUser = 311
    ReplyWhoIsServer = 312
    ReplyWhoIsChannels = 319
    ReplyWhoIsEnd = 318
    ReplyWhoMember = 352
    ReplyWhoEnd = 315
    SuccessfulChanKeyOp = 704
    SuccessfulClientKeyOp = 702
    UnknownCommand = 421
    UnknownChannel = 403
    UnknownMode = 501
    UnknownTarget = 401


__ircstring_translation = str.maketrans(
    string.ascii_lowercase.upper() + "[]\\^", string.ascii_lowercase + "{}|~"
)


def irc_lower(to_lower: str):
    return to_lower.translate(__ircstring_translation)


LINESEP_REGEXP = re2.compile(r"\r?\n")
VALID_NICKNAME_REGEXP = re2.compile(r"^[][\`_^{|}A-Za-z][][\`_^{|}A-Za-z0-9-]{0,50}$")
VALID_CHANNELNAME_REGEXP = re2.compile(r"^[&#+!][^\x00\x07\x0a\x0d ,:]{0,50}$")
