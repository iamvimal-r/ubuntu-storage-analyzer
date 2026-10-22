"""
settings_view.py — Configurable thresholds and preferences.
"""
from __future__ import annotations

import logging

from PySide6.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ui.theme import PALETTE
from ui.widgets import SectionHeader

logger = logging.getLogger(__name__)


class SettingsView(QScrollArea):
    def __init__(self, settings_repo, main_window, parent=None):
        super().__init__(parent)
        self.settings_repo = settings_repo
        self.main_window = main_window
        self.setWidgetResizable(True)

        container = QWidget()
        self.setWidget(container)
        vlay = QVBoxLayout(container)
        vlay.setContentsMargins(20, 20, 20, 20)
        vlay.setSpacing(20)

        vlay.addWidget(SectionHeader("Settings & Preferences"))

        # Thresholds
        thresh_box = QGroupBox("Alert Thresholds (%)")
        form = QFormLayout(thresh_box)
        form.setLabelAlignment(__import__("PySide6.QtCore", fromlist=["Qt"]).Qt.AlignRight)
        form.setSpacing(10)

        def _spin(val: float) -> QDoubleSpinBox:
            s = QDoubleSpinBox()
            s.setRange(1.0, 99.0)
            s.setSingleStep(5.0)
            s.setDecimals(1)
            s.setSuffix(" %")
            s.setValue(val)
            return s

        self._disk_warn = _spin(settings_repo.get("disk_warning", 80.0))
        self._disk_crit = _spin(settings_repo.get("disk_critical", 90.0))
        self._ram_warn = _spin(settings_repo.get("ram_warning", 80.0))
        self._ram_crit = _spin(settings_repo.get("ram_critical", 90.0))
        self._swap_warn = _spin(settings_repo.get("swap_warning", 70.0))
        self._swap_crit = _spin(settings_repo.get("swap_critical", 90.0))
        self._cpu_warn = _spin(settings_repo.get("cpu_warning", 80.0))
        self._cpu_crit = _spin(settings_repo.get("cpu_critical", 95.0))

        form.addRow("Disk — Warning:", self._disk_warn)
        form.addRow("Disk — Critical:", self._disk_crit)
        form.addRow("RAM — Warning:", self._ram_warn)
        form.addRow("RAM — Critical:", self._ram_crit)
        form.addRow("Swap — Warning:", self._swap_warn)
        form.addRow("Swap — Critical:", self._swap_crit)
        form.addRow("CPU — Warning:", self._cpu_warn)
        form.addRow("CPU — Critical:", self._cpu_crit)
        vlay.addWidget(thresh_box)

        # Monitoring
        mon_box = QGroupBox("Monitoring")
        mon_form = QFormLayout(mon_box)
        mon_form.setSpacing(10)

        self._interval_spin = QSpinBox()
        self._interval_spin.setRange(1, 60)
        self._interval_spin.setSuffix(" s")
        self._interval_spin.setValue(int(settings_repo.get("monitor_interval", 2)))
        mon_form.addRow("Refresh interval:", self._interval_spin)

        # Sound alerts toggle
        self._sound_check = QCheckBox("Play sound on CPU / RAM / Swap / Disk alerts")
        self._sound_check.setChecked(bool(settings_repo.get("sound_enabled", True)))
        self._sound_check.setStyleSheet(
            f"color: {PALETTE['text_primary']}; font-size: 13px;"
        )
        mon_form.addRow("Sound alerts:", self._sound_check)
        vlay.addWidget(mon_box)

        # Scan options
        scan_box = QGroupBox("Scan Options")
        scan_form = QFormLayout(scan_box)
        scan_form.setSpacing(10)

        self._dup_check = QCheckBox("Enable by default")
        self._dup_check.setChecked(bool(settings_repo.get("detect_duplicates", False)))
        scan_form.addRow("Duplicate detection:", self._dup_check)

        self._max_entries_spin = QSpinBox()
        self._max_entries_spin.setRange(1000, 100_000)
        self._max_entries_spin.setSingleStep(1000)
        self._max_entries_spin.setValue(int(settings_repo.get("max_scan_entries", 10_000)))
        scan_form.addRow("Max scan entries:", self._max_entries_spin)
        vlay.addWidget(scan_box)

        # Buttons
        btn_row = QHBoxLayout()
        save_btn = QPushButton("✓  Save Settings")
        save_btn.setStyleSheet(
            f"background: {PALETTE['accent2']}; color: {PALETTE['bg_dark']}; font-weight: bold;"
        )
        save_btn.clicked.connect(self._save)

        reset_btn = QPushButton("↺  Reset to Defaults")
        reset_btn.clicked.connect(self._reset)

        btn_row.addWidget(save_btn)
        btn_row.addWidget(reset_btn)
        btn_row.addStretch()
        vlay.addLayout(btn_row)

        vlay.addStretch()

    def _save(self) -> None:
        repo = self.settings_repo
        repo.set("disk_warning", self._disk_warn.value())
        repo.set("disk_critical", self._disk_crit.value())
        repo.set("ram_warning", self._ram_warn.value())
        repo.set("ram_critical", self._ram_crit.value())
        repo.set("swap_warning", self._swap_warn.value())
        repo.set("swap_critical", self._swap_crit.value())
        repo.set("cpu_warning", self._cpu_warn.value())
        repo.set("cpu_critical", self._cpu_crit.value())
        repo.set("sound_enabled", self._sound_check.isChecked())
        repo.set("monitor_interval", self._interval_spin.value())
        repo.set("detect_duplicates", self._dup_check.isChecked())
        repo.set("max_scan_entries", self._max_entries_spin.value())

        logger.info("Settings saved.")
        self.main_window.reload_settings()
        QMessageBox.information(self, "Settings Saved", "Settings have been saved successfully.")

    def _reset(self) -> None:
        self.settings_repo.reset_defaults()
        repo = self.settings_repo
        self._disk_warn.setValue(repo.get("disk_warning", 80.0))
        self._disk_crit.setValue(repo.get("disk_critical", 90.0))
        self._ram_warn.setValue(repo.get("ram_warning", 80.0))
        self._ram_crit.setValue(repo.get("ram_critical", 90.0))
        self._swap_warn.setValue(repo.get("swap_warning", 70.0))
        self._swap_crit.setValue(repo.get("swap_critical", 90.0))
        self._cpu_warn.setValue(repo.get("cpu_warning", 80.0))
        self._cpu_crit.setValue(repo.get("cpu_critical", 95.0))
        self._sound_check.setChecked(bool(repo.get("sound_enabled", True)))
        self._interval_spin.setValue(int(repo.get("monitor_interval", 2)))
        self._dup_check.setChecked(bool(repo.get("detect_duplicates", False)))
        self._max_entries_spin.setValue(int(repo.get("max_scan_entries", 10_000)))
        QMessageBox.information(self, "Settings Reset", "All settings have been reset to defaults.")

