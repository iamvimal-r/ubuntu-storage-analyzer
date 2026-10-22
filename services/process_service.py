"""
process_service.py — Top memory-consuming processes.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List

import psutil

logger = logging.getLogger(__name__)


@dataclass
class ProcessInfo:
    pid: int
    name: str
    username: str
    rss: int        # Resident Set Size in bytes
    vms: int        # Virtual Memory Size in bytes
    mem_percent: float
    cpu_percent: float
    status: str


def get_top_processes(limit: int = 15) -> List[ProcessInfo]:
    """Return top processes sorted by RSS memory usage."""
    results: List[ProcessInfo] = []
    for proc in psutil.process_iter(
        ["pid", "name", "username", "memory_info", "memory_percent", "cpu_percent", "status"]
    ):
        try:
            info = proc.info
            mem_info = info.get("memory_info")
            if mem_info is None:
                continue
            results.append(
                ProcessInfo(
                    pid=info["pid"],
                    name=info.get("name") or "?",
                    username=info.get("username") or "?",
                    rss=mem_info.rss,
                    vms=mem_info.vms,
                    mem_percent=info.get("memory_percent") or 0.0,
                    cpu_percent=info.get("cpu_percent") or 0.0,
                    status=info.get("status") or "?",
                )
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
        except Exception as exc:
            logger.debug("Error reading process: %s", exc)

    results.sort(key=lambda p: p.rss, reverse=True)
    return results[:limit]
