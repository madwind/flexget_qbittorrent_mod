from __future__ import annotations

import re
from abc import ABC, abstractmethod
from enum import Enum

from loguru import logger
from requests import Response

from .entry import SignInEntry
from .request import NetworkState, check_network_state
from .work import Work


class SignState(Enum):
    NO_SIGN_IN = 'No sign in'
    SUCCEED = 'Succeed'
    WRONG_ANSWER = 'Wrong answer'
    SIGN_IN_FAILED = 'Sign in failed, {}'
    UNKNOWN = 'Unknown, url: {}'


class NetworkErrorReason(Enum):
    DDOS_PROTECTION_BY_CLOUDFLARE = 'DDoS protection by .+?Cloudflare'
    SERVER_LOAD_TOO_HIGH = r'<h3 align=center>(服务器负载过|伺服器負載過)高，正在重(试|試)，(请|請)稍(后|後)\.\.\.</h3>'
    CONNECTION_TIMED_OUT = r'<h2 class="text-gray-600 leading-1\.3 text-3xl font-light">Connection timed out</h2>'
    THE_WEB_SERVER_REPORTED_A_BAD_GATEWAY_ERROR = r'<p>The web server reported a bad gateway error\.</p>'
    WEB_SERVER_IS_DOWN = '站点关闭维护中，请稍后再访问...谢谢|站點關閉維護中，請稍後再訪問...謝謝|Web server is down'


def check_state(entry: SignInEntry,
                work: Work,
                response: Response | None,
                content: str | None,
                ) -> bool:
    if entry.failed:
        return False
    if not work.assert_state:
        return True
    check_method, state = work.assert_state
    return check_method(entry, work, response, content) == state


def check_sign_in_state(entry: SignInEntry,
                        work: Work,
                        response: Response | None,
                        content: str | None,
                        ) -> NetworkState | SignState:
    if (network_state := check_network_state(entry, work, response, content=content,
                                             check_content=True)) != NetworkState.SUCCEED:
        return network_state
    if not (succeed_regex := work.succeed_regex):
        entry['result'] = SignState.SUCCEED.value
        return SignState.SUCCEED
    for regex in succeed_regex:
        if isinstance(regex, str):
            regex = (regex, 0)
        regex, group_index = regex
        if succeed_msg := re.search(regex, content):
            entry['result'] = re.sub('<.*?>|&shy;|&nbsp;', '', succeed_msg.group(group_index))
            return SignState.SUCCEED
    if (fail_regex := work.fail_regex) and re.search(fail_regex, content):
        return SignState.WRONG_ANSWER
    for reason in NetworkErrorReason:
        if re.search(reason.value, content):
            entry.fail_with_prefix(
                NetworkState.NETWORK_ERROR.value.format(url=work.url, error=reason.name.title()))
            return NetworkState.NETWORK_ERROR
    if (assert_state := work.assert_state) and assert_state[1] != SignState.NO_SIGN_IN:
        logger.warning(f'no sign in, regex: {succeed_regex}, content: {content}')
    return SignState.NO_SIGN_IN


def check_final_state(entry: SignInEntry,
                      work: Work,
                      response: Response,
                      content: str,
                      ) -> SignState:
    if (sign_in_state := check_sign_in_state(entry, work, response, content)) == SignState.NO_SIGN_IN:
        entry.fail_with_prefix(SignState.SIGN_IN_FAILED.value.format('no sign in'))
        return SignState.SIGN_IN_FAILED
    return sign_in_state


class SignIn(ABC):
    @classmethod
    @abstractmethod
    def sign_in_build_schema(cls) -> dict:
        pass

    @classmethod
    @abstractmethod
    def sign_in_build_entry(cls, entry: SignInEntry, config: dict) -> None:
        pass

    @abstractmethod
    def sign_in(self, entry: SignInEntry, config: dict) -> None:
        pass
