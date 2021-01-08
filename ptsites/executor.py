from flexget import plugin
from flexget.entry import Entry
from loguru import logger

from . import sites
from .schema.site_base import SiteBase


def fail_with_prefix(self, reason):
    self.fail('{}=> {}'.format(self.get('prefix'), reason))


Entry.fail_with_prefix = fail_with_prefix


class Executor:

    @staticmethod
    def build_sign_in(entry, config):
        try:
            site_class = Executor.get_site_class(entry['class_name'])
            site_class.build_sign_in(entry, config)
        except AttributeError as e:
            raise plugin.PluginError('site: {}, error: {}'.format(entry['site_name'], str(e.args)))

    @staticmethod
    def sign_in(entry, config):
        try:
            site_class = Executor.get_site_class(entry['class_name'])
        except AttributeError as e:
            raise plugin.PluginError('site: {}, error: {}'.format(entry['class_name'], str(e.args)))

        site_object = site_class()
        entry['prefix'] = 'Sign_in'
        site_object.sign_in(entry, config)
        if entry.failed:
            return
        if entry['result']:
            logger.info('{} {}'.format(entry['title'], entry['result']).strip())

        if config.get('get_messages', True):
            entry['prefix'] = 'Messages'
            site_object.get_message(entry, config)
            if entry.failed:
                return
            if entry['messages']:
                logger.info('site_name: {}, messages: {}', entry['site_name'], entry['messages'])

        if config.get('get_details', True):
            entry['prefix'] = 'Details'
            site_object.get_details(entry, config)
            if entry.failed:
                return
            if entry['details']:
                logger.info('site_name: {}, details: {}', entry['site_name'], entry['details'])

    @staticmethod
    def build_reseed(entry, site, passkey, torrent_id):
        try:
            site_class = Executor.get_site_class(entry['class_name'])
            site_class.build_reseed(entry, site, passkey, torrent_id)
        except AttributeError:
            SiteBase.build_reseed(entry, site, passkey, torrent_id)

    @staticmethod
    def get_site_class(class_name):
        site_module = getattr(sites, class_name.lower())
        site_class = getattr(site_module, 'MainClass')
        return site_class
