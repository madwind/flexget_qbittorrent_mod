import re
from typing import Optional, Union
from urllib.parse import urljoin

from flexget.utils.soup import get_soup
from loguru import logger

from .base import NetworkState
from ..utils import net_utils
from ..utils.state_checkers import check_network_state


def get_user_id(entry, user_id_selector: str, base_content: str) -> Optional[str]:
    if isinstance(user_id_selector, str):
        if user_id_match := re.search(user_id_selector, base_content):
            return user_id_match.group(1)
        else:
            entry.fail_with_prefix('User id not found.')
            logger.error(f'site: {entry["site_name"]} User id not found. content: {base_content}')
    else:
        entry.fail_with_prefix('user_id_selector is not str.')
        logger.error(f'site: {entry["site_name"]} user_id_selector is not str.')


def get_detail_value(content: str, detail_config: dict) -> Optional[str]:
    if detail_config is None:
        return '*'
    regex: Union[str, tuple] = detail_config['regex']
    group_index = 1
    if isinstance(regex, tuple):
        regex, group_index = regex
    if not (detail_match := re.search(regex, content, re.DOTALL)):
        return None
    if not (detail := detail_match.group(group_index)):
        return None
    detail = detail.replace(',', '')
    if handle := detail_config.get('handle'):
        detail = handle(detail)
    return str(detail)


def get_details_base(site, entry, config: str, selector: dict) -> None:
    if not (base_content := entry.get('base_content')):
        entry.fail_with_prefix('base_content is None.')
        return
    user_id = ''
    if (user_id_selector := selector.get('user_id')) and not (
            user_id := get_user_id(entry, user_id_selector, base_content)):
        return
    details_text = ''
    for detail_source in selector.get('detail_sources').values():
        if detail_source.get('link'):
            detail_source['link'] = urljoin(entry['url'], detail_source['link'].format(user_id))
            detail_response = site.request(entry, 'get', detail_source['link'])
            network_state = check_network_state(entry, detail_source['link'], detail_response)
            if network_state != NetworkState.SUCCEED:
                return
            detail_content = net_utils.decode(detail_response)
        else:
            detail_content = base_content
        if elements := detail_source.get('elements'):
            soup = get_soup(detail_content)
            for name, sel in elements.items():
                if sel:
                    if details_info := soup.select_one(sel):
                        details_text += str(details_info) if detail_source.get('do_not_strip') else details_info.text
                    else:
                        entry.fail_with_prefix(f'Element: {name} not found.')
                        logger.error('site: {} element: {} not found, selector: {}, soup: {}',
                                     entry['site_name'],
                                     name, sel, soup)
                        return
        else:
            details_text += detail_content
    if not details_text:
        entry.fail_with_prefix('details_text is None.')
        return
    logger.debug(details_text)
    details = {}
    for detail_name, detail_config in selector['details'].items():
        if not (detail_value := get_detail_value(details_text, detail_config)):
            entry.fail_with_prefix(f'detail: {detail_name} not found.')
            logger.error(
                f"Details=> site: {entry['site_name']}, regex: {detail_config['regex']}，details_text: {details_text}")
            return
        details[detail_name] = detail_value
    entry['details'] = details
