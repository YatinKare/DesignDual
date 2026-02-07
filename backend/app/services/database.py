"""Database connection helpers for FastAPI routes."""

from __future__ import annotations

import os
from typing import AsyncIterator

import aiosqlite

from app.db import DEFAULT_DATABASE_URL, resolve_database_path


def _database_url() -> str:
    return os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)


async def get_db_connection() -> aiosqlite.Connection:
    path = resolve_database_path(_database_url())
    connection = await aiosqlite.connect(path)
    connection.row_factory = aiosqlite.Row
    await connection.execute("PRAGMA foreign_keys = ON")
    return connection


async def db_connection() -> AsyncIterator[aiosqlite.Connection]:
    connection = await get_db_connection()
    try:
        yield connection
    finally:
        await connection.close()


__all__ = ["db_connection", "get_db_connection"]
