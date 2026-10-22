"""
processes_view.py — Top memory-consuming processes table.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from services.process_service import ProcessInfo, get_top_processes
from services.system_monitor import format_bytes
from ui.theme import PALETTE
from ui.widgets import SectionHeader

HEADERS = ["PID", "Name", "User", "RSS", "VMS", "Mem %", "CPU %", "Status"]


class ProcessesView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        vlay = QVBoxLayout(self)
        vlay.setContentsMargins(20, 20, 20, 20)
        vlay.setSpacing(12)

        vlay.addWidget(SectionHeader("Running Processes"))

        top_row = QHBoxLayout()
        top_row.addWidget(QLabel("Show top:"))
        self._limit_spin = QSpinBox()
        self._limit_spin.setRange(5, 50)
        self._limit_spin.setValue(15)
        self._limit_spin.setFixedWidth(70)
        top_row.addWidget(self._limit_spin)
        top_row.addStretch()
        self._count_lbl = QLabel("")
        self._count_lbl.setStyleSheet(f"color: {PALETTE['text_secondary']}; font-size: 12px;")
        top_row.addWidget(self._count_lbl)
        vlay.addLayout(top_row)

        self._table = QTableWidget(0, len(HEADERS))
        self._table.setHorizontalHeaderLabels(HEADERS)
        self._table.setAlternatingRowColors(True)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self._table.verticalHeader().setVisible(False)
        vlay.addWidget(self._table, 1)

    def refresh(self) -> None:
        limit = self._limit_spin.value()
        procs = get_top_processes(limit)
        self._table.setRowCount(0)
        for proc in procs:
            self._add_row(proc)
        self._count_lbl.setText(f"{len(procs)} processes shown")

    def _add_row(self, proc: ProcessInfo) -> None:
        row = self._table.rowCount()
        self._table.insertRow(row)

        def item(text: str, align=Qt.AlignLeft) -> QTableWidgetItem:
            it = QTableWidgetItem(str(text))
            it.setTextAlignment(align | Qt.AlignVCenter)
            return it

        self._table.setItem(row, 0, item(proc.pid, Qt.AlignRight))
        self._table.setItem(row, 1, item(proc.name))
        self._table.setItem(row, 2, item(proc.username))

        rss_item = item(format_bytes(proc.rss), Qt.AlignRight)
        rss_item.setData(Qt.UserRole, proc.rss)
        rss_item.setForeground(
            __import__("PySide6.QtGui", fromlist=["QColor"]).QColor(PALETTE["accent2"])
        )
        self._table.setItem(row, 3, rss_item)
        self._table.setItem(row, 4, item(format_bytes(proc.vms), Qt.AlignRight))

        mem_pct_item = item(f"{proc.mem_percent:.1f}%", Qt.AlignRight)
        if proc.mem_percent >= 10:
            mem_pct_item.setForeground(
                __import__("PySide6.QtGui", fromlist=["QColor"]).QColor(PALETTE["warning"])
            )
        self._table.setItem(row, 5, mem_pct_item)
        self._table.setItem(row, 6, item(f"{proc.cpu_percent:.1f}%", Qt.AlignRight))
        self._table.setItem(row, 7, item(proc.status))
