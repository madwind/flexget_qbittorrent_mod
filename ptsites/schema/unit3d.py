import itertools
import json
from pathlib import Path
from urllib.parse import urljoin

from flexget.utils.soup import get_soup
from loguru import logger

from .site_base import SiteBase, SignState


class Unit3D(SiteBase):

    def sign_in(self, entry, config):
        self.sign_in_by_get(entry, config)

    def get_message(self, entry, config):
        self.get_unit3d_message(entry, config)

    def get_details(self, entry, config):
        self.get_details_base(entry, config, self.build_selector())

    def build_selector(self):
        selector = {
            'detail_sources': {
                'default': {
                    'elements': {
                        'bar': '#main-content > div.ratio-bar > div > ul',
                    }
                }
            },
            'details': {
                'uploaded': {
                    'regex': '上传.+?([\\d.]+ ?[ZEPTGMK]?iB)'
                },
                'downloaded': {
                    'regex': '下载.+?([\\d.]+ ?[ZEPTGMK]?iB)'
                },
                'share_ratio': {
                    'regex': '分享率.+?([\\d.]+)'
                },
                'points': {
                    'regex': '魔力.+?([\\d,.]+)'
                },
                'seeding': {
                    'regex': '做种.+?(\\d+)'
                },
                'leeching': {
                    'regex': '吸血.+?(\\d+)'
                },
                'hr': {
                    'regex': '警告.+?(\\d+)'
                }
            }
        }
        return selector

    def get_unit3d_message(self, entry, config, messages_url='/messages.php'):
        pass