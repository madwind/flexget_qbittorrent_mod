# flexget_qbittorrent_mod

**为qBittorrent用户打造的FlexGet插件,支持删种/辅种/筛选免费种子/自动签到等功能**

---

## 前言

这原本是一个 Flexget 的 qBittorrent插件，因为懒得开新项目，已经变成大杂烩了

这个大杂烩是为了实现我自己需求的全自动化，只为能用就好，并没有想着朝简单易用的方向发展。

## 类似项目

> 如果以下项目已经完全够用了，就不需要往下看了，PT吧内有很详尽的教程。**用复杂的方式解决简单的需求并不值得。**

- 辅种: [ledccn/IYUUAutoReseed](https://github.com/ledccn/IYUUAutoReseed)
- 删种: [jerrymakesjelly/autoremove-torrents](https://github.com/jerrymakesjelly/autoremove-torrents)
- 筛选免费种子: [Juszoe/flexget-nexusphp](https://github.com/Juszoe/flexget-nexusphp)
- 自动签到: [binux/qiandao](https://github.com/binux/qiandao)

## 功能

- [下载、修改、删除种子，动态调整连接数](https://github.com/IvonWei/flexget_qbittorrent_mod/wiki/qbittorrent_mod)
- [获取qbittorrent状态、种子列表](https://github.com/IvonWei/flexget_qbittorrent_mod/wiki/from_qbittorrent)
- [自动辅种](https://github.com/IvonWei/flexget_qbittorrent_mod/wiki/iyuu_auto_reseed)
- [自动签到、统计](https://github.com/IvonWei/flexget_qbittorrent_mod/wiki/auto_sign_in)
- [消息推送](https://github.com/IvonWei/flexget_qbittorrent_mod/wiki/wecom)

## 提问须知

> 对插件使用有任何疑问以及建议，或者汇报本程序的任何Bug 欢迎使用以下联系方式和我们交流

<details>
  <summary>联系方式</summary>

- [Telegram群聊](https://t.me/flexget_qbittorrent_mod)
- QQ群: 1128215750

口令: 115599
</details>


但是 在提问前你需要了解以下知识

- 基础的 [yaml](https://www.runoob.com/w3cnote/yaml-intro.html) 语法知识
- 了解FlexGet订阅的基础用法
- 清楚自己需要什么功能
- 已经完整阅读 [Wiki](https://github.com/IvonWei/flexget_qbittorrent_mod/wiki)

## 开发与测试

站点实现位于 `ptsites/trackers/`，公共站点框架位于 `ptsites/schema/` 和 `ptsites/base/`。

安装开发依赖并运行离线测试：

```powershell
python -m pip install -e ".[dev]"
python -m pytest
```

真实站点签到测试默认不会运行。需要显式提供本地环境变量，并添加集成测试参数：

```powershell
$env:PT_TEST_SITE = "tracker-name"
$env:PT_TEST_COOKIE = "your-local-cookie"
python -m pytest --run-integration tests/integration/test_sign_in.py
```

需要登录配置而不是单一 Cookie 时，可使用 `PT_TEST_SITE_CONFIG` 提供 JSON 对象。凭据不要写入测试源码。

构建可复制到 FlexGet 插件目录的发布文件：

```powershell
.\scripts\build_dist.ps1
```
