import asyncio
import re

import chardet
from loguru import logger
from pyppeteer import launch
from pyppeteer_stealth import stealth


class NetUtils:
    DDoS_protection_by_Cloudflare = 'DDoS protection by .+?Cloudflare'

    @staticmethod
    def decode(response):
        if response is None:
            return None
        content = response.content
        charset_encoding = chardet.detect(content).get('encoding')
        if charset_encoding == 'ascii':
            charset_encoding = 'unicode_escape'
        elif charset_encoding == 'Windows-1254':
            charset_encoding = 'utf-8'
        return content.decode(charset_encoding if charset_encoding else 'utf-8', 'ignore')

    @staticmethod
    def cookie_str_to_dict(cookie_str):
        cookie_dict = {}
        for line in cookie_str.split(';'):
            if '=' in line:
                i = line.index('=')
                cookie_dict[line[0:i].strip()] = line[i + 1:].strip()
        return cookie_dict

    @staticmethod
    def cookie_to_str(cookie_items: list):
        cookie_array = []
        for k, v in cookie_items:
            cookie_array.append(f'{k}={v}')
        return str.join('; ', cookie_array).strip()

    @staticmethod
    async def get_cf_cookie(log_name, url, user_agent, cookie):
        logger.info(f"{log_name} get_cf_cookie")
        if not (launch and stealth):
            logger.error('Dependency does not exist: [pyppeteer, pyppeteer_stealth]')
            return
        browser = await launch(headless=True, handleSIGINT=False, handleSIGTERM=False, handleSIGHUP=False,
                               args=['--no-sandbox'])
        page = await browser.newPage()
        await stealth(page)
        await page.setUserAgent(user_agent)
        cookie_without_cf = ''
        if cookie:
            cookie_without_cf = ';'.join(
                list(filter(lambda x: not re.search('__cfduid|cf_clearance|__cf_bm', x),
                            cookie.split(';'))))
        await page.setExtraHTTPHeaders({'cookie': cookie_without_cf})
        await page.goto(url)
        await asyncio.sleep(10)
        page_cookie = await page.cookies()
        if cookie_without_cf:
            cookie_without_cf += ';'
        cf_cookie = cookie_without_cf + ';'.join(
            list(map(lambda c: f"{c['name']}={c['value']}", page_cookie)))
        await browser.close()
        return cf_cookie

    @staticmethod
    def dict_merge(dict1, dict2):
        for i in dict2:
            if isinstance(dict1.get(i), dict) and isinstance(dict2.get(i), dict):
                NetUtils.dict_merge(dict1[i], dict2[i])
            else:
                dict1[i] = dict2[i]
