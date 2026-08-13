# SakuraMedia JavDB 排行榜插件

为 SakuraMedia（SakuraMediaBE）提供 JavDB 排行榜来源，宿主不再内置榜单，
本插件通过 `discovery.ranking_source` 扩展点声明 `source_key="javdb"` 的
6 个榜单，并注册定时同步任务。

## 契约版本

- 宿主契约：`host_api_version=1`，对应宿主 commit `6ebc9f3`
  （排行榜历史清空并下放账号到插件）。
- 插件目录名必须等于 `plugin_id`（`sakuramedia_javdb_ranking`），
  宿主 `plugins check` 与安装均按目录名解析。

## 安装

方式一：目录直接拷贝/挂载到 `/data/plugins/sakuramedia_javdb_ranking/`。

方式二：zip 安装（插件根内容打 zip，不含外层目录）：

```bash
cd sakuramedia_javdb_ranking
zip -r ../sakuramedia_javdb_ranking-0.1.0.zip . \
  -x '.git/*' -x 'tests/*' -x '__pycache__/*' -x '.venv/*' \
  -x '.pytest_cache/*' -x 'data/*'
```

然后在宿主仓库：

```bash
uv run python -m src.start.commands plugins install ../sakuramedia_javdb_ranking-0.1.0.zip
uv run python -m src.start.commands plugins enable sakuramedia_javdb_ranking
```

最后重启 api 与 aps 两个进程。

## 配置

```toml
[plugins]
enabled = ["sakuramedia_javdb_ranking"]

[plugins.settings.sakuramedia_javdb_ranking]
javdb_username = "..."
javdb_password = "..."
```

账号仅 TOP250 需要：不配置时 TOP250 整榜跳过（`should_fetch` 返回 False），
其余五个免费榜照常同步；配置后登录失败按普通 target 失败计入 `failed_targets`。
每次任务运行开始时新建 provider（运行内复用），登录失败只影响当次运行，
下次运行会自动重试，无需重启进程。

定时节奏沿用宿主原内置任务的 `45 1 * * *`，可用 `plugins.job_crons` 覆盖：

```toml
[plugins.job_crons.sakuramedia_javdb_ranking]
sakuramedia_javdb_ranking_sync = "15 3 * * *"
```

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
  （`aps sync-javdb-ranking`），全量同步。
- 手动任务：`sakuramedia_javdb_ranking_sync_board`
  （`aps sync-javdb-ranking-board`），参数 `board_key` / `period`，
  可经任务中心 HTTP 手动触发。

## 开发与测试

插件复用宿主 venv 与宿主 `src`（运行 pytest 时通过 `tests/conftest.py`
把 `../SakuraMediaBE/src` 加入 `sys.path`）：

```bash
../SakuraMediaBE/.venv/bin/python -m pytest -q
```

宿主侧契约冒烟：

```bash
cd ../SakuraMediaBE
uv run python -m src.start.commands plugins check ../sakuramedia_javdb_ranking
```
