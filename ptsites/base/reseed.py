from abc import ABC, abstractmethod
from typing import Union

from flexget.entry import Entry


class Reseed(ABC):
    @classmethod
    @abstractmethod
    def reseed_build_schema(cls):
        pass

    @classmethod
    @abstractmethod
    def reseed_build_entry(cls, entry: Entry, config: dict, site: str, passkey: Union[str, dict],
                           torrent_id: str) -> None:
        pass
