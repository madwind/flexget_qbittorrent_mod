import json
from pathlib import Path


class UrlRecorder:
    @staticmethod
    def load_record(site_name):
        record_file = Path('url-record/{}.json'.format(site_name))
        if record_file.is_file():
            return json.loads(record_file.read_text())
        else:
            return {}

    @staticmethod
    def save_record(site_name, record):
        Path('url-record').mkdir(exist_ok=True)
        record_file = Path('url-record/{}.json'.format(site_name))
        record_file.touch(exist_ok=True)
        record_file.write_text(json.dumps(record))
