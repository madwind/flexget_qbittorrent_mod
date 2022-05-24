from typing import Optional
from urllib.parse import urljoin

from requests import Response

from .base import Work
from .site_base import SiteBase
from ..utils import net_utils
from ..utils.state_checkers import check_state


def sign_in(site: SiteBase, entry, config: dict) -> None:
    workflow: list[Work] = []
    if not entry.get('cookie'):
        workflow.extend(site.build_login_workflow(entry, config))
    workflow.extend(site.build_workflow(entry, config))
    if not entry.get('url') or not workflow:
        entry.fail_with_prefix(f"site: {entry['site_name']} url or workflow is empty")
        return
    last_content: Optional[str] = None
    last_response: Optional[Response] = None
    for work in workflow:
        work.url = urljoin(entry['url'], work.url)
        work.response_urls = list(map(lambda response_url: urljoin(entry['url'], response_url), work.response_urls))
        method_name = f"sign_in_by_{work.method}"
        if method := getattr(site, method_name, None):
            if work.method == 'get' and last_response and net_utils.url_equal(
                    work.url, last_response.url) and work.is_base_content:
                entry['base_content'] = last_content
            else:
                last_response: Response = method(entry, config, work, last_content)
                if last_response == 'skip':
                    continue
                if (last_content := net_utils.decode(last_response)) and work.is_base_content:
                    entry['base_content'] = last_content
            if work.check_state and not check_state(entry, work, last_response, last_content):
                return
