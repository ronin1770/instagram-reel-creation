"""Structured application logging backed by a Redis Stream."""

from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

from redis import Redis

LOG_STREAM_KEY = "reelquick:system:logs"
LOG_STREAM_MAXLEN = 5_000
DEFAULT_ENVIRONMENT = "development"
SENSITIVE_KEY_PATTERN = re.compile(
    r"(?:authorization|cookie|password|secret|token|api[_-]?key)", re.IGNORECASE
)
SENSITIVE_VALUE_PATTERN = re.compile(
    r"(?i)(?:bearer\s+|(?:api[_-]?key|password|secret|token)\s*[=:]\s*)[^\s,;]+"
)
STANDARD_LOG_RECORD_KEYS = set(logging.LogRecord("", 0, "", 0, "", (), None).__dict__)
STRUCTURED_CONTEXT_KEYS = ("job_id", "video_id", "request_id", "metadata")


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _sanitize_value(value: Any, *, key: Optional[str] = None) -> Any:
    if key and SENSITIVE_KEY_PATTERN.search(key):
        return "[REDACTED]"
    if isinstance(value, Mapping):
        return {
            str(item_key): _sanitize_value(item_value, key=str(item_key))
            for item_key, item_value in value.items()
        }
    if isinstance(value, (list, tuple, set)):
        return [_sanitize_value(item) for item in value]
    if isinstance(value, str):
        return SENSITIVE_VALUE_PATTERN.sub("[REDACTED]", value)
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return str(value)


def _decode_stream_event(stream_id: str, fields: Mapping[Any, Any]) -> Dict[str, Any]:
    raw_event = fields.get("event") or fields.get(b"event")
    if isinstance(raw_event, bytes):
        raw_event = raw_event.decode("utf-8", errors="replace")
    if not raw_event:
        return {"id": stream_id, "message": "Malformed log event"}

    try:
        event = json.loads(raw_event)
    except (TypeError, json.JSONDecodeError):
        return {"id": stream_id, "message": "Malformed log event"}
    if not isinstance(event, dict):
        return {"id": stream_id, "message": "Malformed log event"}
    return {"id": stream_id, **event}


class RedisStreamHandler(logging.Handler):
    """Write structured log records to Redis without disrupting normal logging."""

    def __init__(
        self,
        *,
        service: str,
        redis_url: Optional[str] = None,
        environment: Optional[str] = None,
    ) -> None:
        super().__init__()
        self.service = service
        self.redis_url = redis_url
        self.environment = environment
        self._client: Optional[Redis] = None
        self._client_url: Optional[str] = None

    def _resolve_redis_url(self) -> str:
        return self.redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")

    def _create_client(self, redis_url: str) -> Redis:
        return Redis.from_url(
            redis_url,
            decode_responses=True,
            socket_connect_timeout=1,
            socket_timeout=1,
        )

    def _get_client(self) -> Redis:
        redis_url = self._resolve_redis_url()
        if self._client is None or self._client_url != redis_url:
            self._close_client()
            self._client = self._create_client(redis_url)
            self._client_url = redis_url
        return self._client

    def _close_client(self) -> None:
        client = self._client
        self._client = None
        self._client_url = None
        if client is not None:
            try:
                client.close()
            except Exception:
                pass

    def _write_event(self, event: Dict[str, Any]) -> None:
        self._get_client().xadd(
            LOG_STREAM_KEY,
            {"event": json.dumps(event, default=str, separators=(",", ":"))},
            maxlen=LOG_STREAM_MAXLEN,
            approximate=True,
        )

    def emit(self, record: logging.LogRecord) -> None:
        event = self._build_event(record)
        try:
            self._write_event(event)
        except Exception:
            self._close_client()
            try:
                # Retry once after reconnecting to survive Redis restarts and stale sockets.
                self._write_event(event)
            except Exception:
                # Observability must never take down the request or worker that emitted it.
                self._close_client()

    def _build_event(self, record: logging.LogRecord) -> Dict[str, Any]:
        event: Dict[str, Any] = {
            "timestamp": _utc_timestamp(),
            "level": record.levelname,
            "service": self.service,
            "source": "python",
            "environment": self.environment
            or os.getenv("APP_ENV", DEFAULT_ENVIRONMENT),
            "message": _sanitize_value(record.getMessage()),
        }
        for key in STRUCTURED_CONTEXT_KEYS:
            value = getattr(record, key, None)
            if value is not None:
                event[key] = _sanitize_value(value, key=key)

        extra_metadata = {
            key: value
            for key, value in record.__dict__.items()
            if key not in STANDARD_LOG_RECORD_KEYS and key not in STRUCTURED_CONTEXT_KEYS
        }
        if extra_metadata:
            event["metadata"] = _sanitize_value(extra_metadata)

        if record.exc_info:
            formatter = logging.Formatter()
            event["exception"] = _sanitize_value(formatter.formatException(record.exc_info))
        return event


def get_recent_log_events(limit: int) -> List[Dict[str, Any]]:
    """Return the newest Redis Stream events in chronological order."""
    client = Redis.from_url(
        os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        decode_responses=True,
        socket_connect_timeout=1,
        socket_timeout=2,
    )
    entries = client.xrevrange(LOG_STREAM_KEY, max="+", min="-", count=limit)
    return [_decode_stream_event(stream_id, fields) for stream_id, fields in reversed(entries)]


def read_log_events(
    last_event_id: str,
    *,
    block_ms: int = 15_000,
) -> List[Dict[str, Any]]:
    """Block briefly for entries after ``last_event_id`` and decode them."""
    client = Redis.from_url(
        os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        decode_responses=True,
        socket_connect_timeout=1,
        socket_timeout=(block_ms / 1000) + 2,
    )
    streams: Iterable[Tuple[str, List[Tuple[str, Mapping[Any, Any]]]]] = client.xread(
        {LOG_STREAM_KEY: last_event_id},
        block=block_ms,
        count=100,
    )
    events: List[Dict[str, Any]] = []
    for _, entries in streams:
        events.extend(_decode_stream_event(stream_id, fields) for stream_id, fields in entries)
    return events
