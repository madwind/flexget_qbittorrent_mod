from ..nexusphp import NexusPHP

# auto_sign_in
URL = 'https://hdhome.org/attendance.php'
SUCCEED_REGEX = '这是您的第 .* 次签到，已连续签到 .* 天，本次签到获得 .* 个魔力值。|您今天已经签到过了，请勿重复刷新。'

# html_rss
ROOT_ELEMENT_SELECTOR = '#torrenttable > tbody > tr:not(:first-child)'
FIELDS = {
    'title': {
        'element_selector': 'a[href*="details.php"]',
        'attribute': 'title'
    },
    'url': {
        'element_selector': 'a[href*="download.php"]',
        'attribute': 'href'
    },
    'leecher': {
        'element_selector': 'td:nth-child(7)',
        'attribute': 'textContent'
    },
    'hr': {
        'element_selector': 'img.hitandrun',
        'attribute': 'alt'
    }
}


class MainClass(NexusPHP):
    @staticmethod
    def build_sign_in_entry(entry, site_name, config):
        NexusPHP.build_sign_in_entry(entry, site_name, config, URL, SUCCEED_REGEX)

    @staticmethod
    def build_html_rss_config(config):
        config['root_element_selector'] = ROOT_ELEMENT_SELECTOR
        config['fields'] = FIELDS
