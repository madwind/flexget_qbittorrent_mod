import json
import pathlib

from flexget.entry import Entry


class SignInEntry(Entry):
    def last_date(self) -> str:
        file_name = 'cookies_backup.json'
        site_name = self['site_name']
        cookies_backup_file = pathlib.Path.cwd().joinpath(file_name)
        if cookies_backup_file.is_file():
            cookies_backup_json = json.loads(cookies_backup_file.read_text(encoding='utf-8'))
        else:
            cookies_backup_json = {}
        if isinstance(cookies_backup_json.get(site_name), dict):
            return cookies_backup_json.get(site_name).get('date')

    def fail_with_prefix(self, reason: str) -> None:
        self.fail(f"{self.get('prefix')}=> {reason}. ({self.last_date()})")
