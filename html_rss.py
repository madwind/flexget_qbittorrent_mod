from urllib.parse import urljoin

from bs4 import BeautifulSoup
from flexget import plugin
from flexget.entry import Entry
from flexget.event import event
from flexget.utils.soup import get_soup
from requests import RequestException


class PluginHtmlRss():
    schema = {
        'anyOf': [
            {'type': 'boolean'},
            {
                'type': 'object',
                'properties': {
                    'url': {'type': 'string', 'format': 'url'},
                    'headers': {
                        'type': 'object',
                        'properties': {
                            'cookies': {'type': 'string'},
                            'agent': {'type': 'string'},
                        }
                    },
                    'passkey': {'type': 'string'},
                    "element_selector": {'type': 'string'},
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
                        }
                    }
                },
                'required': ['url'],
                'additionalProperties': False
            }
        ]
    }

    def prepare_config(self, config):
        config.setdefault('url', '')
        config.setdefault('headers', {})
        config.setdefault('passkey', '')
        config.setdefault('element_selector', '')
        config.setdefault('fields', {})
        return config

    def on_task_input(self, task, config):
        config = self.prepare_config(config)
        url = config.get('url')
        element_selector = config.get('element_selector')

        queue = []
        if url and element_selector:
            try:
                response = task.requests.get(url, headers=config.get('headers'))
                content = response.content
            except RequestException as e:
                raise plugin.PluginError(
                    'Unable to download the Html for task {} ({}): {}'.format(task.name, config['page'], e)
                )
            elements = get_soup(content).select(element_selector)
            if len(elements) == 0:
                return queue
        fields = config.get('keys')

        for element in elements:
            entry = Entry()
            for key, value in fields.items():
                entry[key] = element.select(value['element_selector'])[0].attrs[value['attribute']]
            entry['url'] = urljoin(url, '{}&passkey={}'.format(entry['url'], config.get('passkey')))
            queue.append(entry)
        return queue


@event('plugin.register')
def register_plugin():
    plugin.register(PluginHtmlRss, 'html_rss', api_ver=2)
