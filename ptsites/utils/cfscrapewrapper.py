import asyncio
import re

import flexget.utils.requests
import requests
from loguru import logger
from requests import Session

from .net_utils import NetUtils

try:
    from pyppeteer import launch
    from pyppeteer_stealth import stealth
except ImportError as e:
    logger.error('Error importing pyppeteer: {}', e)

DDoS_protection_by_Cloudflare = 'DDoS protection by .+?Cloudflare'


class CFScrapeWrapperRequests(Session):
    def request(self, method: str, url: str, *args, **kwargs) -> requests.Response:
        response = super(CFScrapeWrapperRequests, self).request(method, url, *args, **kwargs)
        if response is not None and response.content:
            if re.search(DDoS_protection_by_Cloudflare, NetUtils.decode(response)):
                cf_cookie = asyncio.run(CFScrapeWrapper.get_cf_cookie(url, self))
                self.cookies.update(NetUtils.cookie_str_to_dict(cf_cookie))
                response = super(CFScrapeWrapperRequests, self).request(method, url, *args, **kwargs)
        return response


class CFScrapeWrapperFlexget(flexget.utils.requests.Session):
    def request(self, method: str, url: str, *args, **kwargs) -> requests.Response:
        response = super(CFScrapeWrapperFlexget, self).request(method, url, *args, **kwargs)
        if response is not None and response.content:
            if re.search(DDoS_protection_by_Cloudflare, NetUtils.decode(response)):
                cf_cookie = asyncio.run(CFScrapeWrapper.get_cf_cookie(url, self))
                self.cookies.update(NetUtils.cookie_str_to_dict(cf_cookie))
                response = super(CFScrapeWrapperFlexget, self).request(method, url, *args, **kwargs)
        return response


class CFScrapeWrapper:
    @staticmethod
    def create_scraper(session):
        if isinstance(session, Session):
            cf_session = CFScrapeWrapperRequests()
        else:
            cf_session = CFScrapeWrapperFlexget()
        cf_session.headers.update(session.headers)
        cf_session.cookies.update(session.cookies)
        return cf_session

    @staticmethod
    async def get_cf_cookie(url, session):
        logger.info(f'get_cf_cookie: {url}')
        browser = await launch(headless=True, handleSIGINT=False, handleSIGTERM=False, handleSIGHUP=False,
                               args=['--no-sandbox'])
        page = await browser.newPage()
        await stealth(page)
        await page.setUserAgent(session.headers.get('user-agent'))
        cookie_without_cf = NetUtils.cookie_to_str(list(
            filter(lambda x: x[0] not in ['__cfduid', 'cf_clearance', '__cf_bm'], session.cookies.items())))
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
