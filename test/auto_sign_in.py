import importlib
from datetime import datetime

from flexget.entry import Entry


def fail_with_prefix(self, reason):
    self.fail('{}=> {}'.format(self.get('prefix'), reason))


Entry.fail_with_prefix = fail_with_prefix

site_name = 'jptv'
entry = Entry(
    title='{} {}'.format(site_name, datetime.now().date()),
    url=''
)
entry['site_name'] = site_name

entry['result'] = ''
entry['messages'] = ''
entry['detail'] = ''
entry[
    'site_config'] = 'xxxxxxxx'
# entry['site_config'] = {
#     'username': 'xxxx',
#     'cookie': 'xxxxxx',
#     'comment': 'xxxxxxx',
# }
# entry['site_config'] = {
#     'login': {
#         'username': 'xxxxxx',
#         'password': 'xxxxxx'
#     }
# }

config = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36',
    'aipocr': {
        'app_id': 'xxxxxx',
        'api_key': 'xxxxxx',
        'secret_key': 'xxxxxx'
    }
}
# }
site_module = importlib.import_module('ptsites.sites.{}'.format(site_name))
site_class = getattr(site_module, 'MainClass')
site_class.build_sign_in(entry, config)
s = site_class()
entry['prefix'] = 'sign_in'
print(entry['prefix'])
s.sign_in(entry, config)
print(entry['result'])
if not entry.failed and False:
    entry['prefix'] = 'message'
    print(entry['prefix'])
    s.get_message(entry, config)
    print(entry['messages'])
    entry['prefix'] = 'details'
    print(entry['prefix'])
    s.get_details(entry, config)
    print(entry['detail'])
print(entry['result'])
