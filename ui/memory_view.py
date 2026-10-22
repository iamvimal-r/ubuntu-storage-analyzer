"""
memory_view.py — RAM and swap live monitoring panel.
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

from services.system_monitor import MemoryStats, format_bytes
from ui.theme import PALETTE
from ui.widgets import MetricCard, SectionHeader


class _GaugeRow(QWidget):
    def __init__(self, label: str, parent=None):
        super().__init__(parent)
        hlay = QHBoxLayout(self)
        hlay.setContentsMargins(0, 0, 0, 0)
        self._lbl = QLabel(label)
        self._lbl.setFixedWidth(120)
        self._lbl.setStyleSheet(f"color: {PALETTE['text_secondary']}; font-size: 13px;")

        self._bar = QProgressBar()
        self._bar.setRange(0, 100)
        self._bar.setFixedHeight(18)

        self._val = QLabel("—")
        self._val.setFixedWidth(90)
        self._val.setStyleSheet(f"color: {PALETTE['text_primary']}; font-size: 13px;")

        hlay.addWidget(self._lbl)
        hlay.addWidget(self._bar, 1)
        hlay.addWidget(self._val)

    def update(self, percent: float, value_str: str) -> None:
        pct = int(max(0, min(100, percent)))
        self._bar.setValue(pct)
        self._val.setText(value_str)
        if pct >= 90:
            color = PALETTE["critical"]
        elif pct >= 80:
            color = PALETTE["warning"]
        else:
            color = PALETTE["accent"]
        self._bar.setStyleSheet(
            f"""
            QProgressBar {{
                border: 1px solid {PALETTE['border']};
                border-radius: 6px;
                background: {PALETTE['bg_input']};
                text-align: center;
                font-size: 11px;
                color: {PALETTE['text_primary']};
            }}
            QProgressBar::chunk {{
                border-radius: 5px;
                background: {color};
            }}
            """
        )
        self._bar.setFormat(f"{percent:.1f}%")
        self._bar.setTextVisible(True)


class MemoryView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        vlay = QVBoxLayout(self)
        vlay.setContentsMargins(20, 20, 20, 20)
        vlay.setSpacing(18)

        vlay.addWidget(SectionHeader("Memory Monitor"))

        # Cards row
        cards_row = QHBoxLayout()
        self._total_card = MetricCard("Total RAM", show_bar=False)
        self._used_card = MetricCard("Used RAM", show_bar=True)
        self._avail_card = MetricCard("Available RAM", show_bar=False)
        self._swap_card = MetricCard("Swap Used", show_bar=True)
        for card in (self._total_card, self._used_card, self._avail_card, self._swap_card):
            cards_row.addWidget(card)
        vlay.addLayout(cards_row)

        # Detail gauges
        gauge_box = QGroupBox("Detailed Breakdown")
        gauge_vlay = QVBoxLayout(gauge_box)
        gauge_vlay.setSpacing(10)

        self._ram_gauge = _GaugeRow("RAM")
        self._swap_gauge = _GaugeRow("Swap")
        gauge_vlay.addWidget(self._ram_gauge)
        gauge_vlay.addWidget(self._swap_gauge)
        vlay.addWidget(gauge_box)

        vlay.addStretch()

    def refresh(self, mem: MemoryStats) -> None:
        self._total_card.update_value(format_bytes(mem.total), "Physical RAM")
        self._used_card.update_value(
            f"{mem.percent:.1f}%",
            f"{format_bytes(mem.used)} used",
            mem.percent,
        )
        self._avail_card.update_value(format_bytes(mem.available), "Free")
        self._swap_card.update_value(
            f"{mem.swap_percent:.1f}%",
            f"{format_bytes(mem.swap_used)} / {format_bytes(mem.swap_total)}",
            mem.swap_percent,
        )

        self._ram_gauge.update(
            mem.percent,
            f"{format_bytes(mem.used)} / {format_bytes(mem.total)}",
        )
        self._swap_gauge.update(
            mem.swap_percent,
            f"{format_bytes(mem.swap_used)} / {format_bytes(mem.swap_total)}",
        )
