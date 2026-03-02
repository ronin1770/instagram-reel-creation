"""Enqueue post worker jobs for pending raw posts."""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path
from typing import Union

from arq import create_pool
from arq.connections import RedisSettings
from dotenv import find_dotenv, load_dotenv

# Allow running this file directly: `python backend/scripts/enque_post_jobs.py ...`
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.append(str(REPO_ROOT))

from backend.db import close_client, get_db
from backend.models.raw_posts_data import RAW_POSTS_COLLECTION
from backend.workers.queue_names import POST_QUEUE_NAME

REDIS_URL = "redis://localhost:6379/0"


def _num_jobs_arg(value: str) -> Union[str, int]:
    normalized = value.strip().lower()
    if normalized == "all":
        return "all"

    try:
        parsed = int(normalized)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "num_jobs must be 'all' or a positive integer."
        ) from exc

    if parsed <= 0:
        raise argparse.ArgumentTypeError("num_jobs integer value must be > 0.")
    return parsed


def _pending_posts_count() -> int:
    db = get_db()
    return db[RAW_POSTS_COLLECTION].count_documents({"quote_created": False})


def _requested_job_count(num_jobs: Union[str, int], pending_count: int) -> int:
    if num_jobs == "all":
        return pending_count
    return min(num_jobs, pending_count)


async def _enqueue_jobs(job_count: int, redis_url: str) -> list[str]:
    redis = await create_pool(RedisSettings.from_dsn(redis_url))
    job_ids: list[str] = []
    try:
        for _ in range(job_count):
            job = await redis.enqueue_job(
                "process_posts",
                _queue_name=POST_QUEUE_NAME,
            )
            if job is None:
                raise RuntimeError(
                    f"enqueue_job returned None after enqueuing {len(job_ids)} jobs."
                )
            job_ids.append(job.job_id)
    finally:
        await redis.close()
    return job_ids


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Enqueue process_posts jobs for pending raw posts (quote_created=false)."
        )
    )
    parser.add_argument(
        "num_jobs",
        type=_num_jobs_arg,
        help="Use 'all' or a positive integer.",
    )
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    load_dotenv(find_dotenv())
    redis_url = os.getenv("REDIS_URL", REDIS_URL)

    try:
        pending_count = _pending_posts_count()
        requested = _requested_job_count(args.num_jobs, pending_count)

        if requested == 0:
            print("No pending posts found. enqueued=0")
            return 0

        job_ids = asyncio.run(_enqueue_jobs(requested, redis_url))
        print(
            "Enqueue summary:"
            f" pending={pending_count},"
            f" requested={args.num_jobs},"
            f" enqueued={len(job_ids)}"
        )
        print("Job IDs:", ", ".join(job_ids))
        return 0
    except Exception as exc:
        print(f"Failed to enqueue jobs: {exc}", file=sys.stderr)
        return 1
    finally:
        close_client()


if __name__ == "__main__":
    raise SystemExit(main())
