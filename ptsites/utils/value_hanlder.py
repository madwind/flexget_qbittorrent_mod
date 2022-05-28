from datetime import date
from typing import Any

from dateutil.parser import parse


def handle_infinite(value: Any) -> str:
    return '0' if value in ['.', '-', '--', '---', '∞', 'Inf', 'Inf.', '&inf', '无限', '無限'] else value


def handle_join_date(value: Any) -> date:
    return parse(value).date()
