"""
tests/test_system_monitor.py — Unit tests for system monitoring.
"""
import unittest
from services.system_monitor import (
    collect_system_stats,
    format_bytes,
    format_uptime,
    get_cpu_stats,
    get_disk_partitions,
    get_memory_stats,
    get_uptime,
)


class TestFormatBytes(unittest.TestCase):
    def test_bytes(self):
        self.assertIn("B", format_bytes(500))

    def test_kb(self):
        self.assertIn("KB", format_bytes(1500))

    def test_mb(self):
        self.assertIn("MB", format_bytes(5 * 1024 * 1024))

    def test_gb(self):
        self.assertIn("GB", format_bytes(2 * 1024 ** 3))


class TestFormatUptime(unittest.TestCase):
    def test_minutes(self):
        result = format_uptime(300)
        self.assertIn("m", result)

    def test_hours(self):
        result = format_uptime(7200)
        self.assertIn("h", result)

    def test_days(self):
        result = format_uptime(90000)
        self.assertIn("d", result)


class TestCpuStats(unittest.TestCase):
    def test_returns_stats(self):
        stats = get_cpu_stats()
        self.assertGreaterEqual(stats.percent, 0)
        self.assertLessEqual(stats.percent, 100)
        self.assertGreater(stats.count_logical, 0)


class TestMemoryStats(unittest.TestCase):
    def test_returns_stats(self):
        mem = get_memory_stats()
        self.assertGreater(mem.total, 0)
        self.assertGreaterEqual(mem.used, 0)
        self.assertGreaterEqual(mem.percent, 0)


class TestDiskPartitions(unittest.TestCase):
    def test_has_partitions(self):
        parts = get_disk_partitions()
        self.assertIsInstance(parts, list)

    def test_root_partition_exists(self):
        parts = get_disk_partitions()
        mounts = [p.mountpoint for p in parts]
        self.assertIn("/", mounts)


class TestCollectStats(unittest.TestCase):
    def test_full_stats(self):
        stats = collect_system_stats()
        self.assertIsNotNone(stats.cpu)
        self.assertIsNotNone(stats.memory)
        self.assertGreater(stats.uptime_seconds, 0)


if __name__ == "__main__":
    unittest.main()
