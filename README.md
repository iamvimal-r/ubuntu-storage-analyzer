# Ubuntu Storage & Memory Analyzer

A professional Python desktop application for Ubuntu Linux that monitors system resources, analyzes disk storage, identifies large files and directories, and warns you when storage or RAM usage becomes critically high.

---

## Architecture

```
ubuntu-storage-analyzer/
├── main.py                        # Entry point — logging, QApplication bootstrap
├── requirements.txt
├── setup.sh                       # One-shot venv + install script
├── ubuntu-storage-analyzer.desktop  # Ubuntu app menu integration
│
├── ui/                            # All PySide6 GUI code
│   ├── theme.py                   # Dark-mode palette + global stylesheet
│   ├── widgets.py                 # Reusable widgets (MetricCard, StatusDot…)
│   ├── main_window.py             # App shell: sidebar nav + monitoring timer
│   ├── storage_view.py            # Storage analyzer screen
│   ├── memory_view.py             # RAM + swap monitoring screen
│   ├── processes_view.py          # Top-memory processes table
│   ├── alerts_view.py             # Alert history screen
│   ├── reports_view.py            # CSV / JSON export screen
│   └── settings_view.py           # Threshold + preference configuration
│
├── services/
│   ├── system_monitor.py          # CPU, RAM, swap, disk, uptime (psutil)
│   ├── storage_scanner.py         # os.fwalk-based safe filesystem scanner
│   ├── process_service.py         # Top memory-consuming processes
│   ├── alert_service.py           # Threshold checks + desktop notifications
│   └── report_service.py          # CSV + JSON report generation
│
├── workers/
│   └── scan_worker.py             # QThread wrapper for background scanning
│
├── database/
│   └── settings_repository.py     # SQLite settings + alert history
│
└── tests/
    ├── test_system_monitor.py
    ├── test_storage_scanner.py
    └── test_alert_service.py
```

### Key Design Decisions

| Area | Choice | Reason |
|---|---|---|
| GUI | PySide6 (Qt6) | Native look on Ubuntu, powerful threading model |
| Monitoring | psutil | Cross-platform, no root required, rich API |
| Scanning | `os.fwalk` | Avoids following mount points, inode-deduplication |
| Background work | `QThread` | GUI never freezes; clean cancellation via `threading.Event` |
| Persistence | SQLite | Zero external server; settings + alert history survive restarts |
| Notifications | `notify-send` subprocess | Integrates natively with Ubuntu notification centre |
| Security | No `shell=True` ever | Prevents injection; all subprocess calls use argument lists |

---

## Installation

### Prerequisites

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip libglib2.0-0 libgl1 \
     libxcb-cursor0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 \
     libxcb-randr0 libxcb-render-util0 libxcb-xinerama0 libxkbcommon-x11-0 \
     notify-osd
```

### Setup (Recommended — venv)

```bash
cd ubuntu-storage-analyzer
bash setup.sh
```

### Manual Setup

```bash
cd ubuntu-storage-analyzer
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

---

## Running the Application

```bash
cd ubuntu-storage-analyzer
source venv/bin/activate
python main.py
```

Or use the provided launcher:

```bash
bash setup.sh    # once
source venv/bin/activate && python main.py
```

---

## Running Tests

```bash
source venv/bin/activate
python -m pytest tests/ -v
```

---

## Desktop Launcher (Ubuntu App Menu)

```bash
# Update path in the desktop file to match your actual location
APP_DIR="$HOME/ubuntu-storage-analyzer"
sed -i "s|%k|$APP_DIR|g" "$APP_DIR/ubuntu-storage-analyzer.desktop"

# Install for current user
cp ubuntu-storage-analyzer.desktop ~/.local/share/applications/
update-desktop-database ~/.local/share/applications/
```

---

## Features

### 🖥 Overview Dashboard
- Real-time CPU, RAM, Swap, and per-partition disk usage
- Progress bars colored OK (green) → Warning (amber) → Critical (red)
- System uptime
- Auto-refreshes every 2 seconds (configurable)

### 💾 Storage Analyzer
- Scans Home, /var, /tmp, /usr, or any user-selected directory
- Displays the **largest 20 files/folders** with path, size, type, modified date
- Sort by size, name, or modification date
- Filter by minimum size (Any / ≥1 MB / ≥10 MB / ≥100 MB / ≥500 MB / ≥1 GB)
- **Optional duplicate detection** via MD5 hashing
- Cancellable at any time; skips inaccessible files gracefully
- Excludes virtual filesystems (`/proc`, `/sys`, `/dev`, `/run`)
- Does **not** follow symlinks by default

### 🧠 Memory Monitor
- Total / Used / Available RAM with live gauges
- Swap usage

### ⚙ Processes
- Top 15 processes sorted by RSS memory
- PID, name, user, RSS, VMS, Mem%, CPU%, status
- Configurable display limit

### 🔔 Alerts
- Configurable warning (default 80%) and critical (default 90%) thresholds
- Desktop notifications via `notify-send`
- De-bounced: one notification per level change (won't spam)
- Alert history persisted in SQLite; survives restarts

### 📊 Reports
- Export current state to **JSON** or **CSV**
- Includes: disk scan, largest files, memory, top processes, alert history

### ⚙ Settings
- Adjust all thresholds via spinboxes
- Change monitoring refresh interval
- Toggle duplicate detection, max scan entries
- One-click reset to defaults

---

## Security Notes

- No root required for normal operation
- Never executes shell strings (`shell=False` everywhere)
- Never reads file contents except for MD5 duplicate detection (opt-in)
- Never auto-deletes files
- Skips mounted network drives unless explicitly selected
- All subprocess calls use argument lists only

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `ImportError: libGL.so.1` | `sudo apt install libgl1` |
| `xcb platform plugin not found` | `sudo apt install libxcb-cursor0 libxcb-xinerama0 libxkbcommon-x11-0` |
| `notify-send: command not found` | `sudo apt install notify-osd` or `libnotify-bin` |
| App window is blank | Ensure you're running in an X11 session, not a pure Wayland session without XWayland |
| Scan is very slow | Reduce `Max scan entries` in Settings, or set a higher `Min size` filter |
| PySide6 fails to install | Use Python ≥ 3.9; ensure pip is up to date: `pip install --upgrade pip` |

---

## Logs

Application logs are written to:
```
~/.config/ubuntu-storage-analyzer/app.log
```

Settings and alert history database:
```
~/.config/ubuntu-storage-analyzer/settings.db
```
# ubuntu-storage-analyzer
