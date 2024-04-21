from __future__ import annotations
from .pkg4.encoding import dwc_encode
from .pkg4.generator import generate_random_lobby
from typing import Tuple, TYPE_CHECKING
import os
import tempfile

# Avoid Circular imports.
if TYPE_CHECKING:
    from .connected_client import ConnectedClient
    from .server import Server


class Channel(object):
    def __init__(self, server: Server, name: str):
        self.name: str = name
        self.members: set[ConnectedClient] = set()
        self.server: Server = server
        self.__topic: str = ""
        self.__key: str | None = None
        if self.server.state_dir:
            state_file_path = name.replace("_", "__").replace("/", "_")
            self.__state_path = f"{self.server.state_dir}/{state_file_path}"
            self.__read_state()
        else:
            self.__state_path = None
        if self.server.respect_web:
            self.__serialized_lobby: str | None = None
        else:
            self.__serialized_lobby: str | None = dwc_encode(
                generate_random_lobby().to_serialized()
            )
        self.__serialized_world_data: str | None = None
        # This can be dependent on the time from the DS in order to
        # properly forward time.
        #
        # This was the timestamp constant we used before.
        self.started_at_time = 560470305
        self.client_keys: dict[Tuple[str, str], str] = {}

    def add_member(self, client):
        self.members.add(client)

    def get_key(self):
        return self.__key

    def set_key(self, value: str | None):
        self.__key = value
        self.__write_state()

    key = property(get_key, set_key)

    def get_topic(self):
        return self.__topic

    def set_topic(self, value: str):
        self.__topic = value
        self.__write_state()

    topic = property(get_topic, set_topic)

    def get_serialized_lobby(self):
        return self.__serialized_lobby

    def set_serialized_lobby(self, value: str):
        self.__serialized_lobby = value
        self.__write_state()

    serialized_lobby = property(get_serialized_lobby, set_serialized_lobby)

    def get_serialized_world_data(self):
        return self.__serialized_world_data

    def set_serialized_world_data(self, value: str):
        self.__serialized_world_data = value
        self.__write_state()

    serialized_world_data = property(
        get_serialized_world_data, set_serialized_world_data
    )

    def remove_client(self, client: ConnectedClient) -> None:
        self.members.discard(client)
        if not self.members:
            self.server.remove_channel(self)

    def __read_state(self):
        if not (self.__state_path and os.path.exists(self.__state_path)):
            return
        data = {}

        with open(self.__state_path, "rb") as state_file:
            exec(state_file.read(), {}, data)

        self.__topic = data.get("topic", "")
        self.__key = data.get("key")
        self.__serialized_lobby = data.get("serialized_lobby", None)
        self.__serialized_world_data = data.get("serialized_world_data", None)

    def __write_state(self):
        if not self.__state_path:
            return
        (fd, path) = tempfile.mkstemp(dir=os.path.dirname(self.__state_path))
        fp = os.fdopen(fd, "w")
        fp.write(f"topic = {self.__topic}\n")
        fp.write(f"key = {self.__key}\n")
        fp.write(f"serialized_lobby = {self.__serialized_lobby}\n")
        fp.write(f"serialized_world_data = {self.__serialized_world_data}\n")
        fp.close()
        os.rename(path, self.__state_path)
