from __future__ import annotations

import re

import chardet
from requests import Response


def get_module_name(cls) -> str:
    return cls.__module__.rsplit('.', maxsplit=1)[-1]


def decode(response: Response | None) -> str | None:
    if response is None:
        return None
    content = response.content
    charset_encoding = chardet.detect(content).get('encoding')
    if charset_encoding == 'ascii':
        charset_encoding = 'unicode_escape'
    elif charset_encoding in ['Windows-1254','MacRoman']:
        charset_encoding = 'utf-8'
    return content.decode(charset_encoding if charset_encoding else 'utf-8', 'ignore')


def cookie_str_to_dict(cookie_str: str) -> dict:
    cookie_dict = {}
    for line in cookie_str.split(';'):
        if '=' in line:
            i = line.index('=')
            cookie_dict[line[0:i].strip()] = line[i + 1:].strip()
    return cookie_dict


def cookie_to_str(cookie_items: list) -> str:
    cookie_array = []
    for k, v in cookie_items:
        cookie_array.append(f'{k}={v}')
    return '; '.join(cookie_array).strip()


def dict_merge(dict1: dict, dict2: dict) -> None:
    for i in dict2:
        if isinstance(dict1.get(i), dict) and isinstance(dict2.get(i), dict):
            dict_merge(dict1[i], dict2[i])
        else:
            dict1[i] = dict2[i]


def get_site_name(url: str) -> str:
    if (re_object := re.search('(?<=//).*?(?=/)', url)) and len(domain := re_object.group().split('.')) > 1:
        site_name = domain[len(domain) - 2]
        return site_name if site_name != 'edu' else domain[len(domain) - 3]
