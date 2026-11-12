"""匿名 JavDB App API 客户端；只读取免费排行榜，不处理登录。"""

from __future__ import annotations

import hashlib
import time
from typing import Any

import httpx


class JavdbRequestError(RuntimeError):
    def __init__(self, detail: str, *, status_code: int | None = None):
        super().__init__(detail)
        self.status_code = status_code


class JavdbClient:
    API_PATH_RANKINGS = "/api/v1/rankings"
    API_PATH_RANKINGS_PLAYBACK = "/api/v1/rankings/playback"

    SUPPORTED_RANK_VIDEO_TYPES = {"0", "1", "3"}
    SUPPORTED_RANK_PERIODS = {"daily", "weekly", "monthly"}
    SUPPORTED_PLAYBACK_FILTERS = {"all", "high_score"}

    RETRYABLE_STATUS_CODES = {408, 429, 500, 502, 503, 504}
    MD5_SECRET = "71cf27bb3c0bcdf207b64abecddc970098c7421ee7203b9cdae54478478a199e7d5a6e1a57691123c1a931c057842fb73ba3b3c83bcd69c17ccf174081e3d8aa"
    SIGN_PREFIX = '.lpw6vgqzsp.'

    def __init__(
        self,
        *,
        host: str,
        timeout_seconds: float,
        max_retries: int,
        i18n: Any,
        http_client: httpx.Client | None = None,
    ):
        self.host = host
        self.max_retries = max_retries
        self.i18n = i18n
        self._owns_http = http_client is None
        self._http = http_client or httpx.Client(
            timeout=httpx.Timeout(timeout_seconds, connect=min(10.0, timeout_seconds)),
            follow_redirects=True,
        )

    def close(self) -> None:
        if self._owns_http:
            self._http.close()

    def get_rank_numbers(self, *, video_type: str, period: str) -> list[str]:
        if video_type not in self.SUPPORTED_RANK_VIDEO_TYPES:
            raise ValueError(f"unsupported video_type: {video_type}")
        if period not in self.SUPPORTED_RANK_PERIODS:
            raise ValueError(f"unsupported period: {period}")
        return self._get_numbers(
            path=self.API_PATH_RANKINGS,
            params={"type": video_type, "period": period},
        )

    def get_playback_rank_numbers(
        self,
        *,
        filter_by: str,
        period: str,
    ) -> list[str]:
        if filter_by not in self.SUPPORTED_PLAYBACK_FILTERS:
            raise ValueError(f"unsupported filter_by: {filter_by}")
        if period not in self.SUPPORTED_RANK_PERIODS:
            raise ValueError(f"unsupported period: {period}")
        return self._get_numbers(
            path=self.API_PATH_RANKINGS_PLAYBACK,
            params={"filter_by": filter_by, "period": period},
        )

    def _get_numbers(self, *, path: str, params: dict[str, str]) -> list[str]:
        payload = self._request_json(path=path, params=params)
        data = payload.get("data")
        movies = data.get("movies") if isinstance(data, dict) else None
        if not isinstance(movies, list):
            raise JavdbRequestError(
                self.i18n.t(
                    "errors.response_missing_movies",
                    default="JavDB response is missing data.movies",
                )
            )
        return [
            number
            for movie in movies
            if isinstance(movie, dict)
            and isinstance((number := movie.get("number")), str)
            and number
        ]

    def _request_json(
        self,
        *,
        path: str,
        params: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        url = f"https://{self.host}{path}"
        last_detail = "request failed"
        for attempt in range(self.max_retries + 1):
            try:
                response = self._http.get(
                    url,
                    params=params,
                    headers=self._base_headers(),
                )
            except httpx.RequestError as exc:
                last_detail = f"{type(exc).__name__}: {exc}"
                if attempt < self.max_retries:
                    time.sleep(min(8.0, 2**attempt))
                    continue
                raise JavdbRequestError(
                    self.i18n.t(
                        "errors.request_failed",
                        default="JavDB request failed: {detail}",
                        detail=last_detail,
                    )
                ) from exc

            if (
                response.status_code in self.RETRYABLE_STATUS_CODES
                and attempt < self.max_retries
            ):
                if response.status_code == 429:
                    time.sleep(30.0 * (attempt + 1))
                else:
                    time.sleep(min(8.0, 2**attempt))
                continue
            if response.status_code >= 400:
                raise JavdbRequestError(
                    self.i18n.t(
                        "errors.request_failed",
                        default="JavDB request failed: {detail}",
                        detail=f"HTTP {response.status_code}",
                    ),
                    status_code=response.status_code,
                )

            try:
                payload = response.json()
            except ValueError as exc:
                raise JavdbRequestError(
                    self.i18n.t(
                        "errors.request_failed",
                        default="JavDB request failed: {detail}",
                        detail="response body is not valid JSON",
                    )
                ) from exc
            if not isinstance(payload, dict):
                raise JavdbRequestError(
                    self.i18n.t(
                        "errors.request_failed",
                        default="JavDB request failed: {detail}",
                        detail="response is not a JSON object",
                    )
                )
            if payload.get("success") != 1:
                detail = (
                    payload.get("message")
                    or payload.get("action")
                    or f"unexpected success={payload.get('success')}"
                )
                raise JavdbRequestError(
                    self.i18n.t(
                        "errors.request_failed",
                        default="JavDB request failed: {detail}",
                        detail=str(detail),
                    )
                )
            return payload

        raise JavdbRequestError(
            self.i18n.t(
                "errors.request_failed",
                default="JavDB request failed: {detail}",
                detail=last_detail,
            )
        )

    def _base_headers(self) -> dict[str, str]:
        return {
            "connection": "keep-alive",
            "accept-language": "zh-TW",
            "host": self.host,
            "jdsignature": self._sign(),
        }

    def _sign(self) -> str:
        timestamp = int(time.time())
        secret = f"{timestamp}{self.MD5_SECRET}"
        signature = hashlib.md5(secret.encode()).hexdigest()
        return f"{timestamp}{self.SIGN_PREFIX}{signature}"
