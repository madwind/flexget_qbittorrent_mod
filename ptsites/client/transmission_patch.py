import copy

from flexget import plugin
from flexget.plugins.clients.transmission import PluginTransmission

from ..utils.net_utils import NetUtils


def on_task_download(self, task, config):
    """
    Call download plugin to generate the temp files we will load
    into deluge then verify they are valid torrents
    """
    config = self.prepare_config(config)
    if not config['enabled']:
        return
    # If the download plugin is not enabled, we need to call it to get our temp .torrent files
    if 'download' not in task.config:
        download = plugin.get('download', self)
        headers = copy.deepcopy(task.requests.headers)
        for entry in task.accepted:
            if entry.get('transmission_id'):
                # The torrent is already loaded in deluge, we don't need to get anything
                continue
            if config['action'] != 'add' and entry.get('torrent_info_hash'):
                # If we aren't adding the torrent new, all we need is info hash
                continue
            if entry.get('headers'):
                task.requests.headers.update(entry['headers'])
            else:
                task.requests.headers.clear()
                task.requests.headers = headers
            if entry.get('cookie'):
                task.requests.cookies.update(NetUtils.cookie_str_to_dict(entry['cookie']))
            else:
                task.requests.cookies.clear()
            download.get_temp_file(task, entry, handle_magnets=True, fail_html=True)


PluginTransmission.on_task_download = on_task_download
