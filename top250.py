"""打包在插件内的 JavDB TOP250 番号数据。

TOP250 API 需要登录，因此这里只保存一次性抓取后的静态番号列表。
"""

from __future__ import annotations

import json
from pathlib import Path

_DATA_PATH = Path(__file__).with_name("top250.json")
_DATA = json.loads(_DATA_PATH.read_text(encoding="utf-8"))
TOP250_FETCHED_AT: str | None = _DATA.get("fetched_at")
TOP250_PERIODS: tuple[str, ...] = tuple(_DATA["periods"])


def top250_periods() -> tuple[str, ...]:
    return TOP250_PERIODS


def top250_numbers(period: str) -> list[str]:
    periods = _DATA["periods"]
    if period not in periods:
        raise ValueError(f"unsupported top250 period: {period}")
    numbers = periods[period]
    if not isinstance(numbers, list) or not all(
        isinstance(number, str) and number for number in numbers
    ):
        raise ValueError(f"invalid top250 number list: period={period}")
    return list(numbers)
