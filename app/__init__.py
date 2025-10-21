"""
E-Stop Manager - Emergency stop control via GPIO

This module provides both CLI and library interfaces for managing emergency stops
using GPIO pins on Raspberry Pi or compatible single-board computers.

Usage as a library:
    from app import EStopManager, EStopMode, EStopState
    
    # Create manager instance
    estop = EStopManager(gpio_pin=4, mode=EStopMode.NC)
    
    # Check status
    status = estop.get_status()
    
    # Activate e-stop
    estop.activate_estop()
    
    # Reset e-stop
    estop.reset_estop()
    
    # Clean up when done
    estop.cleanup()

Usage as CLI:
    uv run python -m app estop    # Activate e-stop
    uv run python -m app reset    # Reset e-stop
    uv run python -m app status   # Show status
    uv run python -m app config --mode nc  # Configure mode
    uv run python -m app monitor  # Monitor in real-time
"""

from src.estop_manager import EStopManager, EStopMode, EStopState

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

# Convenience functions for quick library usage
def create_estop_manager(gpio_pin: int = 4, mode: EStopMode = EStopMode.NC) -> EStopManager:
    """
    Create and return an EStopManager instance with common defaults
    
    Args:
        gpio_pin: GPIO pin number (default: 4)
        mode: E-stop mode (default: NC for safety)
        
    Returns:
        Configured EStopManager instance
    """
    return EStopManager(gpio_pin=gpio_pin, mode=mode)


def quick_estop_status(gpio_pin: int = 4) -> dict:
    """
    Quick status check without maintaining a persistent manager instance
    
    Args:
        gpio_pin: GPIO pin number (default: 4)
        
    Returns:
        Dictionary with current status
    """
    manager = EStopManager(gpio_pin=gpio_pin)
    try:
        return manager.get_status()
    finally:
        manager.cleanup()


def quick_activate_estop(gpio_pin: int = 4) -> bool:
    """
    Quick e-stop activation without maintaining a persistent manager instance
    
    Args:
        gpio_pin: GPIO pin number (default: 4)
        
    Returns:
        True if successfully activated
    """
    manager = EStopManager(gpio_pin=gpio_pin)
    try:
        return manager.activate_estop()
    finally:
        manager.cleanup()


def quick_reset_estop(gpio_pin: int = 4) -> bool:
    """
    Quick e-stop reset without maintaining a persistent manager instance
    
    Args:
        gpio_pin: GPIO pin number (default: 4)
        
    Returns:
        True if successfully reset
    """
    manager = EStopManager(gpio_pin=gpio_pin)
    try:
        return manager.reset_estop()
    finally:
        manager.cleanup()


# Add convenience functions to __all__
__all__.extend([
    "create_estop_manager",
    "quick_estop_status", 
    "quick_activate_estop",
    "quick_reset_estop"
])
