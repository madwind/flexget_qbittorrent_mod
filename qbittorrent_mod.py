from flexget import plugin
from flexget.event import event

from .ptsites.qbittorrent.plugin import PluginQBittorrentMod, PluginQBittorrentModInput


@event('plugin.register')
def register_plugin() -> None:
    plugin.register(PluginQBittorrentMod, 'qbittorrent_mod', api_ver=2)
    plugin.register(PluginQBittorrentModInput, 'from_qbittorrent_mod', api_ver=2)
