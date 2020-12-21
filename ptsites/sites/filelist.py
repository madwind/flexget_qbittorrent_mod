from ..schema.ocelot import Ocelot
from ..schema.site_base import Work, SignState


class MainClass(Ocelot):
    URL = 'https://filelist.io/'
    USER_CLASSES = {
        'downloaded': [45079976738816],
        'share_ratio': [5],
        'days': [1460]
    }

    @classmethod
    def build_workflow(cls):
        return [
            Work(
                url='/',
                method='get',
                succeed_regex='Hello, <a .+?</a>',
                fail_regex=None,
                check_state=('final', SignState.SUCCEED),
                is_base_content=True
            )
        ]

    def build_selector(self):
        selector = super(MainClass, self).build_selector()
        return selector
