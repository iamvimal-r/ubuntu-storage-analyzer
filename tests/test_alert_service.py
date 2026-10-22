"""
tests/test_alert_service.py — Unit tests for the alert service.
"""
import time
import unittest
from unittest.mock import MagicMock

from services.alert_service import AlertEvent, AlertLevel, AlertService, Thresholds


class TestAlertClassification(unittest.TestCase):
    def setUp(self):
        self.svc = AlertService(Thresholds(
            disk_warning=80, disk_critical=90,
            ram_warning=80, ram_critical=90,
            swap_warning=70, swap_critical=90,
        ))

    def test_ok_below_threshold(self):
        level = self.svc._classify("disk", 50.0)
        self.assertEqual(level, AlertLevel.OK)

    def test_warning_at_threshold(self):
        level = self.svc._classify("disk", 80.0)
        self.assertEqual(level, AlertLevel.WARNING)

    def test_critical_at_threshold(self):
        level = self.svc._classify("disk", 90.0)
        self.assertEqual(level, AlertLevel.CRITICAL)

    def test_ram_warning(self):
        self.assertEqual(self.svc._classify("ram", 85.0), AlertLevel.WARNING)

    def test_swap_warning(self):
        self.assertEqual(self.svc._classify("swap", 75.0), AlertLevel.WARNING)


class TestAlertDebounce(unittest.TestCase):
    def setUp(self):
        self.callback = MagicMock()
        self.svc = AlertService(
            Thresholds(disk_warning=80, disk_critical=90),
            ui_callback=self.callback,
        )

    def test_fires_once_for_sustained_condition(self):
        # Patch out desktop notification
        self.svc._send_desktop_notification = MagicMock()
        self.svc.check("disk", 85.0, "Disk")
        self.svc.check("disk", 86.0, "Disk")
        self.svc.check("disk", 87.0, "Disk")
        self.assertEqual(self.callback.call_count, 1)

    def test_fires_again_after_recovery(self):
        self.svc._send_desktop_notification = MagicMock()
        self.svc.check("disk", 85.0, "Disk")  # fires
        self.svc.check("disk", 50.0, "Disk")  # recovers
        self.svc.check("disk", 85.0, "Disk")  # fires again
        self.assertEqual(self.callback.call_count, 2)

    def test_escalates_from_warning_to_critical(self):
        self.svc._send_desktop_notification = MagicMock()
        self.svc.check("disk", 85.0, "Disk")  # WARNING — fires
        self.svc.check("disk", 92.0, "Disk")  # CRITICAL — fires again
        self.assertEqual(self.callback.call_count, 2)


if __name__ == "__main__":
    unittest.main()
