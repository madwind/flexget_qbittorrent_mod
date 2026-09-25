from __future__ import annotations

from PIL import Image

from ptsites.base.entry import SignInEntry
from ptsites.utils import baidu_ocr


def test_japanese_ocr_preserves_latin_and_cjk_text(monkeypatch) -> None:
    class SuccessfulClient:
        def basicAccurate(self, *args, **kwargs):
            return {
                'words_result': [
                    {'words': 'TIME BOKAN'},
                    {'words': 'タイムボカン'},
                ]
            }

    monkeypatch.setattr(baidu_ocr, 'get_client', lambda *args: SuccessfulClient())
    entry = SignInEntry()

    assert baidu_ocr.get_jap_ocr(Image.new('RGB', (10, 10)), entry, {}) == 'TIME BOKAN タイムボカン'
