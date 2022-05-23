from ..schema.nexusphp import Visit
from ..schema.site_base import SignState, Work


class MainClass(Visit):
    URL = 'https://byr.pt/'
    USER_CLASSES = {
        'uploaded': [4398046511104, 140737488355328],
        'share_ratio': [3.05, 4.55],
        'days': [168, 336]
    }

    def build_workflow(self, entry, config):
        return [
            Work(
                url='/index.php',
                method='get',
                succeed_regex=['欢迎'],
                check_state=('final', SignState.SUCCEED),
                is_base_content=True
            )
        ]
