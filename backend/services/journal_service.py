from datetime import datetime
from functools import lru_cache
from typing import TYPE_CHECKING, Any, ClassVar, Protocol, cast


class ReaderProtocol(Protocol):
    """Protocol for the systemd.journal.Reader class."""

    def this_boot(self) -> None:
        ...

    def seek_realtime(self, dt: datetime) -> None:
        ...

    def add_match(self, **kwargs: Any) -> None:
        ...

    def seek_cursor(self, cursor: str) -> None:
        ...

    def get_cursor(self) -> str:
        ...

    def __iter__(self) -> "ReaderProtocol":
        ...

    def __next__(self) -> dict[str, Any]:
        ...


class JournalModuleProtocol(Protocol):
    """Protocol for the systemd.journal module."""

    Reader: ClassVar[type[ReaderProtocol]]


class SystemdJournalProtocol(Protocol):
    """Protocol for the systemd module with journal attribute."""

    journal: ClassVar[JournalModuleProtocol]


try:
    import systemd.journal  # type: ignore
except ImportError:
    systemd = None  # type: ignore
    if TYPE_CHECKING:
        systemd = cast("SystemdJournalProtocol", Any)  # type: ignore


class JournalLogEntry(dict[str, Any]):
    """Represents a single log entry from journald."""

    pass


def parse_journal_entry(entry: dict[str, Any]) -> JournalLogEntry:
    """Convert a raw journal entry to a serializable log entry."""
    return JournalLogEntry(
        {
            "timestamp": (
                datetime.fromtimestamp(entry["__REALTIME_TIMESTAMP"].timestamp()).isoformat()
                if "__REALTIME_TIMESTAMP" in entry
                else None
            ),
            "level": entry.get("PRIORITY"),
            "message": entry.get("MESSAGE"),
            "service_name": entry.get("_SYSTEMD_UNIT"),
            "logger": entry.get("SYSLOG_IDENTIFIER"),
            "pid": entry.get("_PID"),
            "extra": {
                k: v
                for k, v in entry.items()
                if k
                not in {
                    "__REALTIME_TIMESTAMP",
                    "PRIORITY",
                    "MESSAGE",
                    "_SYSTEMD_UNIT",
                    "SYSLOG_IDENTIFIER",
                    "_PID",
                }
            },
        }
    )


def get_journal_logs(
    since: datetime | None = None,
    until: datetime | None = None,
    level: int | None = None,
    service: str | None = None,
    cursor: str | None = None,
    page_size: int = 100,
) -> tuple[list[JournalLogEntry], str | None]:
    """
    Retrieve logs from journald with optional filtering and pagination.

    Args:
        since: Only return logs after this time.
        until: Only return logs before this time.
        level: Only return logs at this syslog priority or lower (lower is more severe).
        service: Only return logs for this systemd unit.
        cursor: Journal cursor for pagination.
        page_size: Number of log entries to return.

    Returns:
        A tuple of (list of log entries, next cursor for pagination).
    """
    if systemd is None:
        raise RuntimeError("systemd.journal module is not available. Install systemd-python.")

    reader = systemd.journal.Reader()
    reader.this_boot()
    if since:
        reader.seek_realtime(since)
    if until:
        reader.add_match(__REALTIME_TIMESTAMP=f"..{until.isoformat()}")
    if level is not None:
        reader.add_match(PRIORITY=str(level))
    if service:
        reader.add_match(_SYSTEMD_UNIT=service)
    if cursor:
        reader.seek_cursor(cursor)
        next(reader)  # skip the entry at the cursor

    logs: list[JournalLogEntry] = []
    next_cursor = None
    for i, entry in enumerate(reader):
        logs.append(parse_journal_entry(entry))
        if i + 1 >= page_size:
            next_cursor = reader.get_cursor()
            break
    return logs, next_cursor


@lru_cache(maxsize=16)
def get_cached_journal_logs(*args, **kwargs):
    """Cached version of get_journal_logs for performance."""
    return get_journal_logs(*args, **kwargs)
