"""
widgets.py — Reusable custom widgets.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPen, QFont
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

from ui.theme import PALETTE


class MetricCard(QFrame):
    """A card widget showing a title, value, sub-label, and a progress bar."""

    def __init__(
        self,
        title: str,
        value: str = "—",
        subtitle: str = "",
        show_bar: bool = True,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.setObjectName("MetricCard")
        self.setStyleSheet(
            f"""
            #MetricCard {{
                background: {PALETTE['bg_card']};
                border: 1px solid {PALETTE['border']};
                border-radius: 10px;
                padding: 12px;
            }}
            """
        )

        vlay = QVBoxLayout(self)
        vlay.setSpacing(6)

        self._title_lbl = QLabel(title)
        self._title_lbl.setStyleSheet(
            f"color: {PALETTE['text_secondary']}; font-size: 12px; font-weight: bold;"
        )

        self._value_lbl = QLabel(value)
        self._value_lbl.setStyleSheet(
            f"color: {PALETTE['text_primary']}; font-size: 22px; font-weight: bold;"
        )

        self._sub_lbl = QLabel(subtitle)
        self._sub_lbl.setStyleSheet(
            f"color: {PALETTE['text_secondary']}; font-size: 11px;"
        )

        self._bar = QProgressBar()
        self._bar.setRange(0, 100)
        self._bar.setValue(0)
        self._bar.setTextVisible(False)
        self._bar.setFixedHeight(8)

        vlay.addWidget(self._title_lbl)
        vlay.addWidget(self._value_lbl)
        vlay.addWidget(self._sub_lbl)
        if show_bar:
            vlay.addWidget(self._bar)

    def update_value(self, value: str, subtitle: str = "", percent: float = 0.0) -> None:
        self._value_lbl.setText(value)
        self._sub_lbl.setText(subtitle)
        pct = max(0, min(100, int(percent)))
        self._bar.setValue(pct)
        self._apply_bar_color(pct)

    def _apply_bar_color(self, pct: int) -> None:
        if pct >= 90:
            color = PALETTE["critical"]
        elif pct >= 80:
            color = PALETTE["warning"]
        else:
            color = PALETTE["accent2"]
        self._bar.setStyleSheet(
            f"""
            QProgressBar {{
                border: none;
                border-radius: 4px;
                background: {PALETTE['bg_input']};
            }}
            QProgressBar::chunk {{
                border-radius: 4px;
                background: {color};
            }}
            """
        )


class SectionHeader(QLabel):
    """Bold section title with an accent underline look."""

    def __init__(self, text: str, parent: QWidget | None = None):
        super().__init__(text, parent)
        self.setStyleSheet(
            f"""
            font-size: 15px;
            font-weight: bold;
            color: {PALETTE['accent']};
            padding-bottom: 4px;
            border-bottom: 1px solid {PALETTE['border']};
            """
        )


class StatusDot(QLabel):
    """Colored status indicator dot."""

    _COLORS = {
        "ok": PALETTE["ok"],
        "warning": PALETTE["warning"],
        "critical": PALETTE["critical"],
        "idle": PALETTE["text_secondary"],
    }

    def __init__(self, status: str = "idle", parent: QWidget | None = None):
        super().__init__("●", parent)
        self.set_status(status)

    def set_status(self, status: str) -> None:
        color = self._COLORS.get(status, self._COLORS["idle"])
        self.setStyleSheet(f"color: {color}; font-size: 14px;")
