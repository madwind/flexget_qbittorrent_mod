from __future__ import annotations

import json
import pkgutil
from types import SimpleNamespace

import pytest

from ptsites import executor


def test_get_site_class_imports_from_trackers_package(monkeypatch) -> None:
    expected_class = type('ExampleTracker', (), {})
    imported = {}

    def fake_import_module(name: str, package: str):
        imported['name'] = name
        imported['package'] = package
        return SimpleNamespace(MainClass=expected_class)

    monkeypatch.setattr(executor.importlib, 'import_module', fake_import_module)

    assert executor.get_site_class('Example') is expected_class
    assert imported == {
        'name': '.trackers.example',
        'package': executor.__package__,
    }


def test_trackers_path_points_to_renamed_directory() -> None:
    assert executor.TRACKERS_PATH.name == 'trackers'
    assert executor.TRACKERS_PATH.is_dir()


TRACKER_MODULES = [module.name for module in pkgutil.iter_modules([str(executor.TRACKERS_PATH)])]


@pytest.mark.parametrize('module_name', TRACKER_MODULES)
def test_tracker_module_exposes_main_class(module_name: str) -> None:
    try:
        tracker_class = executor.get_site_class(module_name)
    except ModuleNotFoundError as error:
        if error.name in {'numpy', 'PIL'}:
            pytest.skip(f'{module_name} requires the image dependency {error.name}')
        raise
    assert isinstance(tracker_class, type)


def test_save_cookie_writes_runtime_file_in_working_directory(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    entry = {
        'site_name': 'example',
        'session_cookie': 'session=test-value',
    }

    executor.save_cookie(entry)

    saved = json.loads((tmp_path / 'cookies_backup.json').read_text(encoding='utf-8'))
    assert saved['example']['cookie'] == 'session=test-value'
    assert saved['example']['date']


def test_save_cookie_ignores_empty_cookie(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    executor.save_cookie({'site_name': 'example', 'session_cookie': ''})

    assert not (tmp_path / 'cookies_backup.json').exists()
