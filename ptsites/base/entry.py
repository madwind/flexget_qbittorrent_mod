from flexget.entry import Entry


class SignInEntry(Entry):
    def fail_with_prefix(self, reason: str) -> None:
        self.fail(f"{self.get('prefix')}=> {reason}")
