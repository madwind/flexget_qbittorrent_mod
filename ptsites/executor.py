from flexget import plugin
from loguru import logger

from . import sites
from .site_base import SiteBase


class Executor:

    @staticmethod
    def build_sign_in_entry(entry, site_name, config):
        site_config = entry['site_config']
        if isinstance(site_config, str) or not site_config.get('url'):
            try:
                site_module = getattr(sites, site_name.lower())
                site_class = getattr(site_module, 'MainClass')
                site_class.build_sign_in_entry(entry, site_name, config)
                entry['site_class'] = site_class
            except AttributeError as e:
                raise plugin.PluginError(str(e.args))
        else:
            SiteBase.build_sign_in_entry(entry, site_name, config)
            entry['site_class'] = SiteBase
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

        site_class = entry.get('site_class')
        site_object = site_class()
        site_object.sign_in(entry, config)
        if not entry.failed:
            site_object.get_message(entry, config)
        logger.info('{} {}\n{}'.format(entry['title'], entry['result'], entry['messages']).strip())
