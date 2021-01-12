from ..schema.meantorrent import MeanTorrent
from ..schema.site_base import SignState, Work, NetworkState
from ..utils.net_utils import NetUtils


# auto_sign_in
# site_config
# login:
#    usernameOrEmail: 'xxxxx'
#    password: 'xxxxxxxx'


class MainClass(MeanTorrent):
    URL = 'https://hdpost.top/'

    @classmethod
    def build_workflow(cls):
        return [
            Work(
                url='/api/auth/signin',
                method='login',
                check_state=('network', NetworkState.SUCCEED)
            ),
            Work(
                url='/api/check',
                method='get',
                succeed_regex='"keepDays":\\d+|YOU_ALREADY_CHECK_IN',
                check_state=('final', SignState.SUCCEED),
                is_base_content=True
            )
        ]

    def sign_in_by_login(self, entry, config, work, last_content=None):
        login = entry['site_config'].get('login')
        if not login:
            entry.fail_with_prefix('Login data not found!')
            return
        return self._request(entry, 'post', work.url, data=login)
        # if login_response and login_response.status_code == 200:
        #     entry['base_response'] = base_response = self._request(entry, 'put', URL)
        #     self.final_check(entry, base_response, URL)
        # else:
        #     entry.fail_with_prefix('Login failed.')

    def build_selector(self):
        selector = super(MainClass, self).build_selector()
        NetUtils.dict_merge(selector, {
            'details': {
                'hr': None
            }
        })
        return selector
