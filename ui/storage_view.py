"""
storage_view.py — Storage analyzer UI with scan controls and file table.
"""
from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from services.storage_scanner import (
    FileEntry,
    ScanResult,
    find_duplicates,
    format_size,
    get_top_entries,
)
from ui.theme import PALETTE
from ui.widgets import SectionHeader
from workers.scan_worker import ScanWorker

logger = logging.getLogger(__name__)

SCAN_PRESETS = [
    ("Home Directory",    str(Path.home())),
    ("/var",              "/var"),
    ("/tmp",              "/tmp"),
    ("/usr",              "/usr"),
    ("Custom…",           "__custom__"),
]

MIN_SIZE_OPTIONS = [
    ("Any size",   0),
    ("≥ 1 MB",     1 * 1024 * 1024),
    ("≥ 10 MB",   10 * 1024 * 1024),
    ("≥ 100 MB", 100 * 1024 * 1024),
    ("≥ 500 MB", 500 * 1024 * 1024),
    ("≥ 1 GB",  1024 * 1024 * 1024),
]

TABLE_HEADERS = ["#", "Path", "Size", "Type", "Modified"]


class StorageView(QWidget):
    def __init__(self, settings_repo, parent=None):
        super().__init__(parent)
        self.settings_repo = settings_repo
        self._worker: Optional[ScanWorker] = None
        self._last_result: Optional[ScanResult] = None
        self._entries: List[FileEntry] = []

        root_lay = QVBoxLayout(self)
        root_lay.setContentsMargins(20, 20, 20, 20)
        root_lay.setSpacing(14)

        root_lay.addWidget(SectionHeader("Storage Analyzer"))

        # Controls
        ctrl_box = QGroupBox("Scan Options")
        ctrl_lay = QHBoxLayout(ctrl_box)
        ctrl_lay.setSpacing(10)

        # Preset dropdown
        self._preset_combo = QComboBox()
        for label, _ in SCAN_PRESETS:
            self._preset_combo.addItem(label)
        self._preset_combo.currentIndexChanged.connect(self._on_preset_change)
        ctrl_lay.addWidget(QLabel("Location:"))
        ctrl_lay.addWidget(self._preset_combo)

        # Custom path entry
        self._path_edit = QLineEdit(str(Path.home()))
        self._path_edit.setPlaceholderText("Path to scan…")
        ctrl_lay.addWidget(self._path_edit, 1)

        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self._browse)
        ctrl_lay.addWidget(browse_btn)

        # Min size
        ctrl_lay.addWidget(QLabel("Min size:"))
        self._size_combo = QComboBox()
        for label, _ in MIN_SIZE_OPTIONS:
            self._size_combo.addItem(label)
        ctrl_lay.addWidget(self._size_combo)

        # Duplicates checkbox
        self._dup_check = QCheckBox("Find Duplicates")
        self._dup_check.setChecked(
            bool(self.settings_repo.get("detect_duplicates", False))
        )
        ctrl_lay.addWidget(self._dup_check)

        root_lay.addWidget(ctrl_box)

        # Scan / Cancel buttons + progress
        btn_row = QHBoxLayout()
        self._scan_btn = QPushButton("▶  Start Scan")
        self._scan_btn.setStyleSheet(
            f"background: {PALETTE['accent']}; color: {PALETTE['bg_dark']}; font-weight: bold;"
        )
        self._scan_btn.clicked.connect(self._start_scan)
        btn_row.addWidget(self._scan_btn)

        self._cancel_btn = QPushButton("✕  Cancel")
        self._cancel_btn.setEnabled(False)
        self._cancel_btn.clicked.connect(self._cancel_scan)
        btn_row.addWidget(self._cancel_btn)

        btn_row.addStretch()

        self._status_lbl = QLabel("Idle")
        self._status_lbl.setStyleSheet(f"color: {PALETTE['text_secondary']};")
        btn_row.addWidget(self._status_lbl)

        root_lay.addLayout(btn_row)

        self._progress = QProgressBar()
        self._progress.setRange(0, 0)
        self._progress.setVisible(False)
        self._progress.setFixedHeight(10)
        root_lay.addWidget(self._progress)

        # Sort controls
        sort_row = QHBoxLayout()
        sort_row.addWidget(QLabel("Sort by:"))
        self._sort_combo = QComboBox()
        self._sort_combo.addItems(["Size (largest first)", "Name (A→Z)", "Modified (newest first)"])
        self._sort_combo.currentIndexChanged.connect(self._apply_sort)
        sort_row.addWidget(self._sort_combo)
        sort_row.addStretch()
        self._count_lbl = QLabel("")
        self._count_lbl.setStyleSheet(f"color: {PALETTE['text_secondary']}; font-size: 12px;")
        sort_row.addWidget(self._count_lbl)
        root_lay.addLayout(sort_row)

        # Table
        self._table = QTableWidget(0, len(TABLE_HEADERS))
        self._table.setHorizontalHeaderLabels(TABLE_HEADERS)
        self._table.setAlternatingRowColors(True)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self._table.verticalHeader().setVisible(False)
        root_lay.addWidget(self._table, 1)

        # Duplicate summary
        self._dup_lbl = QLabel("")
        self._dup_lbl.setStyleSheet(f"color: {PALETTE['warning']}; font-size: 12px;")
        root_lay.addWidget(self._dup_lbl)

    # ── Controls ──────────────────────────────────────────────────────────────

    def _on_preset_change(self, idx: int) -> None:
        _, path = SCAN_PRESETS[idx]
        if path != "__custom__":
            self._path_edit.setText(path)

    def _browse(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Select Directory", self._path_edit.text())
        if path:
            self._path_edit.setText(path)
            self._preset_combo.setCurrentIndex(len(SCAN_PRESETS) - 1)  # Custom

    # ── Scanning ──────────────────────────────────────────────────────────────

    def _start_scan(self) -> None:
        root = self._path_edit.text().strip()
        if not root or not os.path.isdir(root):
            self._status_lbl.setText("⚠ Invalid path")
            return

        min_size = MIN_SIZE_OPTIONS[self._size_combo.currentIndex()][1]
        detect_dup = self._dup_check.isChecked()

        self._scan_btn.setEnabled(False)
        self._cancel_btn.setEnabled(True)
        self._progress.setVisible(True)
        self._status_lbl.setText("Scanning…")
        self._table.setRowCount(0)
        self._entries = []
        self._dup_lbl.setText("")
        self._count_lbl.setText("")

        max_entries = int(self.settings_repo.get("max_scan_entries", 10_000))

        self._worker = ScanWorker(
            root=root,
            min_size_bytes=min_size,
            detect_duplicates=detect_dup,
            follow_symlinks=False,
            max_entries=max_entries,
        )
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_scan_done)
        self._worker.error.connect(self._on_scan_error)
        self._worker.start()

    def _cancel_scan(self) -> None:
        if self._worker:
            self._worker.cancel()

    def _on_progress(self, files: int, size: int) -> None:
        self._status_lbl.setText(f"Scanned {files:,} files  ({format_size(size)})")

    def _on_scan_done(self, result: ScanResult) -> None:
        self._last_result = result
        self._entries = sorted(result.entries, key=lambda e: e.size, reverse=True)
        top = self._entries[:20]
        self._populate_table(top)

        note = " (cancelled)" if result.cancelled else ""
        self._status_lbl.setText(
            f"Done{note} — {result.total_files:,} files, {result.total_dirs:,} dirs, "
            f"{format_size(result.total_size)} total  •  {result.skipped} skipped"
        )
        self._count_lbl.setText(f"Showing top {len(top)} of {len(result.entries):,} entries")

        # Duplicates
        if self._dup_check.isChecked():
            dups = find_duplicates(result.entries)
            if dups:
                total_dup = sum(len(v) - 1 for v in dups.values())
                self._dup_lbl.setText(
                    f"⚠ {len(dups)} duplicate groups found ({total_dup} extra copies)"
                )
            else:
                self._dup_lbl.setText("✓ No duplicates found")

        self._scan_btn.setEnabled(True)
        self._cancel_btn.setEnabled(False)
        self._progress.setVisible(False)
        self._worker = None

    def _on_scan_error(self, msg: str) -> None:
        self._status_lbl.setText(f"Error: {msg}")
        self._scan_btn.setEnabled(True)
        self._cancel_btn.setEnabled(False)
        self._progress.setVisible(False)
        self._worker = None

    # ── Table ─────────────────────────────────────────────────────────────────

    def _populate_table(self, entries: List[FileEntry]) -> None:
        self._table.setRowCount(0)
        for i, entry in enumerate(entries):
            row = self._table.rowCount()
            self._table.insertRow(row)

            num_item = QTableWidgetItem(str(i + 1))
            num_item.setTextAlignment(Qt.AlignCenter)
            self._table.setItem(row, 0, num_item)

            path_item = QTableWidgetItem(entry.path)
            path_item.setToolTip(entry.path)
            self._table.setItem(row, 1, path_item)

            size_item = QTableWidgetItem(format_size(entry.size))
            size_item.setData(Qt.UserRole, entry.size)
            size_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            size_item.setForeground(
                __import__("PySide6.QtGui", fromlist=["QColor"]).QColor(PALETTE["accent2"])
            )
            self._table.setItem(row, 2, size_item)

            type_item = QTableWidgetItem(entry.file_type)
            self._table.setItem(row, 3, type_item)

            mod_str = time.strftime("%Y-%m-%d %H:%M", time.localtime(entry.mtime))
            self._table.setItem(row, 4, QTableWidgetItem(mod_str))

        self._table.resizeColumnToContents(0)
        self._table.resizeColumnToContents(2)
        self._table.resizeColumnToContents(3)
        self._table.resizeColumnToContents(4)

    def _apply_sort(self) -> None:
        idx = self._sort_combo.currentIndex()
        if not self._entries:
            return
        if idx == 0:
            sorted_entries = sorted(self._entries, key=lambda e: e.size, reverse=True)
        elif idx == 1:
            sorted_entries = sorted(self._entries, key=lambda e: e.path.lower())
        else:
            sorted_entries = sorted(self._entries, key=lambda e: e.mtime, reverse=True)
        self._populate_table(sorted_entries[:20])
