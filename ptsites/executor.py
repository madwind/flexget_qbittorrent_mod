from flexget import plugin
from loguru import logger

from . import sites
from .schema.site_base import SiteBase


class Executor:

    @staticmethod
    def build_sign_in_entry(entry, config):
        try:
            site_module = getattr(sites, entry['site_name'].lower())
            site_class = getattr(site_module, 'MainClass')
            site_class.build_sign_in(entry, config)
        except AttributeError as e:
            raise plugin.PluginError('site: {}, error: {}'.format(entry['site_name'], str(e.args)))
        entry['result'] = ''
        entry['messages'] = ''

    @staticmethod
    def build_reseed_entry(entry, base_url, site, site_name, passkey, torrent_id):
        try:
            site_module = getattr(sites, site_name.lower())
            site_class = getattr(site_module, 'MainClass')
            site_class.build_reseed_entry(entry, base_url, site, passkey, torrent_id)
        except AttributeError as e:
            SiteBase.build_reseed_entry(entry, base_url, site, passkey, torrent_id)

    @staticmethod
    def sign_in(entry, config):
        # command_executor = config.get('command_executor')
        # cf = entry['site_config'].get('cf')
        # if cf:
        #     if command_executor and webdriver:
        #         try:
        #             cookie = self.selenium_get_cookie(command_executor, entry['headers'])
        #         except Exception as e:
        #             entry['result'] = str(e)
        #             entry.fail(entry['result'])
        #             return
        #     else:
        #         entry['result'] = 'command_executor or webdriver not existed'
        #         entry.fail(entry['result'])
        #         return
        #     entry['headers']['cookie'] = cookie
        try:
            site_module = getattr(sites, entry['site_name'].lower())
            site_class = getattr(site_module, 'MainClass')
            site_object = site_class()
            entry['prefix'] = 'Sign_in'
            site_object.sign_in(entry, config)
            if not entry.failed:
                logger.info('{} {}\n{}'.format(entry['title'], entry['result'], entry['messages']).strip())
                entry['prefix'] = 'Details'
                site_object.get_details(entry, config)
                entry['prefix'] = 'Messages'
                site_object.get_message(entry, config)
        except AttributeError as e:
            raise plugin.PluginError('site: {}, error: {}'.format(entry['site_name'], str(e.args)))
