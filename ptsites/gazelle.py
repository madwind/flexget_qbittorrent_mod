from flexget import plugin

from .site_base import SiteBase


class Gazelle(SiteBase):
    @staticmethod
    def build_sign_in_entry(entry, site_name, config, url, succeed_regex, base_url=None,
                            wrong_regex=None):
        site_config = entry['site_config']
        if not isinstance(site_config, str):
            raise plugin.PluginError('{} site_config is not a String'.format(site_name))
        entry['url'] = url
        entry['succeed_regex'] = succeed_regex
        if base_url:
            entry['base_url'] = base_url
        if wrong_regex:
            entry['wrong_regex'] = wrong_regex
        headers = {
            'cookie': site_config,
            'user-agent': config.get('user-agent'),
            'referer': base_url if base_url else url
        }
        entry['headers'] = headers

    def sign_in(self, entry, config):
        self.sign_in_by_get(entry, config)

    def get_message(self, entry, config):
        self.get_gazelle_message(entry, config)
