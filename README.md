# flexget_qbittorrent_mod
因为发现qBittorrent的webapi有last_activity信息，但是flexget官方的qBittorrent插件又没提供删种功能。

于是拼拼凑凑，东搬西抄，学了两天python，仿照flexget官方的tramissmion插件修改了官方的qbittorrent插件，添加了自动删种功能

官方transmission插件说明：<https://www.flexget.com/Cookbook/TorrentCleanup>

官方transmission插件源码：<https://github.com/Flexget/Flexget/blob/develop/flexget/plugins/clients/transmission.py>
 
 #### 下载配置
```yaml
templates:
  qb:
    qbittorrent_mod:
      host: qbittorrent.example.com
      port: 443
      use_ssl: true      
      username: admin
      password: 123456789
      action:
        add:
          category: Rss
          autoTMM: true
```

add属性可选参数表

与qbittorrent： /api/v2/torrents/add 的可选参数一致

当设置了autoTMM自动管理种子的时候 savepath是不起作用的

|Property | Type | Description
-|-|-
|savepath optional | string | Download folder
|cookie optional | string | Cookie sent to download the .torrent file
|category optional | string | Category for the torrent
|skip_checking optional | string | Skip hash checking. Possible values are true, false (default)
|paused optional | string | Add torrents in the paused state. Possible values are true, false (default)
|root_folder optional | string | Create the root folder. Possible values are true, false, unset (default)
|rename optional | string | Rename torrent
|upLimit optional | integer | Set torrent upload speed limit. Unit in bytes/second
|dlLimit optional | integer | Set torrent download speed limit. Unit in bytes/second
|autoTMM optional | bool | Whether Automatic Torrent Management should be used
|sequentialDownload optional | string | Enable sequential download. Possible values are true, false (default)
|firstLastPiecePrio optional | string | Prioritize download first last piece. Possible values are true, false (default) 
 
 以下配置实现删除
 Rss分类里：      qbittorrent_category in ['Rss'] 
 并且：           and
 4天没有流量的种子：qbittorrent_last_activity < now - timedelta(days=4)
#### 自动删种配置
```yaml
task:
  clean:
    from_qbittorrent_mod: 
      host: qbittorrent.example.com
      port: 443
      use_ssl: true
      username: admin
      password: 123456789
    disable: [seen, seen_info_hash]
    if:
      - qbittorrent_category in ['Rss'] and qbittorrent_last_activity < now - timedelta(days=4): accept
    qbittorrent_mod:
      host: qbittorrent.vammonitor.tk
      port: 443
      use_ssl: true      
      username: admin
      password: 123456789
      action:
        remove:
          delete_files: true  
```

entry属性表

在qbittorrent：/api/v2/torrents/info 返回的属性前加了qbittorrent前缀

其中 added_on,completion_on,last_activity,seen_complete 原本是unix时间戳，为了方便在配置里计算时间差都转换成了datetime类型

|Property | Type | Description
-|-|-
|qbittorrent_added_on | datetime | Time (Unix Epoch) when the torrent was added to the client
|qbittorrent_completion_on | datetime | Time (Unix Epoch) when the torrent completed
|qbittorrent_last_activity | datetime | Last time (Unix Epoch) when a chunk was downloaded/uploaded
|qbittorrent_seen_complete | datetime | Time (Unix Epoch) when this torrent was last seen complete
|qbittorrent_amount_left | integer | Amount of data left to download (bytes)
|qbittorrent_auto_tmm | bool | Whether this torrent is managed by Automatic Torrent Management
|qbittorrent_category | string | Category of the torrent
|qbittorrent_completed | integer | Amount of transfer data completed (bytes)
|qbittorrent_dl_limit | integer | Torrent download speed limit (bytes/s). -1 if ulimited.
|qbittorrent_dlspeed | integer | Torrent download speed (bytes/s)
|qbittorrent_downloaded | integer | Amount of data downloaded
|qbittorrent_downloaded_session | integer | Amount of data downloaded this session
|qbittorrent_eta | integer | Torrent ETA (seconds)
|qbittorrent_f_l_piece_prio | bool | True if first last piece are prioritized
|qbittorrent_force_start | bool | True if force start is enabled for this torrent
|qbittorrent_hash | string | Torrent hash
|qbittorrent_magnet_uri | string | Magnet URI corresponding to this torrent
|qbittorrent_max_ratio | float | Maximum share ratio until torrent is stopped from seeding/uploading
|qbittorrent_max_seeding_time | integer | Maximum seeding time (seconds) until torrent is stopped from seeding
|qbittorrent_name | string | Torrent name
|qbittorrent_num_complete | integer | Number of seeds in the swarm
|qbittorrent_num_incomplete | integer | Number of leechers in the swarm
|qbittorrent_num_leechs | integer | Number of leechers connected to
|qbittorrent_num_seeds | integer | Number of seeds connected to
|qbittorrent_priority | integer | Torrent priority. Returns -1 if queuing is disabled or torrent is in seed mode
|qbittorrent_progress | float | Torrent progress (percentage/100)
|qbittorrent_ratio | float | Torrent share ratio. Max ratio value: 9999.
|qbittorrent_ratio_limit | float | TODO (what is different from max_ratio?)
|qbittorrent_save_path | string | Path where this torrent's data is stored
|qbittorrent_seeding_time_limit | integer | TODO (what is different from max_seeding_time?)
|qbittorrent_seq_dl | bool | True if sequential download is enabled
|qbittorrent_size | integer | Total size (bytes) of files selected for download
|qbittorrent_state | string | Torrent state. See table here below for the possible values
|qbittorrent_super_seeding | bool | True if super seeding is enabled
|qbittorrent_tags | string | Comma-concatenated tag list of the torrent
|qbittorrent_time_active | integer | Total active time (seconds)
|qbittorrent_total_size | integer | Total size (bytes) of all file in this torrent (including unselected ones)
|qbittorrent_tracker | string | The first tracker with working status. (TODO: what is returned if no tracker is working?)
|qbittorrent_up_limit | integer | Torrent upload speed limit (bytes/s). -1 if ulimited.
|qbittorrent_uploaded | integer | Amount of data uploaded
|qbittorrent_uploaded_session | integer | Amount of data uploaded this session
|qbittorrent_upspeed | integer | Torrent upload speed (bytes/s)
