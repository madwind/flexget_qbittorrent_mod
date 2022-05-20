import json
from pathlib import Path

RECORD_FILE_PATH = 'reseed'


def load_record(site_name):
    record_file = Path(f'{RECORD_FILE_PATH}/{site_name}.json')
    if record_file.is_file():
        return json.loads(record_file.read_text())
    else:
        return {}


def save_record(site_name, record):
    Path(RECORD_FILE_PATH).mkdir(exist_ok=True)
    record_file = Path(f'{RECORD_FILE_PATH}/{site_name}.json')
    record_file.touch(exist_ok=True)
    record_file.write_text(json.dumps(record))
