from flexget import plugin
from flexget.event import event
from flexget.task import Task
from loguru import logger


class PluginHtmlRss:
    schema = {
        'type': 'object',
        'properties': {
            'state': {'type': 'string'},
            'attribute': {'oneOf': [{'type': 'boolean'}, {'type': 'array', 'items': {'type': 'string'}}]}
        }
    }

    @plugin.priority(plugin.PRIORITY_LAST)
    def on_task_output(self, task: Task, config: dict) -> None:
        state = config.get('state')
        attribute = config.get('attribute')
        entries = getattr(task, state)
        for entry in entries:
            for key, value in entry.items():
                if isinstance(attribute, list) and key not in attribute:
                    continue
                logger.info('key: {}, value: {}', key, value)


@event('plugin.register')
def register_plugin():
    plugin.register(PluginHtmlRss, 'show_entry', api_ver=2)
