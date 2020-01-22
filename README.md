# flexget_qbittorrent_mod
因为发现qBittorrent的webapi有last_activity信息，但是flexget官方的qBittorrent插件又没提供删种功能。

于是拼拼凑凑，东搬西抄，学了两天python，仿照flexget官方的tramissmion插件修改了官方的qbittorrent插件，添加了自动删种功能

官方transmission插件说明：<https://www.flexget.com/Cookbook/TorrentCleanup>

官方transmission插件源码：<https://github.com/Flexget/Flexget/blob/develop/flexget/plugins/clients/transmission.py>

官方qbittorrent插件源码：<https://github.com/Flexget/Flexget/blob/develop/flexget/plugins/clients/qbittorrent.py>

## 安装插件
##### 此段说明抄抄袭于<https://github.com/Juszoe/flexget-nexusphp/blob/master/README.md>
1. 下载插件 [qbittorrent_mod.py](https://github.com/IvonWei/flexget_qbittorrent_mod/archive/0.1.zip)
2. 在Flexget配置文件夹下新建plugins文件夹，例如：
```
~/.flexget/plugins/  # Linux
C:\Users\<YOURUSER>\flexget\plugins\  # Windows
```
3. 将插件拷贝至plugins
4. 若启用了Web-UI或守护进程，则重启flexget重新加载配置

 #### 配置模板
```yaml
web_server:
  bind: 0.0.0.0
  port: 3539

templates:
  #输出模板 添加种子
  qbittorrent_add_template:
    qbittorrent_mod:
      host: qbittorrent.example.com
      port: 443
      use_ssl: true
      username: admin
      password: 123456789
      action:
        add:
          #参考add可选参数
          #分类
          category: Rss
          #自动管理种子
          autoTMM: true

  #输出模板 自动开始：用于校验完数据自动开始
  qbittorrent_resume_template:
    qbittorrent_mod:
      host: qbittorrent.example.com
      port: 443
      use_ssl: true
      username: admin
      password: 123456789
      action:
        resume:
          #暂时没什么用
          only_complete: true

  #输出模板 自动删种
  qbittorrent_delete_template:
    qbittorrent_mod:
      host: qbittorrent.example.com
      port: 443
      use_ssl: true
      username: admin
      password: 123456789
      action:
        remove:
          #删种同时是否删除数据
          delete_files: true

  #输入模板 从qbittorrent获取数据
  from_qbittorrent_template:
    from_qbittorrent_mod:
      host: qbittorrent.example.com
      port: 443
      use_ssl: true
      username: admin
      password: 123456789

schedules:
  #每分钟执行pt1,pt2
  - tasks: [pt1, pt2]
    interval:
      minutes: 1
  #每隔5分钟执行resume,delete
  - tasks: [resume, delete]
    interval:
      minutes: 5

#任务列表
tasks:
  pt1:
    #rss订阅链接
    rss: https://pt1.com/rss
    #过滤器 接受带有 CCTV 字样的种子
    regexp:
      accept:
        - CCTV
      from: title
    #输出模板 添加种子
    template: qbittorrent_add_template
  
  pt2:
    rss: https://pt1.com/rss
    #过滤器 接受全部
    accept_all: yes
    template: qbittorrent_add_template

  #自动开始
  resume:
    #关闭任务记录 
    disable: [seen, seen_info_hash]
    if:
      #选择暂停状态已完成的种子
      - qbittorrent_state == 'pausedUP': accept
    #使用输入模板 从qbittorrent获取数据
    #使用输出模板 自动开始
    template:
      - from_qbittorrent_template
      - qbittorrent_resume_template
 
  #自动删种
  delete:
    disable: [seen, seen_info_hash]
    if:
      #参考entry属性列表
      #种子在 Rss分类 并且 最后活动时间 < 4天 
      - qbittorrent_category in ['Rss'] and qbittorrent_last_activity < now - timedelta(days=4): accept
      #种子数据丢失 或者 （种子处于未完成的暂停状态 并且 下载大小为0）：一般是辅助失败的种子 
      - qbittorrent_state == 'missingFiles' or (qbittorrent_state in ['pausedDL'] and qbittorrent_downloaded == 0): accept
    #使用输入模板 从qbittorrent获取数据
    #使用输出模板 自动删种
    template:
      - from_qbittorrent_template
      - qbittorrent_delete_template

```

### add可选参数

与qbittorrent： /api/v2/torrents/add 的可选参数一致

当设置了autoTMM自动管理种子时 savepath会被忽略

|Property | Type | Description
-|-|-
|savepath  | string | Download folder
|cookie  | string | Cookie sent to download the .torrent file
|category  | string | Category for the torrent
|skip_checking  | string | Skip hash checking. Possible values are true, false (default)
|paused  | string | Add torrents in the paused state. Possible values are true, false (default)
|root_folder  | string | Create the root folder. Possible values are true, false, unset (default)
|rename  | string | Rename torrent
|upLimit  | integer | Set torrent upload speed limit. Unit in bytes/second
|dlLimit  | integer | Set torrent download speed limit. Unit in bytes/second
|autoTMM  | bool | Whether Automatic Torrent Management should be used
|sequentialDownload  | string | Enable sequential download. Possible values are true, false (default)
|firstLastPiecePrio  | string | Prioritize download first last piece. Possible values are true, false (default)
 
 
entry属性列表

在qbittorrent：/api/v2/torrents/info 返回的属性前加了qbittorrent前缀

其中 added_on,completion_on,last_activity,seen_complete 原本是unix时间戳，为了方便计算时间差都转换成了datetime类型

|Property | Type | Description
-|-|-
|qbittorrent_added_on | datetime | Time when the torrent was added to the client
|qbittorrent_completion_on | datetime | Time when the torrent completed
|qbittorrent_last_activity | datetime | Last time when a chunk was downloaded/uploaded
|qbittorrent_seen_complete | datetime | Time when this torrent was last seen complete
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
