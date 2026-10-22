"""
scan_worker.py — QThread-based background filesystem scanner.
"""
from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QThread, Signal

from services.storage_scanner import FileEntry, ScanResult, scan_directory

logger = logging.getLogger(__name__)


class ScanWorker(QThread):
    """
    Runs a storage scan in a background thread.

    Signals:
        progress(files_scanned: int, bytes_scanned: int)
        finished(result: ScanResult)
        error(message: str)
    """

    progress = Signal(int, int)
    finished = Signal(object)   # ScanResult
    error = Signal(str)

    def __init__(
        self,
        root: str,
        min_size_bytes: int = 0,
        detect_duplicates: bool = False,
        follow_symlinks: bool = False,
        max_entries: int = 10_000,
        parent=None,
    ):
        super().__init__(parent)
        self.root = root
        self.min_size_bytes = min_size_bytes
        self.detect_duplicates = detect_duplicates
        self.follow_symlinks = follow_symlinks
        self.max_entries = max_entries
        self._cancel_event = threading.Event()

    def cancel(self) -> None:
        """Request scan cancellation (thread-safe)."""
        self._cancel_event.set()

    def run(self) -> None:
        logger.info("ScanWorker started for %s", self.root)
        try:
            result = scan_directory(
                self.root,
                min_size_bytes=self.min_size_bytes,
                follow_symlinks=self.follow_symlinks,
                detect_duplicates=self.detect_duplicates,
                cancel_flag=self._cancel_event.is_set,
                progress_callback=lambda f, b: self.progress.emit(f, b),
                max_entries=self.max_entries,
            )
            self.finished.emit(result)
        except Exception as exc:
            logger.exception("ScanWorker error: %s", exc)
            self.error.emit(str(exc))
