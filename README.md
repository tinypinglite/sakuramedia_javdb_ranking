# SakuraMedia JavDB 排行榜插件

为 SakuraMedia（SakuraMediaBE）提供 JavDB 排行榜来源。插件通过
`discovery.ranking_source` 扩展点声明 `source_key="javdb"` 的榜单，并注册定时同步任务。

## 工作方式

- 热播、高评分、有码、无码、FC2 五个免费榜直接请求 JavDB App API，不需要账号登录。
- TOP250 的 App API 需要登录，因此插件不再在运行时登录，而是读取打包在
  `top250.json` 中的静态番号列表。
- 当前静态数据于 2026-11-13 抓取，包含 `all`、`censored`、`uncensored`、`fc2`
  以及 2008–2026 年度榜。
- 运行时不会向 JavDB 发送账号密码，也不需要 Cookie 或登录 token。

TOP250 静态数据不会自动更新；需要更新时，替换插件内的 `top250.json` 后重新安装插件。
免费榜仍然按任务周期正常抓取。

## 安装

通过前端插件管理页上传 zip 安装（系统设置 → 插件）：

1. 打开 SakuraMedia 客户端，进入「系统设置 → 插件」；
2. 点击「安装插件」，选择 zip 包上传；安装后插件默认自动启用；
3. 重启 api 与 aps（或重启容器）。

zip 包要求：插件根内容直接打 zip，不含外层目录，根目录须包含 `manifest.json`。
重新上传同 `plugin_id` 的 zip 会替换代码并保留插件 `data/` 运行数据。

## 配置

- `host`：JavDB API 主机，默认 `jdforrepam.com`，只填域名。
- `timeout_seconds`：单次请求超时，默认 30 秒。
- `max_retries`：网络错误和 429/5xx 的最大重试次数，默认 2。

旧版本保存的 `javdb_username` / `javdb_password` 会被忽略，不再用于任何请求。
升级后在插件配置页保存一次即可让宿主按新模型清理旧字段。

## 榜单

| board | 周期 | 说明 |
|---|---|---|
| `playback_all` | daily/weekly/monthly | 热播榜 |
| `playback_high_score` | daily/weekly/monthly | 高评分榜 |
| `censored` | daily/weekly/monthly | 有码 |
| `uncensored` | daily/weekly/monthly | 无码 |
| `fc2` | daily/weekly/monthly | FC2 |
| `top250` | all/uncensored/censored/fc2 + 2008..2026 | 内置静态番号 |

## 任务

- 定时任务：`sakuramedia_javdb_ranking_sync`
  （`aps sync-javdb-ranking`），全量同步，默认每天 01:45。
- 手动任务：`sakuramedia_javdb_ranking_sync_board`
  （`aps sync-javdb-ranking-board`），参数 `board_key` / `period` 均必填，
  可经任务中心 HTTP 手动触发。

## 多语言

本插件声明 Host API 18，支持 `zh-CN` / `en`。语言包位于
`i18n/zh-CN.json` 和 `i18n/en.json`。

## License

本项目采用 [PolyForm Noncommercial License 1.0.0](./LICENSE)，仅允许非商业用途。

Copyright (C) 2026 tinypinglite
