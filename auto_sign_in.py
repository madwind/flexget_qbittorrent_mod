from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED
from datetime import datetime

from flexget import plugin
from flexget.entry import Entry
from flexget.event import event

from .ptsites.executor import Executor


class PluginAutoSignIn:
    schema = {
        'type': 'object',
        'properties': {
            'user-agent': {'type': 'string'},
            'command_executor': {'type': 'string'},
            'max_workers': {'type': 'integer'},
            'aipocr': {
                'type': 'object',
                'properties': {
                    'app_id': {'type': 'string'},
                    'api_key': {'type': 'string'},
                    'secret_key': {'type': 'string'}
                },
                'additionalProperties': False
            },
            'sites': {
                'type': 'object',
                'properties': {
                }
            }
        },
        'additionalProperties': False
    }

    def prepare_config(self, config):
        config.setdefault('user-agent', '')
        config.setdefault('command_executor', '')
        config.setdefault('max_workers', {})
        config.setdefault('aipocr', {})
        config.setdefault('sites', {})
        return config

    def on_task_input(self, task, config):
        config = self.prepare_config(config)
        sites = config.get('sites')

        entries = []

        for site_name, site_config in sites.items():
            entry = Entry(
                title='{} {}'.format(site_name, datetime.now().date()),
            )
            entry['site_config'] = site_config
            Executor.execute_build_sign_in_entry(entry, site_name, config)
            entries.append(entry)
        return entries

    def on_task_output(self, task, config):
        max_workers = config.get('max_workers', 1)
        with ThreadPoolExecutor(max_workers=max_workers) as t:
            all_task = [t.submit(Executor().execute_sign_in, entry, config) for entry in task.accepted]
            wait(all_task, return_when=ALL_COMPLETED)


@event('plugin.register')
def register_plugin():
    plugin.register(PluginAutoSignIn, 'auto_sign_in', api_ver=2)
