from abc import ABC, abstractmethod


class Message(ABC):
    @abstractmethod
    def get_messages(self, entry, config: dict):
        pass
