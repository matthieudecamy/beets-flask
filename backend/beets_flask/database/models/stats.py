"""Cached filesystem statistics model.

Stores pre-computed dir size and file counts so that the stats endpoints
(home page) can return instantly without running expensive subprocesses.

Values are written by:
- The watchdog after its debounce fires (inbox stats)
- The import workers after an import completes (library stats)
- On watchdog startup for each configured inbox
"""

from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from beets_flask.database.models.base import Base


class CachedStatInDb(Base):
    """Cached filesystem stats for a single directory path.

    The ``id`` (inherited primary key) is set to the resolved absolute path
    string so each path maps to exactly one row.
    """

    __tablename__ = "cached_stats"

    # Size of the directory tree in bytes (du -sb)
    size_bytes: Mapped[int | None] = mapped_column(default=None)
    # Total number of files/dirs under the path (find | wc -l)
    n_files: Mapped[int | None] = mapped_column(default=None)
    # When these values were last computed
    computed_at: Mapped[float] = mapped_column(default=func.now())

    def __init__(
        self,
        path: Path | str,
        size_bytes: int | None = None,
        n_files: int | None = None,
    ):
        path = Path(path)
        super().__init__(id=str(path.resolve()))
        self.size_bytes = size_bytes
        self.n_files = n_files

    @property
    def path(self) -> Path:
        return Path(self.id)
