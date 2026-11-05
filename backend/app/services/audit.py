import asyncio
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import delete, insert

from core.config import getSettings
from core.database import SessionLocal
from core.logging import logger
from schemas.models import AuditLog

_MAX_QUEUE_SIZE = 10_000
_BATCH_SIZE = 200
_FLUSH_INTERVAL_SECONDS = 1.0
_PURGE_INTERVAL_SECONDS = 24 * 60 * 60
_MAX_PATH_LENGTH = 512


@dataclass
class AuditEntry:
    user_id: Optional[UUID]
    method: str
    path: str
    status_code: int
    duration_ms: int
    ip_address: Optional[str]
    user_agent: Optional[str]
    request_id: Optional[str]


class AuditLogWriter:
    """
    Writes audit rows in batches on a background task.

    A database write on every request would add latency to each response and tie the
    API's availability to this table. Entries are dropped if the queue fills up, so
    the audit log can have gaps under extreme load, and the drop is logged.
    """

    def __init__(self) -> None:
        self._queue: asyncio.Queue[AuditEntry] = asyncio.Queue(maxsize=_MAX_QUEUE_SIZE)
        self._task: Optional[asyncio.Task] = None
        self._dropped = 0

    def start(self) -> None:
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        if self._task is None:
            return
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        await self._flush(self._drain())

    def record(self, entry: AuditEntry) -> None:
        entry.path = entry.path[:_MAX_PATH_LENGTH]
        try:
            self._queue.put_nowait(entry)
        except asyncio.QueueFull:
            self._dropped += 1
            if self._dropped % 1000 == 1:
                logger.warning("Audit queue full; %s entries dropped", self._dropped)

    def _drain(self) -> list[AuditEntry]:
        batch: list[AuditEntry] = []
        while len(batch) < _BATCH_SIZE and not self._queue.empty():
            batch.append(self._queue.get_nowait())
        return batch

    async def _flush(self, batch: list[AuditEntry]) -> None:
        if not batch:
            return
        try:
            async with SessionLocal() as db:
                await db.execute(insert(AuditLog), [asdict(entry) for entry in batch])
                await db.commit()
        except Exception:
            logger.exception("Failed to write %s audit entries", len(batch))

    async def _purge_expired(self) -> None:
        cutoff = datetime.now(timezone.utc) - timedelta(
            days=getSettings().AUDIT_RETENTION_DAYS
        )
        try:
            async with SessionLocal() as db:
                await db.execute(delete(AuditLog).where(AuditLog.created_at < cutoff))
                await db.commit()
        except Exception:
            logger.exception("Failed to purge expired audit entries")

    async def _run(self) -> None:
        next_purge = time.monotonic()
        while True:
            await asyncio.sleep(_FLUSH_INTERVAL_SECONDS)
            while batch := self._drain():
                await self._flush(batch)
            if time.monotonic() >= next_purge:
                await self._purge_expired()
                next_purge = time.monotonic() + _PURGE_INTERVAL_SECONDS
