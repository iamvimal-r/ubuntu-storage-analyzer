"""
storage_scanner.py — Safe filesystem scanner for large files and directories.
"""
from __future__ import annotations

import hashlib
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, Generator, List, Optional, Set

logger = logging.getLogger(__name__)

# Virtual / temporary filesystem mount points to skip
SKIP_PATHS: Set[str] = {"/proc", "/sys", "/dev", "/run"}
SKIP_FS_TYPES: Set[str] = {
    "proc", "sysfs", "devtmpfs", "devpts", "tmpfs", "cgroup", "cgroup2",
    "pstore", "securityfs", "debugfs", "hugetlbfs", "mqueue", "autofs",
    "binfmt_misc", "overlay", "squashfs",
}


@dataclass
class FileEntry:
    path: str
    size: int           # bytes
    mtime: float        # Unix timestamp
    is_dir: bool
    file_type: str      # extension or "Directory" / "Unknown"
    md5: Optional[str] = None   # filled only if duplicate detection enabled


@dataclass
class ScanResult:
    root: str
    entries: List[FileEntry] = field(default_factory=list)
    total_size: int = 0
    total_files: int = 0
    total_dirs: int = 0
    skipped: int = 0
    cancelled: bool = False


def _get_file_type(path: str, is_dir: bool) -> str:
    if is_dir:
        return "Directory"
    ext = Path(path).suffix.lower()
    return ext if ext else "Unknown"


def _compute_md5(path: str, chunk_size: int = 65536) -> Optional[str]:
    h = hashlib.md5()
    try:
        with open(path, "rb") as f:
            while chunk := f.read(chunk_size):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


def _should_skip(path: str) -> bool:
    return any(path == sp or path.startswith(sp + "/") for sp in SKIP_PATHS)


def scan_directory(
    root: str,
    *,
    min_size_bytes: int = 0,
    follow_symlinks: bool = False,
    detect_duplicates: bool = False,
    cancel_flag: Optional[Callable[[], bool]] = None,
    progress_callback: Optional[Callable[[int, int], None]] = None,
    max_entries: int = 10_000,
) -> ScanResult:
    """
    Walk *root* and collect file/dir entries.

    Args:
        root: Directory to scan.
        min_size_bytes: Ignore items smaller than this.
        follow_symlinks: Follow symbolic links (default False).
        detect_duplicates: Compute MD5 for regular files.
        cancel_flag: Callable that returns True when scan should stop.
        progress_callback: Called with (files_scanned, bytes_scanned).
        max_entries: Hard upper limit on collected entries.

    Returns:
        ScanResult
    """
    result = ScanResult(root=root)
    seen_inodes: Set[int] = set()
    files_scanned = 0
    bytes_scanned = 0

    def is_cancelled() -> bool:
        return cancel_flag is not None and cancel_flag()

    for dirpath, dirnames, filenames, dir_fd in os.fwalk(
        root,
        follow_symlinks=follow_symlinks,
    ):
        if is_cancelled():
            result.cancelled = True
            break

        if _should_skip(dirpath):
            dirnames.clear()
            continue

        # Add directory entry itself (size = sum computed below, set 0 here)
        try:
            dir_stat = os.stat(dirpath)
        except OSError:
            result.skipped += 1
            dirnames.clear()
            continue

        for name in filenames:
            if is_cancelled():
                result.cancelled = True
                break
            fpath = os.path.join(dirpath, name)
            try:
                st = os.stat(fpath, follow_symlinks=follow_symlinks)
            except OSError:
                result.skipped += 1
                continue

            inode = (st.st_dev, st.st_ino)
            if inode in seen_inodes:
                continue
            seen_inodes.add(inode)

            size = st.st_size
            if size < min_size_bytes:
                continue

            md5 = None
            if detect_duplicates and not os.path.islink(fpath):
                md5 = _compute_md5(fpath)

            entry = FileEntry(
                path=fpath,
                size=size,
                mtime=st.st_mtime,
                is_dir=False,
                file_type=_get_file_type(fpath, False),
                md5=md5,
            )
            result.entries.append(entry)
            result.total_size += size
            result.total_files += 1
            files_scanned += 1
            bytes_scanned += size

            if len(result.entries) >= max_entries:
                result.cancelled = True
                break

            if progress_callback and files_scanned % 50 == 0:
                progress_callback(files_scanned, bytes_scanned)

        result.total_dirs += 1

    if progress_callback:
        progress_callback(files_scanned, bytes_scanned)

    return result


def find_duplicates(entries: List[FileEntry]) -> Dict[str, List[FileEntry]]:
    """Group file entries by MD5 hash. Returns only groups with >1 entry."""
    groups: Dict[str, List[FileEntry]] = {}
    for entry in entries:
        if entry.md5:
            groups.setdefault(entry.md5, []).append(entry)
    return {h: lst for h, lst in groups.items() if len(lst) > 1}


def get_top_entries(entries: List[FileEntry], n: int = 20) -> List[FileEntry]:
    return sorted(entries, key=lambda e: e.size, reverse=True)[:n]


def format_size(size_bytes: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024  # type: ignore[assignment]
    return f"{size_bytes:.1f} PB"
