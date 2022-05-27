from __future__ import annotations

from typing import Callable


class Work:
    def __init__(self, url: str, method: Callable, data: dict | None = None,
                 succeed_regex: list[str | tuple] | None = None, fail_regex: str | None = None,
                 assert_state: tuple | None = None, response_urls: list[str] | None = None,
                 use_last_content=False, is_base_content=False, **kwargs) -> None:
        self.url = url
        self.method = method
        self.data = data
        self.succeed_regex = succeed_regex
        self.fail_regex = fail_regex
        self.assert_state = assert_state
        self.use_last_content = use_last_content
        self.is_base_content = is_base_content
        self.response_urls = response_urls if response_urls else [url]
        for key, value in kwargs.items():
            self.__setattr__(key, value)
