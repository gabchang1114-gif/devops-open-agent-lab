"""SQLite storage for PR review history."""

from __future__ import annotations

import asyncio
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from loguru import logger


class PrReviewStore:
    """SQLite-backed PR review history store."""

    def __init__(self, database_path: str) -> None:
        self.database_path = database_path

    async def initialize(self) -> None:
        await asyncio.to_thread(self._initialize_sync)

    def _connect(self) -> sqlite3.Connection:
        Path(self.database_path).parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.database_path, check_same_thread=False)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize_sync(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS pr_reviews (
                    id TEXT PRIMARY KEY,
                    agent_type TEXT NOT NULL DEFAULT 'pr_reviewer',
                    owner TEXT NOT NULL,
                    repository TEXT NOT NULL,
                    pull_request_number INTEGER NOT NULL,
                    pull_request_title TEXT,
                    pull_request_author TEXT,
                    base_branch TEXT,
                    head_branch TEXT,
                    commit_sha TEXT,
                    overall_risk TEXT,
                    findings_count INTEGER NOT NULL DEFAULT 0,
                    final_recommendation TEXT,
                    status TEXT NOT NULL,
                    current_step TEXT,
                    progress_percentage INTEGER NOT NULL DEFAULT 0,
                    review_markdown TEXT,
                    review_json TEXT,
                    github_comment_url TEXT,
                    error TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            connection.commit()
            self._ensure_schema(connection)
        logger.info("PR review store initialized | path={}", self.database_path)

    def _ensure_schema(self, connection: sqlite3.Connection) -> None:
        columns = {
            row[1] for row in connection.execute("PRAGMA table_info(pr_reviews)").fetchall()
        }
        if "user_id" not in columns:
            connection.execute("ALTER TABLE pr_reviews ADD COLUMN user_id TEXT")
            connection.commit()

    @staticmethod
    def utc_now() -> str:
        return datetime.now(timezone.utc).isoformat()

    async def create(
        self,
        owner: str,
        repository: str,
        pull_request_number: int,
        user_id: str | None = None,
    ) -> str:
        return await asyncio.to_thread(
            self._create_sync,
            owner,
            repository,
            pull_request_number,
            user_id,
        )

    def _create_sync(
        self,
        owner: str,
        repository: str,
        pull_request_number: int,
        user_id: str | None = None,
    ) -> str:
        review_id = str(uuid.uuid4())
        now = self.utc_now()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO pr_reviews (
                    id, owner, repository, pull_request_number, status, current_step,
                    progress_percentage, user_id, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    review_id,
                    owner,
                    repository,
                    pull_request_number,
                    "queued",
                    "queued",
                    0,
                    user_id,
                    now,
                    now,
                ),
            )
            connection.commit()
        return review_id

    async def update_progress(
        self,
        review_id: str,
        *,
        status: str,
        current_step: str | None = None,
        progress_percentage: int = 0,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        await asyncio.to_thread(
            self._update_progress_sync,
            review_id,
            status,
            current_step,
            progress_percentage,
            metadata,
        )

    def _update_progress_sync(
        self,
        review_id: str,
        status: str,
        current_step: str | None,
        progress_percentage: int,
        metadata: dict[str, Any] | None,
    ) -> None:
        fields = ["status = ?", "progress_percentage = ?", "updated_at = ?"]
        values: list[Any] = [status, progress_percentage, self.utc_now()]
        if current_step is not None:
            fields.insert(1, "current_step = ?")
            values.insert(1, current_step)
        if metadata:
            for key, column in {
                "pull_request_title": "pull_request_title",
                "pull_request_author": "pull_request_author",
                "base_branch": "base_branch",
                "head_branch": "head_branch",
                "commit_sha": "commit_sha",
            }.items():
                if key in metadata and metadata[key] is not None:
                    fields.append(f"{column} = ?")
                    values.append(metadata[key])
        values.append(review_id)
        with self._connect() as connection:
            connection.execute(
                f"UPDATE pr_reviews SET {', '.join(fields)} WHERE id = ?",
                values,
            )
            connection.commit()

    async def complete(
        self,
        review_id: str,
        *,
        review_markdown: str,
        review_json: dict[str, Any],
        overall_risk: str,
        findings_count: int,
        final_recommendation: str,
        github_comment_url: str | None = None,
    ) -> None:
        await asyncio.to_thread(
            self._complete_sync,
            review_id,
            review_markdown,
            review_json,
            overall_risk,
            findings_count,
            final_recommendation,
            github_comment_url,
        )

    def _complete_sync(
        self,
        review_id: str,
        review_markdown: str,
        review_json: dict[str, Any],
        overall_risk: str,
        findings_count: int,
        final_recommendation: str,
        github_comment_url: str | None,
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE pr_reviews
                SET status = ?, current_step = ?, progress_percentage = ?,
                    review_markdown = ?, review_json = ?, overall_risk = ?,
                    findings_count = ?, final_recommendation = ?,
                    github_comment_url = ?, error = NULL, updated_at = ?
                WHERE id = ?
                """,
                (
                    "completed",
                    "completed",
                    100,
                    review_markdown,
                    json.dumps(review_json),
                    overall_risk,
                    findings_count,
                    final_recommendation,
                    github_comment_url,
                    self.utc_now(),
                    review_id,
                ),
            )
            connection.commit()

    async def fail(self, review_id: str, error: str) -> None:
        await asyncio.to_thread(self._fail_sync, review_id, error)

    def _fail_sync(self, review_id: str, error: str) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE pr_reviews
                SET status = ?, error = ?, progress_percentage = ?, updated_at = ?
                WHERE id = ?
                """,
                ("failed", error, 100, self.utc_now(), review_id),
            )
            connection.commit()

    async def get(self, review_id: str) -> dict[str, Any] | None:
        return await asyncio.to_thread(self._get_sync, review_id)

    def _get_sync(self, review_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM pr_reviews WHERE id = ?",
                (review_id,),
            ).fetchone()
            if not row:
                return None
            data = dict(row)
            if data.get("review_json"):
                data["review"] = json.loads(data["review_json"])
            return data

    async def list_history(self, limit: int = 50) -> list[dict[str, Any]]:
        return await asyncio.to_thread(self._list_history_sync, limit)

    def _list_history_sync(self, limit: int) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, owner, repository, pull_request_number, pull_request_title,
                       overall_risk, findings_count, final_recommendation, status,
                       created_at, commit_sha
                FROM pr_reviews
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
            return [dict(row) for row in rows]
