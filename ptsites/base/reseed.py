from abc import ABC, abstractmethod

from flexget.entry import Entry


class Reseed(ABC):
    @classmethod
    @abstractmethod
    def reseed_build_schema(cls):
        pass

    @classmethod
    @abstractmethod
    def reseed_build_entry(cls, entry: Entry, config: dict, site, passkey, torrent_id) -> None:
        pass
