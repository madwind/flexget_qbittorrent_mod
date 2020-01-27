# flexget_qbittorrent_mod
这是一个 Flexget 的 qBittorrent插件

参考：

IYUUAutoReseed：<https://github.com/ledccn/IYUUAutoReseed>

qBittorrent-Web-API<https://github.com/qbittorrent/qBittorrent/wiki/Web-API-Documentation#api-v20>

## 实现种子生命周期的自动管理
1. 下载：Rss获取种子，筛选后推送到qittorrent下载
2. 修改：根据种子的tracker，修改种子的tag，或替换tracker
3. 辅种：下载完成后，查询IYUUAutoReseed辅种数据，校验完成后自动开始做种
4. 删种：符合删除条件后，删除包含辅种在内的所有种子

## 安装插件
1. 下载插件 [releases](https://github.com/IvonWei/flexget_qbittorrent_mod/releases)
2. 在Flexget配置文件夹下新建plugins文件夹，例如：
```
~/.flexget/plugins/  # Linux
C:\Users\<YOURUSER>\flexget\plugins\  # Windows
```
3. 将所有的 .py 文件解压至plugins
4. 若启用了Web-UI或守护进程，则重启flexget重新加载配置

 #### 配置模板
 先介绍一下我的环境
 
 每隔1分钟下载种子下载到 Rss分类
 
 每隔10分钟 自动给种子打标签 修改tracker 检查有没有校验完的种子自动开始 检查磁盘空间小于20G则删除Rss分类下2天没流量的种子
 
 每个1小时 执行一次辅种
 
注：Flexget不允许用中文注释 请用源码里的config.yml对照修改
```yaml
web_server:
  bind: 0.0.0.0
  #web监听端口
  port: 3539

templates:
  #基础模板
  qbittorrent_base_template:
    qbittorrent_mod:
      host: qbittorrent.example.com
      port: 443
      use_ssl: true
      username: admin
      password: 123456789xx

  #添加种子
  qbittorrent_add_template:
    qbittorrent_mod:
      action:
        add:
          #参考add可选参数
          #分类
          category: Rss
          #自动管理种子
          autoTMM: true
  
  #修改种子信息 
  qbittorrent_modify_template:
    qbittorrent_mod:
      action:
        modify:
          #根据tracker的url自动添加种子标签 例如以下的tracker会提出出 pt1 的标签 v0.1.3新增
          tag_by_tracker: true
          #批量替换tracker 例如把http替换成https (需要完全匹配) v0.1.3新增
          replace_tracker:
            'http://tracker.pt1.com/announce.php?passkey=xxxxxxxxxxxxxx': 'https://tracker.pt1.com/announce.php?passkey=xxxxxxxxxxxxxx'

  #自动开始：用于校验完数据自动开始
  qbittorrent_resume_template:
    qbittorrent_mod:
      action:
        resume:
          #暂时没什么用
          only_complete: true

  #自动删种
  qbittorrent_delete_template:
    qbittorrent_mod:
      action:
        remove:
          #检查所有辅种是否都满足删除条件 v0.1.2新增
          #true: 只要有其中一个不满足条件则放弃删除
          #false（默认）: 只要有一个满足删除条件 就全部删除 
          check_reseed: true
          #删种同时是否删除数据
          delete_files: true
          #设置磁盘空间阈值 单位GB（需要qBittorrent Web API 版本大于 v2.1.1 具体是从哪个版本开始的不清楚）  v0.1.3新增
          #设置了该值后 当磁盘剩余空间低于配置的阈值时才会执行删除 并且当预计删除的种子删除后剩余空间大于阈值 则会放弃继续删除 实现尽可能多做种
          #可配合sort对种子排序 例如 last_activity 实现优先从 最后活动时间（有上传下载流量）最久的种子删起
          #注意：如果经过过滤器后 找不到任何匹配的种子 即使设置了该值 也不会删除
          #推荐最低设置为 下载速度*删除任务时间间隔*2 
          #例如 峰值下载速度：12.5MB/S 删除任务时间间隔：10 min 则最小应该设置为：12.5*60*10/1024=15
          keep_disk_space: 20

  #输入模板 从qbittorrent获取数据
  from_qbittorrent_template:
    from_qbittorrent_mod:
      host: qbittorrent.example.com
      port: 443
      use_ssl: true
      username: admin
      password: 123456789xx

schedules:
  #每分钟执行 pt1, pt2
  - tasks: [pt1, pt2]
    interval:
      minutes: 1

  #每隔10分钟执行 resume, delete, modify
  - tasks: [resume, delete, modify]
    interval:
      minutes: 10

  #每隔1小时执行 reseed
  - tasks: [reseed]
    interval:
      hours: 1

#任务列表
tasks:
  pt1:
    #官方插件：rss 订阅链接
    rss: https://pt1.com/rss
    #官方插件：regexp 过滤器 接受带有 CCTV 字样的种子
    regexp:
      accept:
        - CCTV
      from: title
    #基础+添加种子（模板配置会自动合并）
    template: 
      - qbittorrent_base_template
      - qbittorrent_add_template
  
  pt2:
    rss: https://pt1.com/rss
    #官方插件：accept_all 过滤器 接受全部
    accept_all: yes
    template:
      - qbittorrent_base_template
      - qbittorrent_add_template    

  #自动辅种 使用 IYUU 提供的接口
  reseed:
    iyuu_auto_reseed:
      #IYUU token 获取方法请查阅顶部介绍的 IYUUAutoReseed 项目
      iyuu: xxxxxxxxxxxxxxxxxxxx
      #站点密钥
      passkeys:
        #key: 站点域名包含字符串 value:密钥
        #例 pt123.xyz
        pt123: xxxxxxxxxxxxxxxxxxxx
        # abc456.cn
        abc456: xxxxxxxxxxxxxxxxxxxx
      #获取辅种数据的客户端
      qbittorrent_ressed:
        host: qbittorrent.example.com
        port: 443
        use_ssl: true
        username: admin
        password: 123456789xx
    accept_all: yes
    template:
      - qbittorrent_base_template
      - qbittorrent_add_template

  #修改种子信息
  modify:
    disable: [seen, seen_info_hash]
    accept_all: yes
    #使用修改模板
    template:
      - from_qbittorrent_template
      - qbittorrent_base_template
      - qbittorrent_modify_template  

  #自动删种
  delete:
    #官方插件：disable 关闭任务记录 
    disable: [seen, seen_info_hash]
    #官方插件： if 过滤器
    if:
      #参考entry属性列表
      #种子在 Rss分类 并且 最后活动时间 < 2天 
      - qbittorrent_category in ['Rss'] and qbittorrent_last_activity < now - timedelta(days=2): accept
      #种子数据丢失 或者 （种子处于未完成的暂停状态 并且 下载大小为0）：一般是辅助失败的种子 
      - qbittorrent_state == 'missingFiles' or (qbittorrent_state in ['pausedDL'] and qbittorrent_downloaded == 0): accept
    #官方sort_by插件：按最后活动时间从早到晚排序 优先删除
    sort_by: qbittorrent_last_activity
    #使用输入模板 从qbittorrent获取数据
    #使用自动删种模板
    template:
      - from_qbittorrent_template
      - qbittorrent_base_template      
      - qbittorrent_delete_template

  #自动开始
  resume:
    disable: [seen, seen_info_hash]
    if:
      #选择暂停状态已完成的种子
      - qbittorrent_state == 'pausedUP': accept
    #使用输入模板 从qbittorrent获取数据
    #使用自动开始模板
    template:
      - from_qbittorrent_template
      - qbittorrent_base_template
      - qbittorrent_resume_template
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
 
 
### entry属性列表

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

### qbittorrent_state 可能返回的值:

|Value|Description
-|-
|error|Some error occurred, applies to paused torrents
|missingFiles|Torrent data files is missing
|uploading|Torrent is being seeded and data is being transferred
|pausedUP|Torrent is paused and has finished downloading
|queuedUP|Queuing is enabled and torrent is queued for upload
|stalledUP|Torrent is being seeded, but no connection were made
|checkingUP|Torrent has finished downloading and is being checked
|forcedUP|Torrent is forced to uploading and ignore queue limit
|allocating|Torrent is allocating disk space for download
|downloading|Torrent is being downloaded and data is being transferred
|metaDL|Torrent has just started downloading and is fetching metadata
|pausedDL|Torrent is paused and has NOT finished downloading
|queuedDL|Queuing is enabled and torrent is queued for download
|stalledDL|Torrent is being downloaded, but no connection were made
|checkingDL|Same as checkingUP, but torrent has NOT finished downloading
|forceDL|Torrent is forced to downloading to ignore queue limit
|checkingResumeData|Checking resume data on qBt startup
|moving|Torrent is moving to another location
|unknown|Unknown status