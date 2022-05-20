from ..schema.site_base import SiteBase, Work, SignState


class MainClass(SiteBase):
    URL = 'https://theaudioscene.net/'

    def build_workflow(self, entry, config):
        return [
            Work(
                url='/',
                method='get',
                succeed_regex=r'Logout',
                check_state=('final', SignState.SUCCEED),
                is_base_content=True,
            ),
        ]

    def build_selector(self):
        return {
            'detail_sources': {
                'default': {
                    'elements': {
                        'stats': 'table > tbody > tr:nth-child(1) > td:nth-child(3) > div:nth-child(1)',
                    },
                },
            },
            'details': {
                'uploaded': {
                    'regex': r'''(?x)(?<= Uploaded: )
                                    ([\d.] +
                                    \ 
                                    [ZEPTGMK] B)'''
                },
                'downloaded': {
                    'regex': r'''(?x)(?<= Downloaded: )
                                    ([\d.] +
                                    \ 
                                    [ZEPTGMK] B)'''
                },
                'share_ratio': {
                    'regex': r'''(?x)(?<= Ratio: )
                                    ([\d,.] +)'''
                },
                'points': None,
                'seeding': {
                    'regex': r'''(?x)(?<= Uploading: )
                                    ([\d,] +)'''
                },
                'leeching': {
                    'regex': r'''(?x)(?<= Downloading: )
                                    ([\d,] +)'''
                },
                'hr': None,
            }
        }
