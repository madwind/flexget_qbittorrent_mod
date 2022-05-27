from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from flexget import plugin
from flexget.event import event
from flexget.task import Task
from loguru import logger

from .ptsites import executor
from .ptsites.base.entry import SignInEntry
from .ptsites.utils.details_report import DetailsReport


class PluginAutoSignIn:
    schema: dict = {
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
                'properties': executor.build_sign_in_schema()
            }
        },
        'additionalProperties': False
    }

    def prepare_config(self, config: dict) -> dict:
        config.setdefault('user-agent', '')
        config.setdefault('command_executor', '')
        config.setdefault('max_workers', {})
        config.setdefault('aipocr', {})
        config.setdefault('sites', {})
        return config

    def on_task_input(self, task: Task, config: dict) -> list[SignInEntry]:
        config = self.prepare_config(config)
        sites: dict = config['sites']

        entries: list[SignInEntry] = []

        for site_name, site_configs in sites.items():
            if not isinstance(site_configs, list):
                site_configs = [site_configs]
            for sub_site_config in site_configs:
                entry = SignInEntry(
                    title=f'{site_name} {datetime.now().date()}',
                    url=''
                )
                entry['site_name'] = site_name
                entry['class_name'] = site_name
                entry['site_config'] = sub_site_config
                entry['result'] = ''
                entry['messages'] = ''
                entry['details'] = ''
                executor.build_sign_in_entry(entry, config)
                entries.append(entry)
        return entries

    def on_task_output(self, task: Task, config: dict) -> None:
        max_workers: int = config.get('max_workers', 1)
        date_now: str = str(datetime.now().date())
        for entry in task.all_entries:
            if date_now not in entry['title']:
                entry.reject(f'{entry["title"]} out of date!')
        with ThreadPoolExecutor(max_workers=max_workers) as thread_executor:
            for entry, feature in [(entry, thread_executor.submit(executor.sign_in, entry, config))
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
