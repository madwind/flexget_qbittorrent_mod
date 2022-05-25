from abc import ABC, abstractmethod


class Detail(ABC):
    @abstractmethod
    def get_details(self, entry, config: dict) -> None:
        pass
