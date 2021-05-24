from flexget import plugin
from flexget.event import event
from loguru import logger

from .ptsites.utils.cfscrapewrapper import CFScrapeWrapper

logger = logger.bind(name='cfscraper_mod')


class CFScraperMod:
    """
    Plugin that enables scraping of cloudflare protected sites.

    Example::
      cfscraper_mod: yes
    """

    schema = {'type': 'boolean'}

    @plugin.priority(253)
    def on_task_start(self, task, config):
        if config is True:
            task.requests = CFScrapeWrapper.create_scraper(task.requests)


@event('plugin.register')
def register_plugin():
    plugin.register(CFScraperMod, 'cfscraper_mod', api_ver=2)
