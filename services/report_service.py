"""
report_service.py — CSV and JSON report generation.
"""
from __future__ import annotations

import csv
import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from services.alert_service import AlertEvent
from services.storage_scanner import FileEntry, ScanResult, format_size
from services.system_monitor import MemoryStats, format_bytes

logger = logging.getLogger(__name__)


def _make_report_data(
    scan_result: Optional[ScanResult],
    mem_stats: Optional[MemoryStats],
    top_files: List[FileEntry],
    processes: Optional[List[Any]],
    alerts: List[AlertEvent],
) -> Dict[str, Any]:
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    data: Dict[str, Any] = {"generated_at": ts}

    if scan_result:
        data["disk_scan"] = {
            "root": scan_result.root,
            "total_files": scan_result.total_files,
            "total_dirs": scan_result.total_dirs,
            "total_size_bytes": scan_result.total_size,
            "total_size_human": format_size(scan_result.total_size),
            "skipped": scan_result.skipped,
        }
        data["largest_files"] = [
            {
                "path": e.path,
                "size_bytes": e.size,
                "size_human": format_size(e.size),
                "type": e.file_type,
                "modified": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(e.mtime)),
            }
            for e in top_files
        ]

    if mem_stats:
        data["memory"] = {
            "total": format_bytes(mem_stats.total),
            "used": format_bytes(mem_stats.used),
            "available": format_bytes(mem_stats.available),
            "percent": mem_stats.percent,
            "swap_total": format_bytes(mem_stats.swap_total),
            "swap_used": format_bytes(mem_stats.swap_used),
            "swap_percent": mem_stats.swap_percent,
        }

    if processes:
        data["top_processes"] = [
            {
                "pid": p.pid,
                "name": p.name,
                "rss": format_bytes(p.rss),
                "mem_percent": round(p.mem_percent, 2),
            }
            for p in processes
        ]

    data["alert_history"] = [
        {
            "time": a.time_str,
            "resource": a.resource,
            "level": a.level.value,
            "value": round(a.value, 2),
            "message": a.message,
        }
        for a in alerts
    ]
    return data


def export_json(path: str, **kwargs: Any) -> None:
    data = _make_report_data(**kwargs)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    logger.info("JSON report saved to %s", path)


def export_csv(path: str, **kwargs: Any) -> None:
    data = _make_report_data(**kwargs)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Generated At", data.get("generated_at", "")])
        writer.writerow([])

        if "disk_scan" in data:
            writer.writerow(["=== Disk Scan ==="])
            for k, v in data["disk_scan"].items():
                writer.writerow([k, v])
            writer.writerow([])

        if "largest_files" in data:
            writer.writerow(["=== Largest Files ==="])
            writer.writerow(["Path", "Size", "Type", "Modified"])
            for entry in data["largest_files"]:
                writer.writerow([
                    entry["path"],
                    entry["size_human"],
                    entry["type"],
                    entry["modified"],
                ])
            writer.writerow([])

        if "memory" in data:
            writer.writerow(["=== Memory ==="])
            for k, v in data["memory"].items():
                writer.writerow([k, v])
            writer.writerow([])

        if "top_processes" in data:
            writer.writerow(["=== Top Processes ==="])
            writer.writerow(["PID", "Name", "RSS", "Mem%"])
            for p in data["top_processes"]:
                writer.writerow([p["pid"], p["name"], p["rss"], p["mem_percent"]])
            writer.writerow([])

        if "alert_history" in data:
            writer.writerow(["=== Alert History ==="])
            writer.writerow(["Time", "Resource", "Level", "Value%", "Message"])
            for a in data["alert_history"]:
                writer.writerow([a["time"], a["resource"], a["level"], a["value"], a["message"]])

    logger.info("CSV report saved to %s", path)
