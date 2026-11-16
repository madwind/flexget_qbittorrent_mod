from __future__ import annotations

from io import BytesIO

import pytest
from PIL import Image
from requests import Response

from ptsites.base.entry import SignInEntry
from ptsites.trackers import ptsbao


def test_workflow_uses_captcha_post() -> None:
    tracker = ptsbao.MainClass()
    entry = SignInEntry()

    workflow = tracker.sign_in_build_workflow(entry, {})

    assert [work.url for work in workflow] == ['/attendance.php', '/attendance.php']
    assert workflow[1].method == tracker.sign_in_by_ocr


@pytest.mark.parametrize('code', ['ABC123', None])
def test_ocr_uses_full_captcha_url_and_submits_only_a_valid_code(monkeypatch, code) -> None:
    tracker = ptsbao.MainClass()
    entry = SignInEntry()
    entry.update({'title': 'PTSBAO', 'url': tracker.URL, 'site_name': 'ptsbao', 'site_config': 'test-cookie'})
    work = tracker.sign_in_build_workflow(entry, {})[1]
    content = '''
        <form action="attendance.php" method="post">
            <img src="image.php?action=regimage&amp;imagehash=hash-token&amp;secret=secret-token" />
            <input type="hidden" name="imagehash" value="hash-token" />
        </form>
    '''
    requested = []
    buffer = BytesIO()
    Image.new('L', (2, 2)).save(buffer, format='PNG')

    def fake_request(entry_arg, method, url, **kwargs):
        requested.append((method, url, kwargs))
        response = Response()
        response.status_code = 200
        response.url = url
        response._content = buffer.getvalue()
        return response

    monkeypatch.setattr(tracker, 'request', fake_request)
    def recognize(image, *_):
        assert image.mode == 'RGB'
        return code, b''

    monkeypatch.setattr(ptsbao.baidu_ocr, 'get_ocr_code', recognize)

    response = tracker.sign_in_by_ocr(entry, {}, work, content)

    expected = [('get', tracker.URL + 'image.php?action=regimage&imagehash=hash-token&secret=secret-token', {})]
    if code:
        expected.append(('post', '/attendance.php', {'data': {'imagehash': 'hash-token', 'imagestring': code}}))
    assert requested == expected
    assert (response is not None) == bool(code)
    assert entry.failed == (code is None)


def test_details_do_not_require_hr() -> None:
    assert ptsbao.MainClass().details_selector['details']['hr'] is None
