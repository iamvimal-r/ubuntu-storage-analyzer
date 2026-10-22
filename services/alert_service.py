"""
alert_service.py — Warning thresholds, desktop notifications, and sound alerts.
"""
from __future__ import annotations

import logging
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

NOTIFY_SEND = shutil.which("notify-send")


class AlertLevel(Enum):
    OK = "ok"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class Thresholds:
    disk_warning: float = 80.0
    disk_critical: float = 90.0
    ram_warning: float = 80.0
    ram_critical: float = 90.0
    swap_warning: float = 70.0
    swap_critical: float = 90.0
    cpu_warning: float = 80.0
    cpu_critical: float = 95.0


@dataclass
class AlertEvent:
    timestamp: float
    resource: str        # "disk", "ram", "swap", "cpu"
    level: AlertLevel
    value: float
    message: str

    @property
    def time_str(self) -> str:
        import datetime
        return datetime.datetime.fromtimestamp(self.timestamp).strftime("%Y-%m-%d %H:%M:%S")


class AlertService:
    """
    Evaluates resource usage against thresholds and fires:
      1. A desktop notification (notify-send)
      2. An audio alert (paplay / aplay with freedesktop OGA files)
      3. A UI callback for in-app display

    Notifications are de-bounced: a notification fires only when the level
    *rises* (OK→WARNING, OK/WARNING→CRITICAL).  It fires again only after the
    resource has recovered to OK and then crosses the threshold again.
    """

    # Freedesktop sound files --------------------------------------------------
    _SOUND_WARNING  = "/usr/share/sounds/freedesktop/stereo/dialog-warning.oga"
    _SOUND_CRITICAL = "/usr/share/sounds/freedesktop/stereo/dialog-error.oga"
    _SOUND_ALARM    = "/usr/share/sounds/freedesktop/stereo/alarm-clock-elapsed.oga"

    def __init__(
        self,
        thresholds: Optional[Thresholds] = None,
        ui_callback: Optional[Callable[[AlertEvent], None]] = None,
        sound_enabled: bool = True,
    ):
        self.thresholds = thresholds or Thresholds()
        self.ui_callback = ui_callback
        self.sound_enabled = sound_enabled
        self.history: List[AlertEvent] = []
        self._last_level: Dict[str, AlertLevel] = {}

    # ── Classification ────────────────────────────────────────────────────────

    def _classify(self, resource: str, value: float) -> AlertLevel:
        t = self.thresholds
        mapping = {
            "disk": (t.disk_warning, t.disk_critical),
            "ram":  (t.ram_warning,  t.ram_critical),
            "swap": (t.swap_warning, t.swap_critical),
            "cpu":  (t.cpu_warning,  t.cpu_critical),
        }
        if resource not in mapping:
            return AlertLevel.OK
        warn, crit = mapping[resource]
        if value >= crit:
            return AlertLevel.CRITICAL
        if value >= warn:
            return AlertLevel.WARNING
        return AlertLevel.OK

    # ── Public API ────────────────────────────────────────────────────────────

    def check(self, resource: str, value: float, label: str = "") -> AlertLevel:
        """
        Check *value* against thresholds for *resource*.
        Fires sound + desktop notification + UI callback on level rise.
        Returns the current AlertLevel.
        """
        level = self._classify(resource, value)
        prev = self._last_level.get(resource, AlertLevel.OK)

        if level != AlertLevel.OK and level != prev:
            # Level rose — fire all alerts
            msg = (
                f"{label or resource.title()} usage is {value:.1f}%  "
                f"({'⚠ Warning' if level == AlertLevel.WARNING else '🚨 Critical'})"
            )
            event = AlertEvent(
                timestamp=time.time(),
                resource=resource,
                level=level,
                value=value,
                message=msg,
            )
            self.history.append(event)
            self._send_desktop_notification(event)
            self._play_sound(event)
            if self.ui_callback:
                self.ui_callback(event)

        # Reset on recovery so next crossing triggers again
        if level == AlertLevel.OK and prev != AlertLevel.OK:
            self._last_level[resource] = AlertLevel.OK
        if level != AlertLevel.OK:
            self._last_level[resource] = level

        return level

    # ── Desktop notification ──────────────────────────────────────────────────

    def _send_desktop_notification(self, event: AlertEvent) -> None:
        if not NOTIFY_SEND:
            logger.warning("notify-send not found; skipping desktop notification.")
            return
        urgency = "critical" if event.level == AlertLevel.CRITICAL else "normal"
        icon    = "dialog-error" if event.level == AlertLevel.CRITICAL else "dialog-warning"
        title   = (
            f"🚨 Critical: {event.resource.title()}"
            if event.level == AlertLevel.CRITICAL
            else f"⚠ Warning: {event.resource.title()}"
        )
        try:
            subprocess.run(
                [NOTIFY_SEND, "-u", urgency, "-i", icon, title, event.message],
                timeout=5, check=False,
            )
        except Exception as exc:
            logger.warning("Desktop notification error: %s", exc)

    # ── Sound alerts ──────────────────────────────────────────────────────────

    def _play_sound(self, event: AlertEvent) -> None:
        """
        Play an audio alert in a background daemon thread.

        Sound mapping:
          WARNING  → single dialog-warning chime
          CRITICAL → dialog-error chime
                     + (for cpu / ram / swap / disk) alarm-clock chime after 0.7 s
        """
        if not self.sound_enabled:
            return

        import threading

        first_sound = (
            self._SOUND_CRITICAL
            if event.level == AlertLevel.CRITICAL
            else self._SOUND_WARNING
        )
        play_alarm = (
            event.level == AlertLevel.CRITICAL
            and event.resource in ("cpu", "ram", "swap", "disk")
        )

        def _worker() -> None:
            _paplay(first_sound)
            if play_alarm:
                time.sleep(0.7)
                _paplay(self._SOUND_ALARM)

        thread = threading.Thread(
            target=_worker,
            daemon=True,
            name=f"snd-{event.resource}",
        )
        thread.start()
        logger.debug(
            "Sound alert fired: resource=%s level=%s sound=%s",
            event.resource, event.level.value, first_sound,
        )

    # ── History ───────────────────────────────────────────────────────────────

    def clear_history(self) -> None:
        self.history.clear()

    def get_history(self) -> List[AlertEvent]:
        return list(self.history)


# ── Module-level audio helper ─────────────────────────────────────────────────

_PAPLAY = shutil.which("paplay")
_APLAY  = shutil.which("aplay")


def _paplay(sound_file: str) -> None:
    """
    Play *sound_file* non-blocking using paplay (PulseAudio / PipeWire).
    Falls back to aplay + ffmpeg conversion for .oga files if paplay is absent.
    Errors are always caught — audio failure must never crash the application.
    """
    import os

    if not os.path.isfile(sound_file):
        logger.debug("Sound file not found: %s", sound_file)
        return

    try:
        if _PAPLAY:
            subprocess.run(
                [_PAPLAY, sound_file],
                timeout=8, check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return

        if _APLAY:
            ffmpeg = shutil.which("ffmpeg")
            if ffmpeg and sound_file.endswith(".oga"):
                import tempfile
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    tmp_path = tmp.name
                try:
                    subprocess.run(
                        [ffmpeg, "-y", "-i", sound_file, tmp_path],
                        timeout=5, check=False,
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    )
                    subprocess.run(
                        [_APLAY, "-q", tmp_path],
                        timeout=8, check=False,
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    )
                finally:
                    os.unlink(tmp_path)
            else:
                logger.debug("aplay cannot play .oga without ffmpeg — sound skipped.")
            return

        logger.warning("No audio player found (tried paplay, aplay). Sound alerts disabled.")

    except Exception as exc:
        logger.debug("Sound playback error for %s: %s", sound_file, exc)
