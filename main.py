"""
main.py — Application entry point for Ubuntu Storage & Memory Analyzer.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

# Ensure project root is on sys.path regardless of CWD
_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from database.settings_repository import SettingsRepository
from ui.main_window import MainWindow
from ui.theme import GLOBAL_STYLESHEET

# ── Logging ───────────────────────────────────────────────────────────────────
LOG_DIR = Path.home() / ".config" / "ubuntu-storage-analyzer"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "app.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


def main() -> None:
    logger.info("Starting Ubuntu Storage & Memory Analyzer")

    # Enable HiDPI support
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("Ubuntu Storage Analyzer")
    app.setOrganizationName("SysAnalyzer")
    app.setApplicationVersion("1.0.0")

    # Global font
    font = QFont("Ubuntu", 10)
    font.setStyleStrategy(QFont.PreferAntialias)
    app.setFont(font)

    # Global stylesheet
    app.setStyleSheet(GLOBAL_STYLESHEET)

    settings_repo = SettingsRepository()
    window = MainWindow(settings_repo)
    window.show()

    logger.info("Application window opened")
    ret = app.exec()
    logger.info("Application exiting with code %d", ret)
    sys.exit(ret)


if __name__ == "__main__":
    main()
