from urllib.parse import urljoin

from flexget import plugin
from flexget.entry import Entry
from flexget.event import event
from flexget.utils.soup import get_soup
from loguru import logger
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
        config.setdefault('root_element_selector', '')
        config.setdefault('fields', {})
        return config

    def on_task_input(self, task, config):
        config = self.prepare_config(config)
        url = config.get('url')
        root_element_selector = config.get('root_element_selector')
        fields = config.get('fields')
        passkey = config.get('passkey')

        queue = []
        elements = []
        if url and root_element_selector:
            try:
                response = task.requests.get(url, headers=config.get('headers'))
                content = response.content
            except RequestException as e:
                raise plugin.PluginError(
                    'Unable to download the Html for task {} ({}): {}'.format(task.name, url, e)
                )
            elements = get_soup(content).select(root_element_selector)
            if len(elements) == 0:
                return queue

        for element in elements:
            logger.debug('element in element_selector: {}', element)
            entry = Entry()
            for key, value in fields.items():
                entry[key] = ''
                sub_element = element.select(value['element_selector'])
                if len(sub_element) > 0:
                    entry[key] = sub_element[0].get(value['attribute'], '')
                logger.debug('key: {}, value: {}', key, entry[key])
            if entry['title'] and entry['url']:
                entry['url'] = urljoin(url, '{}&passkey={}'.format(entry['url'], passkey))
                queue.append(entry)
        return queue


@event('plugin.register')
def register_plugin():
    plugin.register(PluginHtmlRss, 'html_rss', api_ver=2)
