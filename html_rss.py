from urllib.parse import urljoin

from flexget import plugin
from flexget.entry import Entry
from flexget.event import event
from flexget.task import Task
from flexget.utils.soup import get_soup
from loguru import logger
from requests import RequestException

from .ptsites.utils import net_utils


class PluginHtmlRss:
    schema = {
        'type': 'object',
        'properties': {
            'url': {'type': 'string', 'format': 'url'},
            'user-agent': {'type': 'string'},
            'cookie': {'type': 'string'},
            'params': {'type': 'string'},
            "root_element_selector": {'type': 'string'},
            'fields': {
                'type': 'object',
                'properties': {
                    'title': {
                        'type': 'object',
                        'properties': {
                            'element_selector': {'type': 'string'},
                            'attribute': {'type': 'string'},
                        }
                    },
                    'url': {
                        'type': 'object',
                        'properties': {
                            'element_selector': {'type': 'string'},
                            'attribute': {'type': 'string'},
                        },
                    }
                },
                'required': ['title', 'url'],
            }
        },
        'required': ['url', 'root_element_selector'],
        'additionalProperties': False
    }

    def prepare_config(self, config: dict) -> dict:
        config.setdefault('url', '')
        config.setdefault('user-agent', '')
        config.setdefault('cookie', '')
        config.setdefault('params', '')
        config.setdefault('root_element_selector', '')
        config.setdefault('fields', {})
        return config

    def on_task_input(self, task: Task, config: dict) -> list[Entry]:
        config = self.prepare_config(config)
        url = config.get('url')
        user_agent = config.get('user-agent')
        cookie = config.get('cookie')
        root_element_selector = config.get('root_element_selector')
        fields = config.get('fields')
        params = config.get('params')
        headers = {
            'accept-encoding': 'gzip, deflate, br',
            'user-agent': user_agent
        }

        entries = []

        try:
            task.requests.headers.update(headers)
            task.requests.cookies.update(net_utils.cookie_str_to_dict(cookie))
            response = task.requests.get(url, timeout=60)
            content = net_utils.decode(response)
        except RequestException as e:
            raise plugin.PluginError(
                'Unable to download the Html for task {} ({}): {}'.format(task.name, url, e)
            )
        elements = get_soup(content).select(root_element_selector)
        if len(elements) == 0:
            logger.debug(f'no elements found in response: {content}')
            return entries

        for element in elements:
            logger.debug('element in element_selector: {}', element)
            entry = Entry()
            for key, value in fields.items():
                entry[key] = ''
                sub_element = element.select_one(value['element_selector'])
                if sub_element:
                    if value['attribute'] == 'textContent':
                        sub_element_content = sub_element.get_text()
                    else:
                        sub_element_content = sub_element.get(value['attribute'], '')
                    entry[key] = sub_element_content
                logger.debug('key: {}, value: {}', key, entry[key])
            if entry['title'] and entry['url']:
                base_url = urljoin(url, entry['url'])
                if params.startswith("&"):
                    entry['url'] = base_url + params
                else:
                    entry['url'] = urljoin(base_url, params)
                entry['original_url'] = entry['url']
                entries.append(entry)
        return entries


@event('plugin.register')
def register_plugin():
    plugin.register(PluginHtmlRss, 'html_rss', api_ver=2)
