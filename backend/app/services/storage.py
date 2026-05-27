from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from app.config import get_settings


class Storage:
    def __init__(self, db_path: Path | None = None) -> None:
        settings = get_settings()
        self.db_path = db_path or settings.db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS user_preferences (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS recommendation_history (
                    item_key TEXT PRIMARY KEY,
                    item_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    topic TEXT NOT NULL,
                    query TEXT NOT NULL,
                    source_provider TEXT NOT NULL,
                    source_url TEXT NOT NULL,
                    pdf_url TEXT,
                    score REAL,
                    recommended_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS document_artifacts (
                    artifact_id TEXT PRIMARY KEY,
                    source_path TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    action TEXT NOT NULL,
                    output_path TEXT,
                    output_url TEXT,
                    status TEXT NOT NULL,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            self._migrate_recommendation_history(connection)

    def _migrate_recommendation_history(self, connection: sqlite3.Connection) -> None:
        columns = {
            row[1]
            for row in connection.execute("PRAGMA table_info(recommendation_history)").fetchall()
        }
        if "paper_id" not in columns:
            return
        legacy_rows = connection.execute(
            "SELECT paper_id, title, topic, recommended_at FROM recommendation_history"
        ).fetchall()
        connection.execute("DROP TABLE recommendation_history")
        connection.execute(
            """
            CREATE TABLE recommendation_history (
                item_key TEXT PRIMARY KEY,
                item_type TEXT NOT NULL,
                title TEXT NOT NULL,
                topic TEXT NOT NULL,
                query TEXT NOT NULL,
                source_provider TEXT NOT NULL,
                source_url TEXT NOT NULL,
                pdf_url TEXT,
                score REAL,
                recommended_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.executemany(
            "INSERT INTO recommendation_history(item_key, item_type, title, topic, query, source_provider, source_url, pdf_url, score, recommended_at) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    paper_id,
                    "paper",
                    title,
                    topic,
                    topic,
                    "legacy",
                    f"https://example.com/{paper_id}",
                    None,
                    None,
                    recommended_at,
                )
                for paper_id, title, topic, recommended_at in legacy_rows
            ],
        )

    def get_preferences(self) -> dict[str, str]:
        with self._connect() as connection:
            rows = connection.execute("SELECT key, value FROM user_preferences").fetchall()
        return {key: value for key, value in rows}

    def set_preference(self, key: str, value: str) -> None:
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO user_preferences(key, value) VALUES(?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, value),
            )

    def delete_preference(self, key: str) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM user_preferences WHERE key = ?", (key,))

    def get_model_provider_value(self, provider: str, field: str) -> str | None:
        return self.get_preferences().get(f"model.{provider}.{field}")

    def set_model_provider_value(self, provider: str, field: str, value: str) -> None:
        self.set_preference(f"model.{provider}.{field}", value)

    def clear_model_provider_value(self, provider: str, field: str) -> None:
        self.delete_preference(f"model.{provider}.{field}")

    def get_model_api_key(self, provider: str) -> str | None:
        return self.get_model_provider_value(provider, "api_key")

    def set_model_api_key(self, provider: str, api_key: str) -> None:
        self.set_model_provider_value(provider, "api_key", api_key)

    def clear_model_api_key(self, provider: str) -> None:
        self.clear_model_provider_value(provider, "api_key")

    def get_model_base_url(self, provider: str) -> str | None:
        return self.get_model_provider_value(provider, "base_url")

    def set_model_base_url(self, provider: str, base_url: str) -> None:
        self.set_model_provider_value(provider, "base_url", base_url)

    def clear_model_base_url(self, provider: str) -> None:
        self.clear_model_provider_value(provider, "base_url")

    def has_recommended(self, item_key: str) -> bool:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT 1 FROM recommendation_history WHERE item_key = ?",
                (item_key,),
            ).fetchone()
        return row is not None

    def list_recommended_keys(self) -> set[str]:
        with self._connect() as connection:
            rows = connection.execute("SELECT item_key FROM recommendation_history").fetchall()
        return {item_key for (item_key,) in rows}

    def save_recommendation(self, recommendation: dict[str, Any], *, query: str, topic: str) -> None:
        with self._connect() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO recommendation_history(item_key, item_type, title, topic, query, source_provider, source_url, pdf_url, score) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    recommendation["item_key"],
                    recommendation["kind"],
                    recommendation["title"],
                    topic,
                    query,
                    recommendation["source_provider"],
                    recommendation["source_url"],
                    recommendation.get("pdf_url"),
                    recommendation.get("score"),
                ),
            )

    def list_recommendations(self) -> list[dict[str, str]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT item_key, title, topic, item_type FROM recommendation_history ORDER BY recommended_at DESC"
            ).fetchall()
        return [
            {"item_key": item_key, "title": title, "topic": topic, "item_type": item_type}
            for item_key, title, topic, item_type in rows
        ]

    def save_document_artifact(
        self,
        *,
        artifact_id: str,
        source_path: str,
        source_type: str,
        action: str,
        output_path: str | None,
        output_url: str | None,
        status: str,
        error_message: str | None = None,
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO document_artifacts(artifact_id, source_path, source_type, action, output_path, output_url, status, error_message) VALUES(?, ?, ?, ?, ?, ?, ?, ?)",
                (artifact_id, source_path, source_type, action, output_path, output_url, status, error_message),
            )
