"""
alerts_view.py — Threshold alert history display.
"""
from __future__ import annotations

import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from services.alert_service import AlertEvent, AlertLevel
from ui.theme import PALETTE
from ui.widgets import SectionHeader

HEADERS = ["Time", "Resource", "Level", "Value", "Message"]


class AlertsView(QWidget):
    def __init__(self, settings_repo, parent=None):
        super().__init__(parent)
        self.settings_repo = settings_repo

        vlay = QVBoxLayout(self)
        vlay.setContentsMargins(20, 20, 20, 20)
        vlay.setSpacing(12)

        vlay.addWidget(SectionHeader("Alert History"))

        btn_row = QHBoxLayout()
        clear_btn = QPushButton("🗑  Clear History")
        clear_btn.clicked.connect(self._clear)
        btn_row.addStretch()
        btn_row.addWidget(clear_btn)
        vlay.addLayout(btn_row)

        self._table = QTableWidget(0, len(HEADERS))
        self._table.setHorizontalHeaderLabels(HEADERS)
        self._table.setAlternatingRowColors(True)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self._table.verticalHeader().setVisible(False)
        vlay.addWidget(self._table, 1)

        # Load persisted history on startup
        self._load_persisted()

    def _load_persisted(self) -> None:
        rows = self.settings_repo.get_alerts(200)
        for row in reversed(rows):
            self._insert_row(
                row["timestamp"],
                row["resource"],
                row["level"],
                row["value"],
                row["message"],
            )

    def add_alert(self, event: AlertEvent) -> None:
        self._insert_row(
            event.timestamp,
            event.resource,
            event.level.value,
            event.value,
            event.message,
        )

    def _insert_row(
        self,
        timestamp: float,
        resource: str,
        level: str,
        value: float,
        message: str,
    ) -> None:
        row = 0
        self._table.insertRow(row)

        time_str = datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
        self._table.setItem(row, 0, QTableWidgetItem(time_str))
        self._table.setItem(row, 1, QTableWidgetItem(resource.title()))

        level_item = QTableWidgetItem(level.upper())
        level_color = (
            PALETTE["critical"] if level == "critical"
            else PALETTE["warning"]
        )
        level_item.setForeground(
            __import__("PySide6.QtGui", fromlist=["QColor"]).QColor(level_color)
        )
        level_item.setTextAlignment(Qt.AlignCenter)
        self._table.setItem(row, 2, level_item)

        val_item = QTableWidgetItem(f"{value:.1f}%")
        val_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._table.setItem(row, 3, val_item)
        self._table.setItem(row, 4, QTableWidgetItem(message))

    def _clear(self) -> None:
        self._table.setRowCount(0)
        self.settings_repo.clear_alert_history()
