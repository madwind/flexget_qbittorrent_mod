from ..executor import Executor, SignState

# auto_sign_in
BASE_URL = 'https://www.haidan.video/index.php'
URL = 'https://www.haidan.video/signin.php'
SUCCEED_REGEX = '(?<=value=")已经打卡(?=")'


class MainClass(Executor):
    @staticmethod
    def build_sign_in_entry(entry, site_name, config):
        Executor.build_sign_in_entry_common(entry, site_name, config, URL, SUCCEED_REGEX, base_url=BASE_URL)

    def check_net_state(self, entry, response, original_url, is_message=False):
        if not response:
            if not is_message:
                if not entry['result'] and not is_message:
                    entry['result'] = SignState.NETWORK_ERROR.value.format('Response is None')
                entry.fail(entry['result'])
            return SignState.NETWORK_ERROR

        if response.url not in [BASE_URL, URL, original_url]:
            if not is_message:
                entry['result'] = SignState.URL_REDIRECT.value.format(original_url, response.url)
                entry.fail(entry['result'])
            return SignState.URL_REDIRECT
