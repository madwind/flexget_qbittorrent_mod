from ..base.sign_in import check_final_state, SignState, Work
from ..schema.unit3d import Unit3D


class MainClass(Unit3D):
    URL = 'https://jptv.club/'
    USER_CLASSES = {
        'uploaded': [109951162777600],
        'days': [365]
    }

    def sign_in_build_workflow(self, entry, config):
        return [
            Work(
                url='/',
                method=self.sign_in_by_get,
                succeed_regex=['<title>JPTV\\.club - JPTV for everyone!</title>'],
                assert_state=(check_final_state, SignState.SUCCEED),
                is_base_content=True
            )
        ]

    @property
    def details_selector(self) -> dict:
        selector = super().details_selector
        return selector
