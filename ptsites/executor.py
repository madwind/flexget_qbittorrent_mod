from __future__ import annotations

import importlib
import pathlib
import pkgutil

from flexget import plugin
from flexget.entry import Entry
from loguru import logger

from .base.detail import Detail
from .base.entry import SignInEntry
from .base.message import Message
from .base.reseed import Reseed
from .base.sign_in import SignIn


def build_sign_in_schema() -> dict:
    module = None
    sites_schema: dict = {}
    try:
        for module in pkgutil.iter_modules(path=[f'{pathlib.PurePath(__file__).parent}/sites']):
            site_class = get_site_class(module.name)
            if issubclass(site_class, SignIn):
                sites_schema.update(site_class.sign_in_build_schema())
    except AttributeError as e:
        raise plugin.PluginError(f"site: {module.name}, error: {e}")
    return sites_schema


def build_sign_in_entry(entry: SignInEntry, config: dict) -> None:
    try:
        site_class = get_site_class(entry['class_name'])
        if issubclass(site_class, SignIn):
            site_class.sign_in_build_entry(entry, config)
    except AttributeError as e:
        raise plugin.PluginError(f"site: {entry['site_name']}, error: {e}")


def sign_in(entry: SignInEntry, config: dict) -> None:
    try:
        site_class = get_site_class(entry['class_name'])
    except AttributeError as e:
        raise plugin.PluginError(f"site: {entry['class_name']}, error: {e}")

    site_object = site_class()

    if issubclass(site_class, SignIn):
        entry['prefix'] = 'Sign_in'
        site_object.sign_in(entry, config)
        if entry.failed:
            return
        if entry['result']:
            logger.info(f"{entry['title']} {entry['result']}".strip())

    if config.get('get_messages', True) and issubclass(site_class, Message):
        entry['prefix'] = 'Messages'
        site_object.get_messages(entry, config)
        if entry.failed:
            return
        if entry['messages']:
            logger.info(f"site_name: {entry['site_name']}, messages: {entry['messages']}")

    if config.get('get_details', True) and issubclass(site_class, Detail):
        entry['prefix'] = 'Details'
        site_object.get_details(entry, config)
        if entry.failed:
            return
        if entry['details']:
            logger.info(f"site_name: {entry['site_name']}, details: {entry['details']}")
    clean_entry_attr(entry)


def clean_entry_attr(entry: SignInEntry) -> None:
    for attr in ['base_content', 'prefix']:
        if hasattr(entry, attr):
            del entry[attr]


def build_reseed_schema() -> dict:
    module = None
    sites_schema: dict = {}
    try:
        for module in pkgutil.iter_modules(path=[f'{pathlib.PurePath(__file__).parent}/sites']):
            site_class = get_site_class(module.name)
            if issubclass(site_class, Reseed):
                sites_schema.update(site_class.reseed_build_schema())
    except AttributeError as e:
        raise plugin.PluginError(f"site: {module.name}, error: {e}")
    return sites_schema


def build_reseed_entry(entry: Entry, config: dict, site: dict, passkey: str | dict, torrent_id: str) -> None:
    try:
        site_class = get_site_class(entry['class_name'])
        if issubclass(site_class, Reseed):
            site_class.reseed_build_entry(entry, config, site, passkey, torrent_id)
    except AttributeError as e:
        raise plugin.PluginError(f"site: {entry['site_name']}, error: {e}")


def get_site_class(class_name: str) -> type:
    site_module = importlib.import_module(f'flexget.plugins.ptsites.sites.{class_name.lower()}')
    return getattr(site_module, 'MainClass')
