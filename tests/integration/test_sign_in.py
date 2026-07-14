from __future__ import annotations

import json
import os
from datetime import datetime

import pytest

from ptsites import executor
from ptsites.base.entry import SignInEntry


def _site_config_from_environment() -> str | dict:
    raw_config = os.environ.get('PT_TEST_SITE_CONFIG')
    if raw_config:
        return json.loads(raw_config)

    cookie = os.environ.get('PT_TEST_COOKIE')
    if cookie:
        return cookie

    pytest.skip('set PT_TEST_COOKIE or PT_TEST_SITE_CONFIG before running the integration test')


@pytest.mark.integration
def test_real_tracker_sign_in() -> None:
    site_name = os.environ.get('PT_TEST_SITE')
    if not site_name:
        pytest.skip('set PT_TEST_SITE before running the integration test')

    site_config = _site_config_from_environment()
    config = {
        'cookie_backup': False,
        'get_details': False,
        'get_messages': False,
        'sites': {site_name: site_config},
    }
    entry = SignInEntry(title=f'{site_name} {datetime.now().date()}', url='')
    entry['site_name'] = site_name
    entry['class_name'] = site_name
    entry['site_config'] = site_config
    entry['result'] = ''
    entry['messages'] = ''
    entry['details'] = ''

    executor.build_sign_in_entry(entry, config)
    executor.sign_in(entry, config)

    assert not entry.failed, entry.get('reason')

