from ..schema.site_base import SignState, Work
from ..schema.unit3d import Unit3D


class MainClass(Unit3D):
    URL = 'https://aither.cc/'
    USER_CLASSES = {
        'uploaded': [43980465111040],
        'days': [365]
    }

    def build_workflow(self, entry, config):
        return [
            Work(
                url='/',
                method='get',
                succeed_regex='<title>Aither - Heaven</title>',
                fail_regex=None,
                check_state=('final', SignState.SUCCEED),
                is_base_content=True
            )
        ]

    def build_selector(self):
        selector = super(MainClass, self).build_selector()
        return selector
