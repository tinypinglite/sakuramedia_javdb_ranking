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

## 多语言

本插件声明 Host API 12，支持 `zh-CN` / `en`，也是宿主插件 i18n 的样板：

- 语言包放在 `i18n/zh-CN.json`、`i18n/en.json`；`translations.py` 只负责在
  插件导入时读取它们并生成静态 `*_i18n` 字典。
- 插件名：`manifest.json` 的 `display_name_i18n` +
  `PluginRegistration.display_name_i18n`。
- 榜单名：`PluginRankingSource.name_i18n` / `PluginRankingBoard.name_i18n`。
- 任务说明：`JobDefinition.cli_help_i18n`；任务参数 JSON Schema 的
  `title_i18n` / `description_i18n`。
- 设置项标题：Pydantic `Field` 的 `json_schema_extra={"title_i18n": ...}`。
- 运行时文本（任务进度、通知）：`context.i18n.t(key, default=..., **params)`。
- 元数据插件用 `PluginRegistration.display_name_i18n`，媒体 Provider 插件用
  `MediaProviderBundle.display_name_i18n`；两者都是可选字段，缺失时回退原文。
- 新增语言时，在 `i18n/` 增加同名 JSON，并补 manifest / registration 的
  `display_name_i18n`。

## 任务

- 定时任务：`sakuramedia_javdb_ranking_sync`
  （`aps sync-javdb-ranking`），全量同步，默认每天 01:45。
- 手动任务：`sakuramedia_javdb_ranking_sync_board`
  （`aps sync-javdb-ranking-board`），参数 `board_key` / `period` 均必填，
  可经任务中心 HTTP 手动触发。
  任务中心表单按当前界面语言显示下拉标签，`period` 选项随 `board_key` 联动；
  CLI/HTTP 直接调用时取值：`playback_all`（热播）/ `playback_high_score`（高评分）/
  `censored`（有码）/ `uncensored`（无码）/ `fc2`（FC2）支持
  `daily`（日榜）/ `weekly`（周榜）/ `monthly`（月榜）；
  `top250`（TOP250）支持 `all`（全部）/ `uncensored`（无码）/ `censored`（有码）/
  `fc2`（FC2）及年份（如 `2025`）。

## License

本项目采用 [PolyForm Noncommercial License 1.0.0](./LICENSE)，仅允许非商业用途。

Copyright (C) 2026 tinypinglite
