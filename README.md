<div align="center">

# 🔍 Ubuntu Storage & Memory Analyzer

**A professional desktop tool for Ubuntu that monitors disk storage, RAM, processes, and system health — in real time.**

[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![PySide6](https://img.shields.io/badge/PySide6-Qt6-41CD52?style=for-the-badge&logo=qt&logoColor=white)](https://doc.qt.io/qtforpython/)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Ubuntu%2020.04%2B-E95420?style=for-the-badge&logo=ubuntu&logoColor=white)](https://ubuntu.com)
[![SQLite](https://img.shields.io/badge/Storage-SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlite.org)

</div>

---

## ✨ Overview

**Ubuntu Storage & Memory Analyzer** is a fully offline, no-root-required desktop application built with **PySide6 (Qt6)** and **psutil**. It gives you a live, unified view of your system's health — disk partitions, top files, RAM, swap, running processes, and alert history — all in a polished dark-mode GUI.

### Why use this tool?

| Problem | Solution |
|---|---|
| "My disk is full but I don't know what's using it" | Storage Analyzer scans any directory and ranks the largest 20 files/folders |
| "My system is slow but I can't tell why" | Processes view shows the top RAM & CPU consumers live |
| "I missed a disk-full event while I was away" | Persistent alert history survives restarts; desktop notifications fire in real time |
| "I need a system snapshot to send to my team" | One-click JSON or CSV report export |

---

## 🚀 Quick Start

```bash
# 1. Clone
git clone https://github.com/iamvimal-r/ubuntu-storage-analyzer.git
cd ubuntu-storage-analyzer

# 2. Install system deps (once per machine)
sudo apt update && sudo apt install -y \
    python3 python3-venv libgl1 libxcb-cursor0 \
    libxcb-xinerama0 libxkbcommon-x11-0 notify-osd

# 3. Set up Python environment and install packages
bash setup.sh

# 4. Run
source venv/bin/activate && python main.py
```

---

## 📦 Features

### 🖥 Overview Dashboard
- Live CPU, RAM, Swap, and per-partition disk usage cards
- Colour-coded progress bars: 🟢 OK → 🟡 Warning → 🔴 Critical
- System uptime display
- Auto-refreshes every 2 s (interval configurable in Settings)

### 💾 Storage Analyzer
- Scans **Home**, `/var`, `/tmp`, `/usr`, or any custom path
- Shows the **top 20 largest files/folders** with path, size, type, and modified date
- Column sorting (Name / Size / Type / Modified)
- Minimum-size filter (Any / ≥1 MB / ≥10 MB / ≥100 MB / ≥500 MB / ≥1 GB)
- **Optional MD5 duplicate detection**
- Background scanning via `QThread` — UI never freezes
- Cancellable at any time
- Skips virtual filesystems (`/proc`, `/sys`, `/dev`, `/run`) and inaccessible paths
- Inode deduplication prevents counting hard-linked files twice

### 🧠 Memory Monitor
- Total / Used / Available RAM with live progress gauges
- Swap total / used

### ⚙ Process Monitor
- Top 15 processes by RSS memory consumption
- Columns: PID · Name · User · RSS · VMS · Mem% · CPU% · Status
- Auto-refreshing

### 🔔 Alert System
- Per-resource warning & critical thresholds (CPU, RAM, Swap, Disk)
- Desktop notifications via `notify-send`
- De-bounced — one notification per level change (no spam)
- Full alert history persisted in SQLite and displayed in-app

### 📊 Report Export
- One-click export to **JSON** or **CSV**
- Report includes: disk scan summary, top 20 files, memory stats, top 10 processes, alert history

### ⚙ Settings
- Adjust all thresholds via spinboxes
- Configure monitoring interval, max scan entries, default scan path
- Toggle duplicate detection and symlink following
- One-click **Reset to Defaults**

---

## 🗂 Project Structure

```
ubuntu-storage-analyzer/
├── main.py                          # Entry point — logging + QApplication bootstrap
├── requirements.txt                 # PySide6, psutil
├── setup.sh                         # One-shot venv setup script
├── run.sh                           # Background launcher (start|stop|restart|status|log)
├── ubuntu-storage-analyzer.desktop  # GNOME/Ubuntu app menu integration
├── ubuntu-storage-analyzer.service  # systemd user service unit
│
├── ui/                              # All PySide6 GUI code
│   ├── theme.py                     # Dark-mode colour palette + global stylesheet
│   ├── widgets.py                   # Shared widgets: MetricCard, SectionHeader, StatusDot
│   ├── main_window.py               # App shell: sidebar nav + monitoring timer
│   ├── storage_view.py              # Storage analyzer screen
│   ├── memory_view.py               # RAM + swap monitoring screen
│   ├── processes_view.py            # Top-memory process table
│   ├── alerts_view.py               # Alert history screen
│   ├── reports_view.py              # CSV / JSON export screen
│   └── settings_view.py             # Threshold + preference configuration
│
├── services/                        # Pure business logic (no Qt imports)
│   ├── system_monitor.py            # CPU, RAM, swap, disk, uptime via psutil
│   ├── storage_scanner.py           # os.fwalk-based safe filesystem scanner
│   ├── process_service.py           # Top memory-consuming processes
│   ├── alert_service.py             # Threshold checks + desktop notifications
│   └── report_service.py            # CSV + JSON report generation
│
├── workers/
│   └── scan_worker.py               # QThread wrapper for background scanning
│
├── database/
│   └── settings_repository.py       # SQLite: settings + alert history persistence
│
└── tests/
    ├── test_system_monitor.py
    ├── test_storage_scanner.py
    └── test_alert_service.py
```

---

## 🔧 Installation

### Prerequisites

| Requirement | Version |
|---|---|
| Ubuntu | 20.04 LTS or later |
| Python | 3.9+ (3.11 / 3.12 recommended) |
| Display | X11 or XWayland |

```bash
sudo apt update
sudo apt install -y \
    python3 python3-venv python3-pip \
    libglib2.0-0 libgl1 \
    libxcb-cursor0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 \
    libxcb-randr0 libxcb-render-util0 libxcb-xinerama0 libxkbcommon-x11-0 \
    notify-osd
```

### Automated Setup (Recommended)

```bash
bash setup.sh
```

### Manual Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

---

## ▶ Running

### Foreground (development / first run)

```bash
source venv/bin/activate
python main.py
```

### Background (using `run.sh`)

```bash
bash run.sh start      # launch in background
bash run.sh stop       # graceful shutdown
bash run.sh restart    # stop + start
bash run.sh status     # show PID or "not running"
bash run.sh log        # tail the live log file
```

### As a systemd User Service (auto-start on login)

```bash
mkdir -p ~/.config/systemd/user/
cp ubuntu-storage-analyzer.service ~/.config/systemd/user/

# Edit ExecStart path to your clone location, then:
systemctl --user daemon-reload
systemctl --user enable --now ubuntu-storage-analyzer.service
systemctl --user status ubuntu-storage-analyzer.service
```

### Install to GNOME App Menu

```bash
APP_DIR="$(pwd)"
sed -i "s|%k|$APP_DIR|g" ubuntu-storage-analyzer.desktop
cp ubuntu-storage-analyzer.desktop ~/.local/share/applications/
update-desktop-database ~/.local/share/applications/
```

---

## 🧪 Running Tests

```bash
source venv/bin/activate
python -m pytest tests/ -v
```

Run a single suite:

```bash
python -m pytest tests/test_alert_service.py -v
```

---

## 📁 Data Files

| Path | Purpose |
|---|---|
| `~/.config/ubuntu-storage-analyzer/app.log` | Application log (INFO level) |
| `~/.config/ubuntu-storage-analyzer/settings.db` | SQLite — settings & alert history |
| `~/.config/ubuntu-storage-analyzer/app.pid` | PID file when using `run.sh start` |

To fully reset all settings and history:

```bash
rm ~/.config/ubuntu-storage-analyzer/settings.db
# Restart the app — defaults are seeded automatically
```

---

## 🛡 Security

- **No root required** for any operation
- `shell=False` everywhere — no shell injection possible
- Never reads file contents except during optional MD5 duplicate detection (opt-in)
- Never auto-deletes any files
- Skips network mounts unless explicitly selected
- All subprocess calls use argument lists only

---

## 🩺 Troubleshooting

| Symptom | Fix |
|---|---|
| `ImportError: libGL.so.1` | `sudo apt install libgl1` |
| `qt.qpa.plugin: Could not load xcb` | `sudo apt install libxcb-cursor0 libxcb-xinerama0 libxkbcommon-x11-0` |
| `notify-send: command not found` | `sudo apt install notify-osd` or `libnotify-bin` |
| Blank / black window | Run in X11 session. On Wayland: `export QT_QPA_PLATFORM=xcb` first |
| Scan is very slow | Lower **Max scan entries** in Settings or increase the **Min size** filter |
| `PySide6` fails to install | Python ≥ 3.9 required. Run `pip install --upgrade pip` first |
| App crashed | Check `~/.config/ubuntu-storage-analyzer/app.log` |

---

## 🏗 Architecture Decisions

| Area | Choice | Reason |
|---|---|---|
| GUI | PySide6 (Qt6) | Native Ubuntu look, powerful threading, LGPL licence |
| Monitoring | psutil | Cross-platform, no root, rich API |
| Scanning | `os.fwalk` | Avoids crossing mount points; inode deduplication built-in |
| Background work | `QThread` | UI stays responsive; clean cancellation via `threading.Event` |
| Persistence | SQLite | Zero external server; settings + alerts survive restarts |
| Notifications | `notify-send` subprocess | Integrates natively with Ubuntu notification centre |
| Security | No `shell=True` ever | Prevents command injection |

---

## 🤝 Contributing

Contributions are very welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) first.

**Quick steps:**

```bash
# 1. Fork this repo on GitHub, then clone your fork
git clone https://github.com/<your-username>/ubuntu-storage-analyzer.git
cd ubuntu-storage-analyzer

# 2. Create a feature branch
git checkout -b feature/my-new-feature

# 3. Set up dev environment
bash setup.sh

# 4. Make changes, write tests, run the suite
source venv/bin/activate
python -m pytest tests/ -v

# 5. Commit and push
git commit -m "feat: add my new feature"
git push origin feature/my-new-feature

# 6. Open a Pull Request on GitHub
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for code style, branch naming, and PR guidelines.

---

## 📋 Changelog

See [CHANGELOG.md](CHANGELOG.md) for a full version history.

---

## 📄 License

This project is licensed under the **MIT License** — see [LICENSE](LICENSE) for details.

---

## 👤 Author

**Vimal R**
- GitHub: [@iamvimal-r](https://github.com/iamvimal-r)

---

<div align="center">

⭐ If this project helped you, please give it a star on GitHub!

</div>
