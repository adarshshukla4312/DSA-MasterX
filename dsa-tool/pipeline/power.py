"""
DSA Mastery Tool — System Power & Hardware Detection
Provides zero-dependency, low-latency Windows power status detection via Win32 API.
"""
import ctypes
from ctypes import wintypes
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class SYSTEM_POWER_STATUS(ctypes.Structure):
    _fields_ = [
        ('ACLineStatus', wintypes.BYTE),
        ('BatteryFlag', wintypes.BYTE),
        ('BatteryLifePercent', wintypes.BYTE),
        ('SystemStatusFlag', wintypes.BYTE),
        ('BatteryLifeTime', wintypes.DWORD),
        ('BatteryFullLifeTime', wintypes.DWORD)
    ]


@dataclass
class PowerStatus:
    is_plugged_in: bool
    battery_percent: int
    ac_line_status: int
    status_text: str


def get_power_status() -> PowerStatus:
    """
    Queries Windows kernel for AC power and battery level.
    ACLineStatus:
      0: Offline (Running on battery)
      1: Online (Plugged into AC power)
      255: Unknown status (typically desktop workstation or AC without battery)
    """
    try:
        if hasattr(ctypes, 'windll') and hasattr(ctypes.windll, 'kernel32'):
            status = SYSTEM_POWER_STATUS()
            success = ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(status))
            if success:
                ac_status = int(status.ACLineStatus)
                battery_pct = int(status.BatteryLifePercent)
                
                # ACLineStatus == 1 is plugged in, 255 is desktop/unknown (treat as plugged in)
                is_plugged_in = ac_status in (1, 255)
                
                if ac_status == 1:
                    txt = f"AC Power (Plugged in, {battery_pct}%)" if battery_pct <= 100 else "AC Power (Plugged in)"
                elif ac_status == 0:
                    txt = f"Battery Power ({battery_pct}%)"
                else:
                    txt = "AC/Unknown Power"
                    
                return PowerStatus(
                    is_plugged_in=is_plugged_in,
                    battery_percent=battery_pct,
                    ac_line_status=ac_status,
                    status_text=txt
                )
    except Exception as e:
        logger.warning(f"Failed to query GetSystemPowerStatus ({e}). Defaulting to plugged in.")

    return PowerStatus(
        is_plugged_in=True,
        battery_percent=100,
        ac_line_status=1,
        status_text="Desktop / Unrestricted AC"
    )
