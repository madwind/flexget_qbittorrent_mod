import importlib
import pathlib
import pkgutil

from flexget import plugin
from flexget.entry import Entry
from loguru import logger

from .base.sign_in import sign_in
from .base.site_base import SiteBase


def fail_with_prefix(self, reason: str) -> None:
    self.fail(f"{self.get('prefix')}=> {reason}")


Entry.fail_with_prefix = fail_with_prefix


def build_sign_in_schema() -> dict:
    module = None
    sites_schema: dict = {}
    try:
        for module in pkgutil.iter_modules(path=[f'{pathlib.PurePath(__file__).parent}/sites']):
            site_class = get_site_class(module.name)
            sites_schema.update(site_class.build_sign_in_schema())
    except AttributeError as e:
        raise plugin.PluginError(f"site: {module.name}, error: {e}")
    return sites_schema


def build_reseed_schema() -> dict:
    module = None
    sites_schema: dict = {}
    try:
        for module in pkgutil.iter_modules(path=[f'{pathlib.PurePath(__file__).parent}/sites']):
            site_class = get_site_class(module.name)
            sites_schema.update(site_class.build_reseed_schema())
    except AttributeError as e:
        raise plugin.PluginError(f"site: {module.name}, error: {e}")
    return sites_schema


def build_sign_in_entry(entry: Entry, config: dict) -> None:
    try:
        site_class = get_site_class(entry['class_name'])
        site_class.build_sign_in_entry(entry, config)
    except AttributeError as e:
        raise plugin.PluginError(f"site: {entry['site_name']}, error: {e}")


def process_sites(entry: Entry, config: dict) -> None:
    try:
        site_class = get_site_class(entry['class_name'])
    except AttributeError as e:
        raise plugin.PluginError(f"site: {entry['class_name']}, error: {e}")

    site_object = site_class()
    entry['prefix'] = 'Sign_in'
    sign_in(site_object, entry, config)
    if entry.failed:
        return
    if entry['result']:
        logger.info(f"{entry['title']} {entry['result']}".strip())

    if config.get('get_messages', True):
        entry['prefix'] = 'Messages'
        site_object.get_message(entry, config)
        if entry.failed:
            return
        if entry['messages']:
            logger.info(f"site_name: {entry['site_name']}, messages: {entry['messages']}")

    if config.get('get_details', True):
        entry['prefix'] = 'Details'
        site_object.get_details(entry, config)
        if entry.failed:
            return
        if entry['details']:
            logger.info(f"site_name: {entry['site_name']}, details: {entry['details']}")
    clean_entry_attr(entry)


def clean_entry_attr(entry: Entry) -> None:
    for attr in ['base_content', 'prefix']:
        if hasattr(entry, attr):
            del entry[attr]


def build_reseed_entry(entry: Entry, config: dict, site, passkey, torrent_id) -> None:
    try:
        site_class = get_site_class(entry['class_name'])
        site_class.build_reseed_entry(entry, config, site, passkey, torrent_id)
    except AttributeError:
        SiteBase.build_reseed_entry(entry, config, site, passkey, torrent_id)


def get_site_class(class_name: str):
    site_module = importlib.import_module(f'flexget.plugins.ptsites.sites.{class_name.lower()}')
    site_class = getattr(site_module, 'MainClass')
    return site_class
