"""
reports_view.py — Export system reports to CSV and JSON.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Callable, List, Optional

from PySide6.QtWidgets import (
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from services.alert_service import AlertService
from services.system_monitor import MemoryStats
from ui.theme import PALETTE
from ui.widgets import SectionHeader

logger = logging.getLogger(__name__)


class ReportsView(QWidget):
    def __init__(self, settings_repo, alert_service: AlertService, parent=None):
        super().__init__(parent)
        self.settings_repo = settings_repo
        self.alert_service = alert_service
        self._mem_stats: Optional[MemoryStats] = None
        self._scan_result_getter: Optional[Callable] = None

        vlay = QVBoxLayout(self)
        vlay.setContentsMargins(20, 20, 20, 20)
        vlay.setSpacing(16)

        vlay.addWidget(SectionHeader("Reports"))

        box = QGroupBox("Export Report")
        blay = QVBoxLayout(box)

        desc = QLabel(
            "Generate a snapshot report of current system state including disk usage, "
            "memory stats, top processes, and alert history."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color: {PALETTE['text_secondary']}; font-size: 13px;")
        blay.addWidget(desc)

        btn_row = QHBoxLayout()
        json_btn = QPushButton("💾  Export as JSON")
        json_btn.clicked.connect(lambda: self._export("json"))
        csv_btn = QPushButton("📋  Export as CSV")
        csv_btn.clicked.connect(lambda: self._export("csv"))
        btn_row.addWidget(json_btn)
        btn_row.addWidget(csv_btn)
        btn_row.addStretch()
        blay.addLayout(btn_row)

        vlay.addWidget(box)

        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setStyleSheet(
            f"background: {PALETTE['bg_input']}; font-family: monospace; font-size: 12px;"
        )
        vlay.addWidget(self._log, 1)

    def set_mem_stats(self, stats: MemoryStats) -> None:
        self._mem_stats = stats

    def set_scan_result_getter(self, getter: Callable) -> None:
        self._scan_result_getter = getter

    def _export(self, fmt: str) -> None:
        default_name = f"sys_report.{fmt}"
        path, _ = QFileDialog.getSaveFileName(
            self,
            f"Save {fmt.upper()} Report",
            str(Path.home() / default_name),
            f"{fmt.upper()} Files (*.{fmt})",
        )
        if not path:
            return

        scan_result = self._scan_result_getter() if self._scan_result_getter else None
        top_files = []
        if scan_result:
            from services.storage_scanner import get_top_entries
            top_files = get_top_entries(scan_result.entries, 20)

        from services.process_service import get_top_processes
        procs = get_top_processes(10)
        alerts = self.alert_service.get_history()

        try:
            kwargs = dict(
                scan_result=scan_result,
                mem_stats=self._mem_stats,
                top_files=top_files,
                processes=procs,
                alerts=alerts,
            )
            if fmt == "json":
                from services.report_service import export_json
                export_json(path, **kwargs)
            else:
                from services.report_service import export_csv
                export_csv(path, **kwargs)
            self._log.append(f"✓ Saved {fmt.upper()} report → {path}")
        except Exception as exc:
            logger.exception("Report export failed: %s", exc)
            self._log.append(f"✗ Export failed: {exc}")
