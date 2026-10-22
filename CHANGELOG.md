# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- (Your next changes go here)

---

## [1.0.0] — 2026-10-22

### Added
- **Overview Dashboard** — live CPU, RAM, Swap, and per-partition disk metric cards
- **Storage Analyzer** — `os.fwalk`-based scanner with inode deduplication, symlink guard, and virtual-fs exclusion
  - Preset paths: Home, `/var`, `/tmp`, `/usr`, or any custom path
  - Top-20 largest files/folders table with sort and min-size filter
  - Optional MD5 duplicate detection
  - Cancellable background scan via `QThread`
- **Memory Monitor** — real-time RAM and swap gauges
- **Process Monitor** — top-15 processes by RSS with PID, user, Mem%, CPU%, status
- **Alert System** — configurable warning/critical thresholds for CPU, RAM, Swap, and Disk
  - Desktop notifications via `notify-send`
  - De-bounced (one notification per level change)
  - Alert history persisted in SQLite
- **Report Export** — one-click JSON and CSV snapshots (disk scan, memory, processes, alerts)
- **Settings** — all thresholds, monitor interval, scan limits, and preferences configurable in-app
- **SQLite persistence** — settings and alert history survive restarts
- **Background launcher** — `run.sh` with start / stop / restart / status / log sub-commands
- **systemd user service** — `ubuntu-storage-analyzer.service` for auto-start on login
- **GNOME desktop integration** — `.desktop` file for Ubuntu app menu
- **Automated setup** — `setup.sh` creates venv and installs all dependencies

---

[Unreleased]: https://github.com/iamvimal-r/ubuntu-storage-analyzer/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/iamvimal-r/ubuntu-storage-analyzer/releases/tag/v1.0.0
