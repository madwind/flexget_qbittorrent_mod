from flexget import plugin

from ptsites.executor import Executor

# auto_sign_in
URL = 'https://discfan.net/attendance.php'
SUCCEED_REGEX = '這是您的第 \\d+ 次簽到，已連續簽到 \\d+ 天，本次簽到獲得 \\d+ 個魔力值。|您今天已經簽到過了，請勿重複刷新。'


class MainClass(Executor):
    @staticmethod
    def build_sign_in_entry(entry, site_name, config):
        site_config = entry['site_config']
        if not isinstance(site_config, str):
            raise plugin.PluginError('{} site_config is not a String'.format(site_name))
        entry['url'] = URL
        entry['succeed_regex'] = SUCCEED_REGEX
        headers = {
            'cookie': site_config,
            'user-agent': config.get('user-agent'),
            'referer': URL
        }
        entry['headers'] = headers
