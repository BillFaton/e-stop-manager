"""
E-Stop Manager - Emergency stop control via GPIO

This package provides core functionality for managing emergency stops
using GPIO pins on Raspberry Pi or compatible single-board computers.
"""

from .estop_manager import EStopManager, EStopMode, EStopState

# Version info
__version__ = "0.1.0"
__author__ = "E-Stop Manager"
__description__ = "Emergency stop control via GPIO"

# Public API exports
__all__ = [
    "EStopManager",
    "EStopMode", 
    "EStopState"
]
