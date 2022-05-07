from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from flexget import plugin
from flexget.entry import Entry
from flexget.event import event
from loguru import logger

from .ptsites.executor import Executor
from .ptsites.utils.details_report import DetailsReport


class PluginAutoSignIn:
    schema = {
        'type': 'object',
        'properties': {
            'user-agent': {'type': 'string'},
            'max_workers': {'type': 'integer'},
            'get_messages': {'type': 'boolean', 'default': True},
            'get_details': {'type': 'boolean', 'default': True},
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
                'properties': Executor.build_sign_in_schema()
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

        for site_name, site_configs in sites.items():
            if not isinstance(site_configs, list):
                site_configs = [site_configs]
            for sub_site_config in site_configs:
                entry = Entry(
                    title='{} {}'.format(site_name, datetime.now().date()),
                    url=''
                )
                entry['site_name'] = site_name
                entry['class_name'] = site_name
                entry['site_config'] = sub_site_config
                entry['result'] = ''
                entry['messages'] = ''
                entry['details'] = ''
                Executor.build_sign_in_entry(entry, config)
                entries.append(entry)
        return entries

    def on_task_output(self, task, config):
        max_workers = config.get('max_workers', 1)
        date_now = str(datetime.now().date())
        for entry in task.all_entries:
            if date_now not in entry['title']:
                entry.reject('{} out of date!'.format(entry['title']))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for entry, feature in [(entry, executor.submit(Executor.sign_in, entry, config))
                                   for entry in task.accepted]:
                try:
                    feature.result()
                except Exception as e:
                    logger.exception(e)
                    entry.fail_with_prefix('Exception: ' + str(e))
        if config.get('get_details', True):
            DetailsReport().build(task)


@event('plugin.register')
def register_plugin():
    plugin.register(PluginAutoSignIn, 'auto_sign_in', api_ver=2)
