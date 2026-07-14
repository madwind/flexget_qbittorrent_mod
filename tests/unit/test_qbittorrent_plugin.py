from ptsites.qbittorrent.operations import QBittorrentOperationsMixin
from ptsites.qbittorrent.plugin import PluginQBittorrentMod, PluginQBittorrentModInput


def test_output_plugin_keeps_action_schema_after_split() -> None:
    action_schema = PluginQBittorrentMod.schema['properties']['action']

    assert 'add' in action_schema['properties']
    assert 'remove' in action_schema['properties']
    assert action_schema['maxProperties'] == 1


def test_output_plugin_inherits_operations_after_split() -> None:
    assert issubclass(PluginQBittorrentMod, QBittorrentOperationsMixin)
    assert callable(PluginQBittorrentMod.add_entries)
    assert callable(PluginQBittorrentMod.remove_entries)


def test_input_plugin_schema_is_unchanged() -> None:
    properties = PluginQBittorrentModInput.schema['properties']

    assert properties['server_state']['oneOf']
    assert properties['force_update']['enum'] == ['uploading', 'active', 'all']
