import pytest
from requests import Response

from ptsites.base.entry import SignInEntry
from ptsites.trackers.htpt import MainClass


@pytest.mark.parametrize('already_signed_in', [False, True])
def test_attendance_submits_the_form_only_when_needed(monkeypatch, already_signed_in):
    tracker = MainClass()
    entry = SignInEntry(url=tracker.URL, site_name='htpt', cookie='test=value', result='')
    calls = []
    attendance_url = tracker.URL + 'attendance.php'

    def request(entry, method, url, **kwargs):
        calls.append((method, url, kwargs))
        response = Response()
        response.url = url
        response.status_code = 200
        response.encoding = 'utf-8'
        content = '<span>今日已签到 ✓</span>' if already_signed_in or method == 'post' else (
            '<form method="post"><input name="action" value="sign"></form>'
        )
        response._content = content.encode('utf-8')
        return response

    monkeypatch.setattr(tracker, 'request', request)

    tracker.sign_in(entry, {})

    expected = [('get', attendance_url, {})]
    if not already_signed_in:
        expected.append(('post', attendance_url, {'data': {'action': 'sign'}}))
    assert calls == expected
    assert entry['result'] == '今日已签到'
    assert not entry.failed
