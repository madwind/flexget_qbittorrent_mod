## flexget_qbittorrent_mod
这原本是一个 Flexget 的 qBittorrent插件，因为懒得开新项目，已经变成大杂烩了

tg: <https://t.me/flexget_qbittorrent_mod>

目前实现的功能有：
- 下载：Rss、爬网页获取种子列表，筛选（爬网页方式可获取Free等信息）后推送到qittorrent下载
- 修改：根据种子的tracker，修改种子的tag，或替换tracker
- 辅种：查询IYUUAutoReseed辅种数据，校验完成后自动开始做种（需在<http://api.iyuu.cn/docs.php?service=App.User.Login&detail=1&type=fold>绑定登陆）
- 删种：符合删除条件后（可根据剩余空间决定删除或放弃，若空间不足，可设置限速），删除包含辅种在内的所有种子
- 自动签到：自动签到，支持答题

参考：

- IYUUAutoReseed：<https://github.com/ledccn/IYUUAutoReseed>

- qBittorrent-Web-API<https://github.com/qbittorrent/qBittorrent/wiki/Web-API-Documentation#api-v20>

### 系统需求
- qBittorrent 4.1.4+
- Flexget 3.0.19+
- Python 3

### 测试环境
- qBittorrent 4.2.2
- Flexget 3.1.46
- Python 3.8

### 安装插件
- 下载插件 [releases](https://github.com/IvonWei/flexget_qbittorrent_mod/releases/latest/download/dist.zip)
- 在Flexget配置文件夹下新建plugins文件夹，例如：
```
~/.flexget/plugins/  # Linux
C:\Users\<YOURUSER>\flexget\plugins\  # Windows
```
- 将所有的 .py 文件解压至plugins
- 若启用了Web-UI或守护进程，则重启flexget重新加载配置
- 从v0.2.5开始删除了templates-> qbittorrent_resume_template-> qbittorrent_mod-> action-> resume-> only_completed项，如果使用旧版本配置，启动报错可以编辑Flexget配置文件夹下的 config.yml 文件手动删除

### 配置模板
更多配置可以学习Flexget官方文档

config_example.yml是我当前正在使用的配置，其中自动签到配置在tasks的最后一段

注：Flexget不允许用中文注释 请用源码里的config.yml对照修改
```yaml
web_server:
  bind: 0.0.0.0
  #web监听端口
  port: 3539

templates:
  #从qBittorrent获取数据
  from_qbittorrent_template:
    from_qbittorrent_mod:
      host: qbittorrent.example.com
      port: 443
      use_ssl: true
      username: admin
      password: 123456789xx

  #基础
  qbittorrent_base_template:
    qbittorrent_mod:
      host: qbittorrent.example.com
      port: 443
      #非https请设置为 no
      use_ssl: yes
      username: admin
      password: 123456789xx

  #添加
  qbittorrent_add_template:
    qbittorrent_mod:
      action:
        add:
          #当当限速低于设定值时 停止添加新任务（限速与当前下载速度无关） v0.2.15新增
          #单位byte（以下示例为 4MiB）
          reject_on_dl_limit: 4194304 
          #参考add可选参数
          #分类
          category: Rss
          #自动管理种子
          autoTMM: true
  
  #修改
  qbittorrent_modify_template:
    qbittorrent_mod:
      action:
        modify:
          #根据tracker添加种子标签 例如以下的tracker会为种子添加 "pt1" 标签 v0.1.3新增
          tag_by_tracker: true
          #批量替换tracker 例如把http替换成https (需要完全匹配) v0.1.3新增
          replace_tracker:
            'http://tracker.pt1.com/announce.php?passkey=xxxxxxxxxxxxxx': 'https://tracker.pt1.com/announce.php?passkey=xxxxxxxxxxxxxx'

  #恢复
  qbittorrent_resume_template:
    qbittorrent_mod:
      action:
        resume:
          #如果保存路径上没有种子在正常做种，则重新校验种子，配合跳检，将种子还原成0进度状态
          recheck_torrents: true

  #删除
  qbittorrent_delete_template:
    qbittorrent_mod:
      action:
        remove:
          #检查所有辅种是否都满足删除条件
          #yes: 只要有其中一个不满足条件则放弃删除
          #no（默认）: 只要有一个满足删除条件 就全部删除 
          #array: 只检查匹配tag的种子，满足就全部删除
          check_reseed:
            - totheglory
            - m-team
            - hdhome
            - open
            - pterclub
          #删种同时是否删除数据
          delete_files: true
          #设置磁盘空间阈值 单位GB（需要qBittorrent 4.14+）  v0.1.3新增
          #设置了该值后 当磁盘剩余空间低于配置的阈值时才会执行删除 并且当预计删除的种子删除后剩余空间大于阈值 则会放弃继续删除 实现尽可能多做种
          #可配合sort对种子排序 例如 last_activity 实现优先从 最后活动时间（有上传下载流量）最久的种子删起
          #注意：如果经过过滤器后 找不到任何匹配的种子 即使设置了该值 也不会删除
          #推荐最低设置为 下载速度*删除任务时间间隔*2 
          #例如 峰值下载速度：12.5MB/S 删除任务时间间隔：10 min 则最小应该设置为：12.5*60*10/1024*2=15
          #单位：GiB 
          keep_disk_space: 10
          #如果删除种子后空间大于keep_disk_space(在第二次运行时检测，防止做了硬链接时只删除一个并没有实际释放空间)，则恢复限速，0为不限速 v0.2.8新增
          #单位：byte
          dl_limit_on_succeeded: 0
          #如执行任务后空间小于keep_disk_space，则自动限速为 (剩余空间 / dl_limit_interval) KiB/s, 不超过dl_limit_on_succeeded, 防止qbittorrent磁盘空间为0后，任务只能下载到99%，需要强制校验
          #默认值为 24*60*60 秒
          #单位：秒
          dl_limit_interval: 1800
          #show_entry: 633645aa28a4aa48e8b7d2ac618fe691e81df30f

schedules:
  - tasks: [xxxx, xxxx, rss_download]
    interval:
      #1分钟
      minutes: 1

  - tasks: [reseed, resume, delete, modify]
    interval:
      minutes: 5

  - tasks: [xxxxx]
    interval:
      minutes: 10

  - tasks: [sign_in]
    interval:
      #1小时
      hours: 1


#任务列表
tasks:
  rss1:
    #官方插件：rss 订阅链接
    rss:
      url: https://pt1.com/rss
      #官方说这样会提高速度
      all_entries: no
    no_entries_ok: yes
    #官方插件：regexp 过滤器 接受带有 CCTV 字样的种子
    regexp:
      accept:
        - CCTV
      from: title
    #基础+添加种子（模板配置会自动合并）
    template: 
      - qbittorrent_base_template
      - qbittorrent_add_template
  
  rss2:
    # 相同过滤条件的rss可以放到一个inputs下
    inputs:
      - rss: https://pt1.com/rss
      - rss: https://pt2.com/rss
    #官方插件：accept_all 过滤器 接受全部
    accept_all: yes
    template:
      - qbittorrent_base_template
      - qbittorrent_add_template    

  pt3:
    #网页获取下载数据 需要有css选择器知识 以下是打开碟片的置顶种子设置
    html_rss:
      url: https://pt3.com/torrents.php
      headers:
        cookie: 'xxxxxxxxxxxxxxxxxx'
        user-agent: 'xxxxxxxxxx'
      #用于下载种子时的附件信息 v0.3.2 修改
      #以 "&" 开头时附加在下载链接之后，否则使用 urljoin 方式拼接
      params: '&passkey=xxxxxxxxxxxxx'
      #组件选择器
      root_element_selector: '#form_torrent > table > tbody > tr.topdown_bg'
      #以下配置基于上面 组件选择器 匹配到的组件做二次匹配
      fields:
        #标题（必选）
        #为 entry 增加 title 属性 值为 匹配到的组件下的 title 属性
        title:
          #二次选择器
          element_selector: 'a[href*="details.php"]'
          #提取属性
          attribute: title
        #链接（必选）
        #为 entry 增加 url 属性 值为 匹配到的组件下的 href 属性
        url:
          element_selector: 'a[href*="download.php"]'
          attribute: href
        #除title url属性为必选，其它可自由添加用于过滤
        #示例 增加促销信息
        #为 entry 增加 promotion 属性 值为 匹配到的组件下的 alt 属性
        promotion:
          element_selector: 'div[style="padding-bottom: 5px"] > img'
          attribute: alt
    no_entries_ok: yes
    #如果promotion带有 Free则接受
    if:
      - promotion in ['Free']: accept
    template: 
      - qbittorrent_base_template
      - qbittorrent_add_template

  #自动辅种 使用 IYUU 提供的接口
  reseed:
    #优先级 1
    priority: 1
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
    #只拒绝相同url的种子
    seen:
      fields:
        - url
    qbittorrent_mod:
      action:
        add:
          #忽略reject_on_dl_limit 始终添加
          reject_on_dl_limit: 0
          #跳过校验
          skip_checking: true
    template:
      - qbittorrent_base_template
      - qbittorrent_add_template

  #自动开始
  resume:
    priority: 2
    disable: [seen, seen_info_hash, retry_failed]
    if:
      #选择进度100%、暂停状态、并且从未下载过数据，1小时内（防止停止任务后又重新开始）添加的的种子
      - qbittorrent_state == 'pausedUP' and qbittorrent_downloaded == 0 and qbittorrent_added_on > now - timedelta(hours=1): accept
    template:
      - from_qbittorrent_template
      - qbittorrent_base_template
      - qbittorrent_resume_template

  #自动删种
  delete:
    priority: 3
    #官方插件：disable 关闭任务记录 失败重试
    disable: [seen, seen_info_hash, retry_failed]
    #官方插件： if 过滤器
    if:
      #参考entry属性列表
      #种子在 Rss分类 并且 最后活动时间 < 2天 
      - qbittorrent_category in ['Rss'] and qbittorrent_last_activity < now - timedelta(days=2): accept
      #种子数据丢失 或者 （种子处于未完成的暂停状态 并且 完成大小为0）：一般是辅助失败的种子
      - qbittorrent_state == 'missingFiles' or (qbittorrent_state in ['pausedDL'] and qbittorrent_completed == 0): accept
      #如种子的tag带有 pt1 并且做种时间小于48小时则拒绝 v0.2.9新增:seeding_time share_ratio属性
      - "'pt1' in qbittorrent_tags and qbittorrent_seeding_time<48*60*60": reject
    #官方sort_by插件：按最后活动时间从早到晚排序 优先删除
    sort_by: qbittorrent_last_activity
   template:
      - from_qbittorrent_template
      - qbittorrent_base_template      
      - qbittorrent_delete_template

  #修改种子信息
  modify:
    priority: 4
    disable: [seen, seen_info_hash, retry_failed]
    accept_all: yes
    template:
      - from_qbittorrent_template
      - qbittorrent_base_template
      - qbittorrent_modify_template  
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
|title | string | Torrent name
|torrent_info_hash | string | Torrent hash
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
|qbittorrent_seeding_time | integer | Torrent elapsed time while complete (seconds)
|qbittorrent_share_ratio | float | Torrent share ratio

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
