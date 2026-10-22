"""
theme.py — Centralized dark-mode color palette and style constants.
"""

PALETTE = dict(
    bg_dark="#0D1117",
    bg_card="#161B22",
    bg_input="#21262D",
    border="#30363D",
    accent="#58A6FF",
    accent2="#3FB950",
    accent3="#F78166",
    accent4="#D29922",
    text_primary="#E6EDF3",
    text_secondary="#8B949E",
    warning="#D29922",
    critical="#F85149",
    ok="#3FB950",
)

GLOBAL_STYLESHEET = """
/* ─── Global ─────────────────────────────────────────────────────── */
* {{
    font-family: 'Segoe UI', 'Ubuntu', sans-serif;
    color: {text_primary};
}}

QMainWindow, QDialog, QWidget {{
    background-color: {bg_dark};
}}

/* ─── Labels ─────────────────────────────────────────────────────── */
QLabel {{
    background: transparent;
}}

/* ─── Group / Frame ─────────────────────────────────────────────── */
QGroupBox {{
    border: 1px solid {border};
    border-radius: 8px;
    margin-top: 12px;
    padding: 8px;
    background-color: {bg_card};
    font-weight: bold;
    font-size: 13px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 6px;
    color: {accent};
}}

/* ─── Buttons ─────────────────────────────────────────────────────── */
QPushButton {{
    background-color: {bg_input};
    border: 1px solid {border};
    border-radius: 6px;
    padding: 6px 14px;
    font-size: 13px;
    color: {text_primary};
}}
QPushButton:hover {{
    background-color: {accent};
    color: {bg_dark};
    border-color: {accent};
}}
QPushButton:pressed {{
    background-color: #1f6feb;
}}
QPushButton:disabled {{
    color: {text_secondary};
    border-color: {border};
}}

/* ─── Progress bars ─────────────────────────────────────────────── */
QProgressBar {{
    border: 1px solid {border};
    border-radius: 6px;
    background-color: {bg_input};
    text-align: center;
    font-size: 11px;
    color: {text_primary};
    height: 18px;
}}
QProgressBar::chunk {{
    border-radius: 5px;
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 {accent}, stop:1 #1f6feb
    );
}}

/* ─── Tables ─────────────────────────────────────────────────────── */
QTableWidget {{
    background-color: {bg_card};
    alternate-background-color: {bg_input};
    border: 1px solid {border};
    border-radius: 6px;
    gridline-color: {border};
    font-size: 12px;
    selection-background-color: {accent};
    selection-color: {bg_dark};
}}
QTableWidget::item {{
    padding: 4px 8px;
}}
QHeaderView::section {{
    background-color: {bg_input};
    border: none;
    border-bottom: 1px solid {border};
    padding: 6px 8px;
    font-weight: bold;
    font-size: 12px;
    color: {accent};
}}

/* ─── Scroll bars ─────────────────────────────────────────────────── */
QScrollBar:vertical {{
    background: {bg_dark};
    width: 10px;
    border-radius: 5px;
}}
QScrollBar::handle:vertical {{
    background: {border};
    border-radius: 5px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: {accent};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar:horizontal {{
    background: {bg_dark};
    height: 10px;
    border-radius: 5px;
}}
QScrollBar::handle:horizontal {{
    background: {border};
    border-radius: 5px;
    min-width: 30px;
}}

/* ─── Tab Bar ─────────────────────────────────────────────────────── */
QTabBar::tab {{
    background: {bg_card};
    border: 1px solid {border};
    border-radius: 6px 6px 0 0;
    padding: 8px 16px;
    margin-right: 2px;
    font-size: 13px;
    color: {text_secondary};
}}
QTabBar::tab:selected {{
    background: {bg_input};
    color: {accent};
    border-bottom-color: {bg_input};
}}
QTabBar::tab:hover:!selected {{
    color: {text_primary};
}}
QTabWidget::pane {{
    border: 1px solid {border};
    border-radius: 0 6px 6px 6px;
    background: {bg_card};
}}

/* ─── Combo / Spin ─────────────────────────────────────────────────── */
QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit {{
    background-color: {bg_input};
    border: 1px solid {border};
    border-radius: 6px;
    padding: 5px 10px;
    font-size: 13px;
    color: {text_primary};
}}
QComboBox::drop-down {{
    border: none;
    padding-right: 8px;
}}
QComboBox QAbstractItemView {{
    background: {bg_card};
    selection-background-color: {accent};
    selection-color: {bg_dark};
    border: 1px solid {border};
}}

/* ─── CheckBox ─────────────────────────────────────────────────────── */
QCheckBox {{
    spacing: 6px;
    font-size: 13px;
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid {border};
    border-radius: 4px;
    background: {bg_input};
}}
QCheckBox::indicator:checked {{
    background: {accent};
    border-color: {accent};
}}

/* ─── Slider ─────────────────────────────────────────────────────── */
QSlider::groove:horizontal {{
    background: {border};
    height: 4px;
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background: {accent};
    width: 14px;
    height: 14px;
    margin: -5px 0;
    border-radius: 7px;
}}

/* ─── Status bar ─────────────────────────────────────────────────── */
QStatusBar {{
    background: {bg_card};
    border-top: 1px solid {border};
    font-size: 12px;
    color: {text_secondary};
}}
""".format(**PALETTE)
