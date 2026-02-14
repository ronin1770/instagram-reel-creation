"""Shared queue names for ARQ workers."""

from __future__ import annotations

from arq.constants import health_check_key_suffix

VIDEO_QUEUE_NAME = "arq:queue:video"
AI_QUEUE_NAME = "arq:queue:ai"
POST_QUEUE_NAME = "arq:queue:post"


def queue_health_key(queue_name: str) -> str:
    return f"{queue_name}{health_check_key_suffix}"
