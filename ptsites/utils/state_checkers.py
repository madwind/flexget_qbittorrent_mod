import re
import sys
from typing import Union

from flexget.entry import Entry
from loguru import logger
from requests import Response

from ..base.base import Work, NetworkState, SignState, NetworkErrorReason


def check_state(entry: Entry, work: Work, response: Response, content: str) -> bool:
    if entry.failed:
        return False
    check_type, check_result = work.check_state
    if check := getattr(sys.modules[__name__], f"check_{check_type}_state", None):
        return check(entry, work, response, content) == check_result


def check_network_state(entry, param: Union[Work, str, list[str]], response: Response,
                        content: str = None, check_content=False) -> NetworkState:
    urls = param
    if isinstance(param, Work):
        urls = param.response_urls
    elif isinstance(param, str):
        urls = [param]
    if response is None or (check_content and content is None):
        entry.fail_with_prefix(NetworkState.NETWORK_ERROR.value.format(url=urls[0], error='Response is None'))
        return NetworkState.NETWORK_ERROR
    if response.url not in urls:
        entry.fail_with_prefix(
            NetworkState.URL_REDIRECT.value.format(original_url=urls[0], redirect_url=response.url))
        return NetworkState.URL_REDIRECT
    return NetworkState.SUCCEED


def check_sign_in_state(entry, work: Work, response: Response,
                        content: str) -> Union[NetworkState, SignState]:
    network_state = check_network_state(entry, work, response, content=content, check_content=True)
    if network_state != NetworkState.SUCCEED:
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
    if fail_regex := work.fail_regex:
        if re.search(fail_regex, content):
            return SignState.WRONG_ANSWER

    for reason in NetworkErrorReason:
        if re.search(reason.value, content):
            entry.fail_with_prefix(
                NetworkState.NETWORK_ERROR.value.format(url=work.url, error=reason.name.title()))
            return NetworkState.NETWORK_ERROR

    if check_state := work.check_state:
        if check_state[1] != SignState.NO_SIGN_IN:
            logger.warning(f'no sign in, regex: {succeed_regex}, content: {content}')

    return SignState.NO_SIGN_IN


def check_final_state(entry, work: Work, response: Response, content: str) -> SignState:
    sign_in_state: SignState = check_sign_in_state(entry, work, response, content)
    if sign_in_state == SignState.NO_SIGN_IN:
        entry.fail_with_prefix(SignState.SIGN_IN_FAILED.value.format('no sign in'))
        return SignState.SIGN_IN_FAILED
    return sign_in_state
