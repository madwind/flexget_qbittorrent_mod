from flexget import plugin

from ptsites.executor import Executor

# auto_sign_in
URL = 'https://52pt.site/bakatest.php'
SUCCEED_REGEX = '连续.*天签到,获得.*点魔力值|今天已经签过到了\(已连续.*天签到\)'
WRONG_REGEX = '回答错误,失去 1 魔力值,这道题还会再考一次'


class MainClass(Executor):
    @staticmethod
    def build_sign_in_entry(entry, site_name, config):
        site_config = entry['site_config']
        if not isinstance(site_config, str):
            raise plugin.PluginError('{} site_config is not a String'.format(site_name))
        entry['url'] = URL
        entry['succeed_regex'] = SUCCEED_REGEX
        entry['wrong_regex'] = WRONG_REGEX
        headers = {
            'cookie': site_config,
            'user-agent': config.get('user-agent'),
            'referer': URL
        }
        entry['headers'] = headers

    def do_sign_in(self, entry, config):
        self.sign_in_by_question(entry, config)
