"""
system_monitor.py — CPU, RAM, swap, disk, and uptime monitoring.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import List

import psutil

logger = logging.getLogger(__name__)

EXCLUDED_FS_TYPES = {
    "proc", "sysfs", "devtmpfs", "devpts", "tmpfs", "cgroup",
    "cgroup2", "pstore", "securityfs", "debugfs", "hugetlbfs",
    "mqueue", "fusectl", "autofs", "binfmt_misc", "overlay",
    "squashfs",
}

EXCLUDED_MOUNT_PREFIXES = ("/proc", "/sys", "/dev", "/run")


@dataclass
class CpuStats:
    percent: float
    count_logical: int
    count_physical: int
    freq_current: float  # MHz


@dataclass
class MemoryStats:
    total: int       # bytes
    used: int
    available: int
    percent: float
    swap_total: int
    swap_used: int
    swap_free: int
    swap_percent: float


@dataclass
class DiskPartitionStats:
    device: str
    mountpoint: str
    fstype: str
    total: int
    used: int
    free: int
    percent: float


@dataclass
class SystemStats:
    cpu: CpuStats
    memory: MemoryStats
    partitions: List[DiskPartitionStats] = field(default_factory=list)
    uptime_seconds: float = 0.0


def get_cpu_stats() -> CpuStats:
    freq = psutil.cpu_freq()
    return CpuStats(
        percent=psutil.cpu_percent(interval=None),
        count_logical=psutil.cpu_count(logical=True),
        count_physical=psutil.cpu_count(logical=False) or 1,
        freq_current=freq.current if freq else 0.0,
    )


def get_memory_stats() -> MemoryStats:
    vm = psutil.virtual_memory()
    sw = psutil.swap_memory()
    return MemoryStats(
        total=vm.total,
        used=vm.used,
        available=vm.available,
        percent=vm.percent,
        swap_total=sw.total,
        swap_used=sw.used,
        swap_free=sw.free,
        swap_percent=sw.percent,
    )


def get_disk_partitions() -> List[DiskPartitionStats]:
    results: List[DiskPartitionStats] = []
    try:
        partitions = psutil.disk_partitions(all=False)
    except Exception as exc:
        logger.warning("Could not list disk partitions: %s", exc)
        return results

    for part in partitions:
        if part.fstype.lower() in EXCLUDED_FS_TYPES:
            continue
        if any(part.mountpoint.startswith(pfx) for pfx in EXCLUDED_MOUNT_PREFIXES):
            continue
        try:
            usage = psutil.disk_usage(part.mountpoint)
        except PermissionError:
            logger.debug("Permission denied: %s", part.mountpoint)
            continue
        except OSError as exc:
            logger.debug("OSError for %s: %s", part.mountpoint, exc)
            continue
        results.append(
            DiskPartitionStats(
                device=part.device,
                mountpoint=part.mountpoint,
                fstype=part.fstype,
                total=usage.total,
                used=usage.used,
                free=usage.free,
                percent=usage.percent,
            )
        )
    return results


def get_uptime() -> float:
    return time.time() - psutil.boot_time()


def format_bytes(n: int) -> str:
    """Human-readable byte size."""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024  # type: ignore[assignment]
    return f"{n:.1f} PB"


def format_uptime(seconds: float) -> str:
    seconds = int(seconds)
    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, secs = divmod(rem, 60)
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    parts.append(f"{minutes}m {secs}s")
    return " ".join(parts)


def collect_system_stats() -> SystemStats:
    return SystemStats(
        cpu=get_cpu_stats(),
        memory=get_memory_stats(),
        partitions=get_disk_partitions(),
        uptime_seconds=get_uptime(),
    )
