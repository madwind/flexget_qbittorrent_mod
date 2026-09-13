from __future__ import annotations

import re
from types import SimpleNamespace

from PIL import Image
from requests import Response

from ptsites.base.entry import SignInEntry
from ptsites.base.work import Work
from ptsites.trackers import dmhy


def test_workflow_uses_browser_page_urls() -> None:
    tracker = dmhy.MainClass()
    entry = SignInEntry()
    entry['site_config'] = {'username': 'tester'}

    assert [work.url for work in tracker.sign_in_build_workflow(entry, {})] == [
        '/showup.php',
        '/showup.php?action=show',
        '/showup.php',
    ]


def test_captcha_image_request_keeps_image_hash() -> None:
    tracker = dmhy.MainClass()
    entry = SignInEntry()
    entry['site_config'] = {'username': 'tester'}
    work = tracker.sign_in_build_workflow(entry, {})[1]
    image_url = 'image.php?action=adbc2&req=v2.signed-request&imagehash=c23fc31a6e29bccc'
    html = f'<img src="{image_url}" />'

    assert re.search(work.img_regex, html).group() == image_url


def test_build_data_uses_dynamic_images_then_registers_image_hash(monkeypatch) -> None:
    tracker = dmhy.MainClass()
    entry = SignInEntry()
    entry.update({
        'site_config': {'username': 'tester', 'comment': 'Hello World'},
        'url': tracker.URL,
    })
    work = tracker.sign_in_build_workflow(entry, {})[1]
    full_image_url = 'image.php?action=adbc2&req=v2.signed-request&imagehash=c23fc31a6e29bccc'
    html = f'''
        <input type="hidden" name="_csrf" value="csrf-token" />
        <img src="{full_image_url}" />
        <input type="submit" name="captcha_token" value="Salaryman Kintarou / 上班族金太郎" />
        <input type="hidden" name="req" value="v2.signed-request" />
        <input type="hidden" name="hash" value="c23fc31a6e29bccc" />
        <input type="hidden" name="form" value="form-token" />
    '''
    image = Image.new('RGB', (10, 10))
    analyzed_urls = []
    requested = []

    monkeypatch.setattr(
        tracker,
        'get_image',
        lambda entry_arg, config, url, char_count: analyzed_urls.append(url) or (image, image),
    )
    monkeypatch.setattr(dmhy.baidu_ocr, 'get_jap_ocr', lambda *args: '上班族金太郎')
    monkeypatch.setattr(
        dmhy,
        'process',
        SimpleNamespace(extractOne=lambda *args, **kwargs: ('上班族金太郎', 100)),
    )
    monkeypatch.setattr(dmhy, 'fuzz', SimpleNamespace(partial_ratio=object()))

    def fake_request(entry_arg, method, url, **kwargs):
        requested.append((method, url, kwargs))
        response = Response()
        response.status_code = 200
        response.url = url
        return response

    monkeypatch.setattr(tracker, 'request', fake_request)

    assert tracker.build_data(entry, {}, work, html, {'retry': 20, 'char_count': 4, 'score': 40}) == {
        'captcha_token': 'Salaryman Kintarou / 上班族金太郎',
        'req': 'v2.signed-request',
        'hash': 'c23fc31a6e29bccc',
        'form': 'form-token',
        '_csrf': 'csrf-token',
        'message': 'Hello World',
    }
    assert analyzed_urls == ['image.php?action=adbc2&req=v2.signed-request']
    assert requested == [(
        'get',
        tracker.URL + full_image_url,
        {'headers': {
            'referer': tracker.URL + 'showup.php',
            'sec-fetch-dest': 'image',
            'sec-fetch-mode': 'no-cors',
            'sec-fetch-site': 'same-origin',
        }},
    )]


def test_build_data_preserves_csrf_across_captcha_reload(monkeypatch) -> None:
    tracker = dmhy.MainClass()
    entry = SignInEntry()
    entry.update({
        'site_config': {'username': 'tester', 'comment': 'Hello World'},
        'url': tracker.URL,
    })
    work = tracker.sign_in_build_workflow(entry, {})[1]
    reload_url = 'image.php?action=reload_adbc2&div=showup&rand=123'
    initial_html = f'''
        <meta name="csrf-token" content="csrf-from-page" />
        <img src="image.php?action=adbc2&req=v2.initial&imagehash={'a' * 40}" />
        <a onclick="ajax.update('{reload_url}','showup')">refresh</a>
    '''
    refreshed_html = f'''
        <img src="image.php?action=adbc2&req=v2.refreshed&imagehash={'b' * 40}" />
        <input type="submit" name="captcha_answer" value="Eko Eko Azarak / エコエコアザラク" />
        <input type="hidden" name="req" value="v2.refreshed" />
        <input type="hidden" name="hash" value="{'b' * 40}" />
        <input type="hidden" name="form" value="{'c' * 40}" />
    '''
    image = Image.new('RGB', (10, 10))
    image_results = iter([None, (image, image)])

    monkeypatch.setattr(tracker, 'get_image', lambda *args: next(image_results))
    monkeypatch.setattr(dmhy.baidu_ocr, 'get_jap_ocr', lambda *args: 'エコエコアザラク')
    monkeypatch.setattr(
        dmhy,
        'process',
        SimpleNamespace(extractOne=lambda *args, **kwargs: ('エコエコアザラク', 100)),
    )
    monkeypatch.setattr(dmhy, 'fuzz', SimpleNamespace(partial_ratio=object()))

    def fake_request(entry_arg, method, url, **kwargs):
        response = Response()
        response.status_code = 200
        response.url = url
        response._content = refreshed_html.encode() if url.endswith(reload_url) else b''
        return response

    monkeypatch.setattr(tracker, 'request', fake_request)

    data = tracker.build_data(entry, {}, work, initial_html, {'retry': 20, 'char_count': 4, 'score': 40})

    assert data['_csrf'] == 'csrf-from-page'
    assert data['req'] == 'v2.refreshed'
    assert data['captcha_answer'] == 'Eko Eko Azarak / エコエコアザラク'


def test_anime_answer_is_submitted_from_showup_page(monkeypatch) -> None:
    tracker = dmhy.MainClass()
    entry = SignInEntry()
    entry.update({
        'site_config': {'username': 'tester'},
        'url': tracker.URL,
    })
    work = Work(
        url=tracker.URL + 'showup.php?action=show',
        method=tracker.sign_in_by_anime,
        data={},
    )
    answer = {
        'captcha_token': 'answer',
        'req': 'request-token',
        'hash': 'image-hash',
        'form': 'form-token',
    }
    submitted = {}
    response = Response()
    response.status_code = 200

    monkeypatch.setattr(dmhy, 'fuzz', object())
    monkeypatch.setattr(dmhy, 'process', object())
    monkeypatch.setattr(tracker, 'build_data', lambda *args: answer)

    def fake_request(entry_arg, method, url, **kwargs):
        submitted.update(method=method, url=url, **kwargs)
        return response

    monkeypatch.setattr(tracker, 'request', fake_request)

    assert tracker.sign_in_by_anime(entry, {}, work, '<html>') is response
    assert submitted == {
        'method': 'post',
        'url': tracker.URL + 'showup.php?action=show',
        'data': answer,
        'headers': {
            'origin': 'https://u2.dmhy.org',
            'referer': tracker.URL + 'showup.php',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
        },
    }
