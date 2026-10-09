# SakuraMedia JavDB 排行榜插件

为 SakuraMedia（SakuraMediaBE）提供 JavDB 排行榜来源，宿主不再内置榜单，
本插件通过 `discovery.ranking_source` 扩展点声明 `source_key="javdb"` 的
6 个榜单，并注册定时同步任务。

## 安装

通过前端插件管理页上传 zip 安装（系统设置 → 插件）：

1. 打开 SakuraMedia 客户端，进入「系统设置 → 插件」；
2. 点击「安装插件」，选择 zip 包上传；安装后插件默认自动启用；
3. 重启 api 与 aps（或重启容器）。

zip 包要求：插件根内容直接打 zip，不含外层目录，根目录须包含 `manifest.json`。
重新上传同 `plugin_id` 的 zip 会替换代码并保留插件 `data/` 运行数据。

## 配置

在插件管理页（系统设置 → 插件）点击本插件行，通过配置表单编辑并保存。配置对象示例：

```json
{
  "javdb_username": "",
  "javdb_password": ""
}
```

保存后需重启 api 与 aps（或整个容器）才生效。

账号仅 TOP250 需要：不配置时 TOP250 整榜跳过（`should_fetch` 返回 False），
其余五个免费榜照常同步；

## 榜单

| board | 周期 | 说明 |
|---|---|---|
| `playback_all` | daily/weekly/monthly | 热播榜 |
| `playback_high_score` | daily/weekly/monthly | 高评分榜 |
| `censored` | daily/weekly/monthly | 有码 |
| `uncensored` | daily/weekly/monthly | 无码 |
| `fc2` | daily/weekly/monthly | FC2 |
| `top250` | all/uncensored/censored/fc2 + 当前年..2008 | 需账号；历史年份已有数据不重抓 |

## 任务

- 定时任务：`sakuramedia_javdb_ranking_sync`
  （`aps sync-javdb-ranking`），全量同步，默认每天 01:45。
- 手动任务：`sakuramedia_javdb_ranking_sync_board`
  （`aps sync-javdb-ranking-board`），参数 `board_key` / `period` 均必填，
  可经任务中心 HTTP 手动触发。
  任务中心表单中两者为中文下拉选择，`period` 选项随 `board_key` 联动；
  CLI/HTTP 直接调用时取值：`playback_all`（热播）/ `playback_high_score`（高评分）/
  `censored`（有码）/ `uncensored`（无码）/ `fc2`（FC2）支持
  `daily`（日榜）/ `weekly`（周榜）/ `monthly`（月榜）；
  `top250`（TOP250）支持 `all`（全部）/ `uncensored`（无码）/ `censored`（有码）/
  `fc2`（FC2）及年份（如 `2025`）。
