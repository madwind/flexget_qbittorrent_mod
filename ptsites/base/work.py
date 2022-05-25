from typing import Union


class Work:
    def __init__(self, url: str = None, method: callable = None, data=None,
                 succeed_regex: list[Union[str, tuple]] = None, fail_regex: str = None,
                 assert_state: tuple = None, response_urls=None, is_base_content=False, **kwargs):
        self.url: str = url
        self.method = method
        self.data = data
        self.succeed_regex = succeed_regex
        self.fail_regex = fail_regex
        self.assert_state = assert_state
        self.is_base_content = is_base_content
        self.response_urls = response_urls if response_urls else [url]
        for key, value in kwargs.items():
            self.__setattr__(key, value)
