"""
tests/test_storage_scanner.py — Unit tests for the storage scanner.
"""
import os
import tempfile
import time
import unittest

from services.storage_scanner import (
    FileEntry,
    ScanResult,
    find_duplicates,
    format_size,
    get_top_entries,
    scan_directory,
)


class TestFormatSize(unittest.TestCase):
    def test_zero(self):
        self.assertEqual(format_size(0), "0.0 B")

    def test_mb(self):
        self.assertIn("MB", format_size(5 * 1024 * 1024))


class TestScanDirectory(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _write(self, name: str, size: int) -> str:
        path = os.path.join(self.tmpdir, name)
        with open(path, "wb") as f:
            f.write(b"x" * size)
        return path

    def test_scan_finds_files(self):
        self._write("a.txt", 1024)
        self._write("b.txt", 2048)
        result = scan_directory(self.tmpdir)
        self.assertEqual(result.total_files, 2)

    def test_min_size_filter(self):
        self._write("small.txt", 100)
        self._write("large.txt", 5000)
        result = scan_directory(self.tmpdir, min_size_bytes=1000)
        paths = [e.path for e in result.entries]
        self.assertTrue(any("large" in p for p in paths))
        self.assertFalse(any("small" in p for p in paths))

    def test_cancellation(self):
        for i in range(20):
            self._write(f"file{i}.txt", 100)
        result = scan_directory(self.tmpdir, cancel_flag=lambda: True)
        self.assertTrue(result.cancelled)

    def test_total_size_accumulates(self):
        self._write("x.bin", 4096)
        result = scan_directory(self.tmpdir)
        self.assertGreaterEqual(result.total_size, 4096)


class TestGetTopEntries(unittest.TestCase):
    def _make_entry(self, size: int) -> FileEntry:
        return FileEntry(
            path=f"/fake/{size}",
            size=size,
            mtime=time.time(),
            is_dir=False,
            file_type=".bin",
        )

    def test_top_n(self):
        entries = [self._make_entry(i * 100) for i in range(30)]
        top = get_top_entries(entries, 5)
        self.assertEqual(len(top), 5)
        self.assertEqual(top[0].size, 2900)


class TestFindDuplicates(unittest.TestCase):
    def _entry(self, md5: str) -> FileEntry:
        return FileEntry(
            path=f"/fake/{md5}",
            size=1000,
            mtime=time.time(),
            is_dir=False,
            file_type=".bin",
            md5=md5,
        )

    def test_detects_duplicates(self):
        entries = [self._entry("abc123"), self._entry("abc123"), self._entry("xyz999")]
        dups = find_duplicates(entries)
        self.assertIn("abc123", dups)
        self.assertNotIn("xyz999", dups)
        self.assertEqual(len(dups["abc123"]), 2)


if __name__ == "__main__":
    unittest.main()
