"""
main_window.py — Application shell, sidebar navigation, system dashboard.
"""
from __future__ import annotations

import logging
from typing import Optional

import psutil
from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QStatusBar,
    QVBoxLayout,
    QWidget,
    QGridLayout,
)

from services.alert_service import AlertEvent, AlertLevel, AlertService, Thresholds
from services.system_monitor import (
    collect_system_stats,
    format_bytes,
    format_uptime,
    SystemStats,
)
from ui.theme import PALETTE
from ui.widgets import MetricCard, SectionHeader, StatusDot

logger = logging.getLogger(__name__)

NAV_ITEMS = [
    ("🖥  Overview",      "overview"),
    ("💾  Storage",        "storage"),
    ("🧠  Memory",         "memory"),
    ("⚙  Processes",      "processes"),
    ("🔔  Alerts",         "alerts"),
    ("📊  Reports",        "reports"),
    ("⚙  Settings",       "settings"),
]


class NavButton(QPushButton):
    def __init__(self, text: str, page_id: str, parent=None):
        super().__init__(text, parent)
        self.page_id = page_id
        self.setCheckable(True)
        self.setFixedHeight(44)
        self.setCursor(Qt.PointingHandCursor)
        self._apply_style(False)

    def _apply_style(self, active: bool) -> None:
        if active:
            self.setStyleSheet(
                f"""
                QPushButton {{
                    background: {PALETTE['accent']};
                    color: {PALETTE['bg_dark']};
                    border: none;
                    border-radius: 8px;
                    padding: 8px 16px;
                    text-align: left;
                    font-weight: bold;
                    font-size: 13px;
                }}
                """
            )
        else:
            self.setStyleSheet(
                f"""
                QPushButton {{
                    background: transparent;
                    color: {PALETTE['text_secondary']};
                    border: none;
                    border-radius: 8px;
                    padding: 8px 16px;
                    text-align: left;
                    font-size: 13px;
                }}
                QPushButton:hover {{
                    background: {PALETTE['bg_input']};
                    color: {PALETTE['text_primary']};
                }}
                """
            )

    def setActive(self, active: bool) -> None:
        self._apply_style(active)


class OverviewPage(QScrollArea):
    """System dashboard page."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        self.setWidget(container)
        vlay = QVBoxLayout(container)
        vlay.setSpacing(20)
        vlay.setContentsMargins(20, 20, 20, 20)

        vlay.addWidget(SectionHeader("System Overview"))

        # Top metric cards
        cards_row = QWidget()
        grid = QGridLayout(cards_row)
        grid.setSpacing(12)
        grid.setContentsMargins(0, 0, 0, 0)

        self.cpu_card = MetricCard("CPU Usage", show_bar=True)
        self.ram_card = MetricCard("RAM Usage", show_bar=True)
        self.swap_card = MetricCard("Swap Usage", show_bar=True)
        self.uptime_card = MetricCard("System Uptime", show_bar=False)

        grid.addWidget(self.cpu_card, 0, 0)
        grid.addWidget(self.ram_card, 0, 1)
        grid.addWidget(self.swap_card, 0, 2)
        grid.addWidget(self.uptime_card, 0, 3)
        vlay.addWidget(cards_row)

        # Disk partitions section
        vlay.addWidget(SectionHeader("Disk Partitions"))
        self.disk_container = QWidget()
        self.disk_layout = QVBoxLayout(self.disk_container)
        self.disk_layout.setSpacing(10)
        self.disk_layout.setContentsMargins(0, 0, 0, 0)
        vlay.addWidget(self.disk_container)

        vlay.addStretch()

    def refresh(self, stats: SystemStats, alert_service: AlertService) -> None:
        cpu = stats.cpu
        mem = stats.memory

        cpu_level = alert_service.check("cpu", cpu.percent, "CPU")
        self.cpu_card.update_value(
            f"{cpu.percent:.1f}%",
            f"{cpu.count_logical} threads  •  {cpu.freq_current:.0f} MHz",
            cpu.percent,
        )

        ram_pct = mem.percent
        ram_level = alert_service.check("ram", ram_pct, "RAM")
        self.ram_card.update_value(
            f"{ram_pct:.1f}%",
            f"Used {format_bytes(mem.used)} / {format_bytes(mem.total)}",
            ram_pct,
        )

        swap_pct = mem.swap_percent
        swap_level = alert_service.check("swap", swap_pct, "Swap")
        self.swap_card.update_value(
            f"{swap_pct:.1f}%",
            f"Used {format_bytes(mem.swap_used)} / {format_bytes(mem.swap_total)}",
            swap_pct,
        )

        self.uptime_card.update_value(
            format_uptime(stats.uptime_seconds),
            "Since last boot",
        )

        # Rebuild disk partition cards
        while self.disk_layout.count():
            item = self.disk_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for part in stats.partitions:
            card = self._make_disk_card(part, alert_service)
            self.disk_layout.addWidget(card)

    def _make_disk_card(self, part, alert_service: AlertService) -> QWidget:
        from services.alert_service import AlertLevel
        frame = QFrame()
        frame.setStyleSheet(
            f"""
            QFrame {{
                background: {PALETTE['bg_card']};
                border: 1px solid {PALETTE['border']};
                border-radius: 8px;
                padding: 10px;
            }}
            """
        )
        hlay = QHBoxLayout(frame)

        left = QVBoxLayout()
        name_lbl = QLabel(f"{part.mountpoint}  ({part.device})")
        name_lbl.setStyleSheet(f"font-weight: bold; font-size: 13px; color: {PALETTE['text_primary']};")
        fs_lbl = QLabel(f"Filesystem: {part.fstype}  •  Total: {format_bytes(part.total)}  •  Free: {format_bytes(part.free)}")
        fs_lbl.setStyleSheet(f"font-size: 11px; color: {PALETTE['text_secondary']};")
        left.addWidget(name_lbl)
        left.addWidget(fs_lbl)

        bar = MetricCard(f"", show_bar=True)
        bar.setFixedWidth(220)

        disk_level = alert_service.check("disk", part.percent, f"Disk {part.mountpoint}")
        bar.update_value(f"{part.percent:.1f}%", f"Used {format_bytes(part.used)}", part.percent)

        hlay.addLayout(left, 1)
        hlay.addWidget(bar)
        return frame


class MainWindow(QMainWindow):
    """Top-level application window with sidebar and stacked pages."""

    alert_received = Signal(AlertEvent)

    def __init__(self, settings_repo, parent=None):
        super().__init__(parent)
        self.settings_repo = settings_repo
        self._build_alert_service()

        self.setWindowTitle("Ubuntu Storage & Memory Analyzer")
        self.setMinimumSize(1100, 700)
        self.resize(1300, 780)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        root_hlay = QHBoxLayout(central)
        root_hlay.setSpacing(0)
        root_hlay.setContentsMargins(0, 0, 0, 0)

        # Sidebar
        sidebar = self._build_sidebar()
        root_hlay.addWidget(sidebar)

        # Page stack
        self.stack = QStackedWidget()
        root_hlay.addWidget(self.stack, 1)

        self._pages = {}
        self._nav_buttons = []
        self._build_pages()

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self._status_msg = QLabel("Ready")
        self._status_msg.setStyleSheet(f"color: {PALETTE['text_secondary']}; font-size: 12px;")
        self.status_bar.addWidget(self._status_msg)

        # Monitoring timer
        self._monitor_interval = int(self.settings_repo.get("monitor_interval", 2)) * 1000
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_monitor_tick)
        self._timer.start(self._monitor_interval)
        # Initial collection (don't block: cpu_percent needs a reference call)
        import psutil as _psutil
        _psutil.cpu_percent()  # primes the counter
        QTimer.singleShot(500, self._on_monitor_tick)

        self._navigate("overview")

    # ── Alert Service ─────────────────────────────────────────────────────────

    def _build_alert_service(self) -> None:
        t = Thresholds(
            disk_warning=self.settings_repo.get("disk_warning", 80.0),
            disk_critical=self.settings_repo.get("disk_critical", 90.0),
            ram_warning=self.settings_repo.get("ram_warning", 80.0),
            ram_critical=self.settings_repo.get("ram_critical", 90.0),
            swap_warning=self.settings_repo.get("swap_warning", 70.0),
            swap_critical=self.settings_repo.get("swap_critical", 90.0),
            cpu_warning=self.settings_repo.get("cpu_warning", 80.0),
            cpu_critical=self.settings_repo.get("cpu_critical", 95.0),
        )
        sound_on = bool(self.settings_repo.get("sound_enabled", True))
        self.alert_service = AlertService(
            thresholds=t,
            ui_callback=self._on_alert,
            sound_enabled=sound_on,
        )

    def _on_alert(self, event: AlertEvent) -> None:
        self.alert_received.emit(event)
        # Persist
        self.settings_repo.save_alert(
            event.timestamp, event.resource, event.level.value, event.value, event.message
        )
        color = PALETTE["critical"] if event.level == AlertLevel.CRITICAL else PALETTE["warning"]
        self._status_msg.setText(f"⚠ {event.message}")
        self._status_msg.setStyleSheet(f"color: {color}; font-size: 12px; font-weight: bold;")
        QTimer.singleShot(8000, self._reset_status)

    def _reset_status(self) -> None:
        self._status_msg.setText("Monitoring…")
        self._status_msg.setStyleSheet(f"color: {PALETTE['text_secondary']}; font-size: 12px;")

    # ── Sidebar ───────────────────────────────────────────────────────────────

    def _build_sidebar(self) -> QWidget:
        sidebar = QFrame()
        sidebar.setFixedWidth(210)
        sidebar.setStyleSheet(
            f"""
            QFrame {{
                background: {PALETTE['bg_card']};
                border-right: 1px solid {PALETTE['border']};
            }}
            """
        )
        vlay = QVBoxLayout(sidebar)
        vlay.setSpacing(6)
        vlay.setContentsMargins(12, 20, 12, 20)

        # App title
        title = QLabel("🔍  SysAnalyzer")
        title.setStyleSheet(
            f"font-size: 16px; font-weight: bold; color: {PALETTE['accent']}; margin-bottom: 16px;"
        )
        vlay.addWidget(title)

        self._nav_buttons = []
        for text, page_id in NAV_ITEMS:
            btn = NavButton(text, page_id)
            btn.clicked.connect(lambda checked, pid=page_id: self._navigate(pid))
            vlay.addWidget(btn)
            self._nav_buttons.append(btn)

        vlay.addStretch()

        # Version label
        ver = QLabel("v1.0  •  Ubuntu Analyzer")
        ver.setStyleSheet(f"color: {PALETTE['text_secondary']}; font-size: 10px;")
        ver.setAlignment(Qt.AlignCenter)
        vlay.addWidget(ver)

        return sidebar

    # ── Pages ─────────────────────────────────────────────────────────────────

    def _build_pages(self) -> None:
        # Lazy import to avoid circular deps
        from ui.storage_view import StorageView
        from ui.memory_view import MemoryView
        from ui.settings_view import SettingsView
        from ui.alerts_view import AlertsView
        from ui.reports_view import ReportsView
        from ui.processes_view import ProcessesView

        self._overview_page = OverviewPage()
        self._storage_page = StorageView(self.settings_repo)
        self._memory_page = MemoryView()
        self._processes_page = ProcessesView()
        self._alerts_page = AlertsView(self.settings_repo)
        self._reports_page = ReportsView(self.settings_repo, self.alert_service)
        self._settings_page = SettingsView(self.settings_repo, self)

        pages = [
            ("overview",   self._overview_page),
            ("storage",    self._storage_page),
            ("memory",     self._memory_page),
            ("processes",  self._processes_page),
            ("alerts",     self._alerts_page),
            ("reports",    self._reports_page),
            ("settings",   self._settings_page),
        ]
        for page_id, widget in pages:
            self.stack.addWidget(widget)
            self._pages[page_id] = widget

        # Wire alert page to receive new alerts
        self.alert_received.connect(self._alerts_page.add_alert)
        self._reports_page.set_scan_result_getter(
            lambda: getattr(self._storage_page, "_last_result", None)
        )

    def _navigate(self, page_id: str) -> None:
        for btn in self._nav_buttons:
            btn.setActive(btn.page_id == page_id)
        widget = self._pages.get(page_id)
        if widget:
            self.stack.setCurrentWidget(widget)

    # ── Monitoring tick ───────────────────────────────────────────────────────

    def _on_monitor_tick(self) -> None:
        try:
            stats = collect_system_stats()
            # CPU alert — checked here so it fires regardless of which page is active
            self.alert_service.check("cpu", stats.cpu.percent, "CPU")
            self._overview_page.refresh(stats, self.alert_service)
            self._memory_page.refresh(stats.memory)
            self._processes_page.refresh()
            # Store latest stats for reports
            self._last_stats = stats
            self._reports_page.set_mem_stats(stats.memory)
        except Exception as exc:
            logger.exception("Monitor tick error: %s", exc)

    def reload_settings(self) -> None:
        """Called by SettingsView after saving."""
        self._build_alert_service()
        interval = int(self.settings_repo.get("monitor_interval", 2)) * 1000
        self._timer.setInterval(interval)

    def closeEvent(self, event) -> None:
        self._timer.stop()
        # Stop any running scan
        if hasattr(self._storage_page, "_worker") and self._storage_page._worker:
            self._storage_page._worker.cancel()
            self._storage_page._worker.wait(3000)
        self.settings_repo.close()
        super().closeEvent(event)
