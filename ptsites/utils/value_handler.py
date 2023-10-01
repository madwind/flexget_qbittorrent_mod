from datetime import date
from typing import Any

from dateutil.parser import parse


def handle_infinite(value: Any) -> str:
    return '0' if value in ['.', '-', '--', '---', '∞', 'Inf', 'Inf.', '&inf', '无限', '無限'] else value


def handle_join_date(value: Any) -> date:
    return parse(value).date()


suffix_dict = {'BiB': 1, 'KiB': 1024, 'MiB': 1048576, 'GiB': 1073741824, 'TiB': 1099511627776, 'PiB': 1125899906842624,
               'EiB': 1152921504606846976, 'ZiB': 1180591620717411303424}


def size(value: float, suffix: str) -> float:
    return value * suffix_dict.get(suffix)
