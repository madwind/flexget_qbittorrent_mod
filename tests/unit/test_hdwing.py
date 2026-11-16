import pytest
from requests import Response

from ptsites.base.entry import SignInEntry
from ptsites.trackers.hdwing import MainClass


@pytest.mark.parametrize('state', ['unsigned', 'signed', 'missing_csrf'])
def test_hdwing_attendance_workflow(monkeypatch, state):
    tracker = MainClass()
    entry = SignInEntry(title='HDWING', site_name='hdwing', site_config='PHPSESSID=old; uid=42; auth=test', result='')
    tracker.sign_in_build_entry(entry, {})
    assert entry['cookie'] == 'uid=42; auth=test'
    assert tracker.reseed_build_schema() == {'hdwing': {'type': 'string'}}

    torrents_url = tracker.URL + 'torrents.php'
    attendance_url = tracker.URL + 'plugin_sign-in.php?cmd=signin'
    page = {
        'unsigned': '<meta name="x-csrf" content="fixture-csrf">',
        'signed': '<a class="label label-default" href="#">已签到</a>',
        'missing_csrf': '<html></html>',
    }[state]
    success = '{"state":"success","signindays":7,"integral":17}'
    calls = []

    def request(entry, method, url, **kwargs):
        calls.append((method, url, kwargs))
        response = Response()
        response.url = url
        response.status_code = 200
        response._content = (page if method == 'get' else success).encode()
        return response

    monkeypatch.setattr(tracker, 'request', request)

    tracker.sign_in(entry, {})

    expected = [('get', torrents_url, {})]
    if state == 'unsigned':
        expected.append(('post', attendance_url, {'data': {'csrf': 'fixture-csrf'}}))
        assert entry['result'] == success
    if state == 'signed':
        assert entry['result'] == '已签到'
    assert calls == expected
    assert entry['base_content'] == page
    assert entry.failed == (state == 'missing_csrf')
