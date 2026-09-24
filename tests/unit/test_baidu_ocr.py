from __future__ import annotations

from loguru import logger
from PIL import Image

from ptsites.base.entry import SignInEntry
from ptsites.utils import baidu_ocr


def test_get_client_reuses_sdk_client(monkeypatch) -> None:
    clients = []

    class FakeAipOcr:
        def __init__(self, app_id, api_key, secret_key):
            clients.append((app_id, api_key, secret_key))

    monkeypatch.setattr(baidu_ocr, 'AipOcr', FakeAipOcr)
    baidu_ocr._get_cached_client.cache_clear()
    entry = SignInEntry()
    config = {
        'aipocr': {
            'app_id': 'app-id',
            'api_key': 'api-key',
            'secret_key': 'secret-key',
        }
    }

    assert baidu_ocr.get_client(entry, config) is baidu_ocr.get_client(entry, config)
    assert clients == [('app-id', 'api-key', 'secret-key')]
    baidu_ocr._get_cached_client.cache_clear()


def test_japanese_ocr_network_error_is_recoverable_and_redacted(monkeypatch) -> None:
    secret = 'must-not-be-logged'
    messages = []

    class FailingClient:
        def basicAccurate(self, *args, **kwargs):
            raise ConnectionError(f'https://example.test/token?client_secret={secret}')

    monkeypatch.setattr(baidu_ocr, 'get_client', lambda *args: FailingClient())
    sink_id = logger.add(messages.append, format='{message}')
    entry = SignInEntry()
    try:
        assert baidu_ocr.get_jap_ocr(Image.new('RGB', (10, 10)), entry, {}) is None
    finally:
        logger.remove(sink_id)

    assert not entry.failed
    assert secret not in ''.join(messages)
    assert 'ConnectionError' in ''.join(messages)
