from flexget import plugin
from flexget.event import event
from loguru import logger


class PluginHtmlRss():
    schema = {
        'type': 'object',
        'properties': {
            'state': {'type': 'string'},
            'attribute': {'oneOf': [{'type': 'boolean'}, {'type': 'array', 'items': {'type': 'string'}}]}
        }
    }

    def on_task_output(self, task, config):
        state = config.get('state')
        if not config:
            return
        for entry in getattr(task, state):
            for key, value in entry.items():
                if isinstance(config, list) and key not in config:
                    continue
                logger.info('key: {}, value: {}', key, value)


@event('plugin.register')
def register_plugin():
    plugin.register(PluginHtmlRss, 'show_entry', api_ver=2)
