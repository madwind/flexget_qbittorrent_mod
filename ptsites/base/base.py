from enum import Enum
from typing import Union


class SignState(Enum):
    NO_SIGN_IN = 'No sign in'
    SUCCEED = 'Succeed'
    WRONG_ANSWER = 'Wrong answer'
    SIGN_IN_FAILED = 'Sign in failed, {}'
    UNKNOWN = 'Unknown, url: {}'


class NetworkState(Enum):
    SUCCEED = 'Succeed'
    URL_REDIRECT = 'Url: {original_url} redirect to {redirect_url}'
    NETWORK_ERROR = 'Network error: url: {url}, error: {error}'


class NetworkErrorReason(Enum):
    DDoS_protection_by_Cloudflare = 'DDoS protection by .+?Cloudflare'
    Server_load_too_high = r'<h3 align=center>(服务器负载过|伺服器負載過)高，正在重(试|試)，(请|請)稍(后|後)\.\.\.</h3>'
    Connection_timed_out = r'<h2 class="text-gray-600 leading-1\.3 text-3xl font-light">Connection timed out</h2>'
    The_web_server_reported_a_bad_gateway_error = r'<p>The web server reported a bad gateway error\.</p>'
    Web_server_is_down = '站点关闭维护中，请稍后再访问...谢谢|站點關閉維護中，請稍後再訪問...謝謝|Web server is down'


class Work:
    def __init__(self, url: str = None, method: str = None, data=None,
                 succeed_regex: Union[list[Union[str, tuple]], tuple[str, int]] = None, fail_regex: str = None,
                 check_state: tuple = None, response_urls=None, is_base_content=False, **kwargs):
        self.url: str = url
        self.method = method
        self.data = data
        self.succeed_regex = succeed_regex
        self.fail_regex = fail_regex
        self.check_state = check_state
        self.is_base_content = is_base_content
        self.response_urls = response_urls if response_urls else [url]
        for key, value in kwargs.items():
            self.__setattr__(key, value)
