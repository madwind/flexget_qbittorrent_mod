import json
from pathlib import Path

RECORD_FILE_PATH = 'reseed'


def load_record(site_name: str) -> dict:
    record_file = Path(f'{RECORD_FILE_PATH}/{site_name}.json')
    return json.loads(record_file.read_text()) if record_file.is_file() else {}


def save_record(site_name: str, record: dict) -> None:
    Path(RECORD_FILE_PATH).mkdir(exist_ok=True)
    record_file = Path(f'{RECORD_FILE_PATH}/{site_name}.json')
    record_file.touch(exist_ok=True)
    record_file.write_text(json.dumps(record))
