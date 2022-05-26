from abc import ABC, abstractmethod

from ptsites.base.entry import SignInEntry


class Message(ABC):
    @abstractmethod
    def get_messages(self, entry: SignInEntry, config: dict) -> None:
        pass
