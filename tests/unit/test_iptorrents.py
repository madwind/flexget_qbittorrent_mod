import pytest
from loguru import logger
from requests import Response

from ptsites.base.entry import SignInEntry
from ptsites.trackers.iptorrents import MainClass


@pytest.mark.parametrize('include_join_date', [True, False])
def test_iptorrents_profile_parsing_keeps_page_content_out_of_logs(monkeypatch, include_join_date):
    tracker = MainClass()
    entry = SignInEntry(title='IPTorrents', url=tracker.URL, site_name='iptorrents', site_config='test-cookie')
    entry['base_content'] = '<a href="/u/42">Profile</a>'
    joined = '<div>Joined <time datetime="2024-05-06T00:00:00Z">May 6</time></div>' if include_join_date else ''
    page = f'''
        <div>Uploaded</div> 8.50 TB
        <div>Downloaded</div> 2.00 TB
        <div>Ratio</div> <span></span> 4.25
        <div>Bonus Points</div> 1,234.5
        {joined}
        <div>Active Torrents</div> 1,234 Seeding / 56 Leeching
        <dt>Passkey</dt><dd><code>synthetic-passkey</code></dd>
    '''

    def request(entry, method, url):
        assert (method, url) == ('get', 'https://iptorrents.com/user.php?u=42')
        response = Response()
        response.url = url
        response.status_code = 200
        response._content = page.encode()
        return response

    monkeypatch.setattr(tracker, 'request', request)
    logged = []
    handler = logger.add(logged.append, level='DEBUG')
    try:
        tracker.get_details(entry, {})
    finally:
        logger.remove(handler)

    assert 'synthetic-passkey' not in ''.join(logged)
    if include_join_date:
        assert not entry.failed
        assert entry['details'] == {
            'uploaded': '8.50 TB', 'downloaded': '2.00 TB', 'share_ratio': '4.25', 'points': '1234.5',
            'join_date': '2024-05-06', 'seeding': '1234', 'leeching': '56', 'hr': '*',
        }
    else:
        assert entry.failed
        assert 'detail: join_date not found' in ''.join(logged)
