"""
E-Stop Manager - Core functionality for managing emergency stop via GPIO
"""
import json
import os
from pathlib import Path
from typing import Optional
from gpiozero import DigitalInputDevice, DigitalOutputDevice, Device
from enum import Enum
import logging
import platform

# Pi 5 optimization: Prefer lgpio backend for better performance
try:
    from gpiozero.pins.lgpio import LGPIOFactory
    Device.pin_factory = LGPIOFactory()
    _PI5_OPTIMIZED = True
except ImportError:
    # Fallback to default pin factory
    _PI5_OPTIMIZED = False

logger = logging.getLogger(__name__)


class EStopMode(Enum):
    """E-Stop wiring configuration modes"""
    NC = "nc"  # Normally Closed (safer, default)
    NO = "no"  # Normally Open


class EStopState(Enum):
    """E-Stop states"""
    ACTIVE = "active"      # E-stop is engaged
    INACTIVE = "inactive"  # E-stop is not engaged


class EStopManager:
    """Manages emergency stop functionality using GPIO"""
    
    def __init__(self, gpio_pin: int = 4, mode: EStopMode = EStopMode.NC, 
                 config_file: Optional[str] = None):
        """
        Initialize E-Stop Manager
        
        Args:
            gpio_pin: GPIO pin number for e-stop (default: 4)
            mode: E-stop mode (NC or NO, default: NC for safety)
            config_file: Optional config file path for persistence
        """
        self.gpio_pin = gpio_pin
        self.mode = mode
        self.config_file = config_file or str(Path.home() / ".estop_config.json")
        
        # Initialize GPIO
        self._gpio_device = None
        self._current_state = EStopState.INACTIVE
        self._manual_override = False
        
        # Load saved configuration
        self._load_config()
        
        # Initialize GPIO device
        self._init_gpio()
    
    def _init_gpio(self):
        """Initialize GPIO device"""
        try:
            self._gpio_device = DigitalInputDevice(self.gpio_pin, pull_up=True)
            logger.info(f"GPIO pin {self.gpio_pin} initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize GPIO pin {self.gpio_pin}: {e}")
            # For testing without actual GPIO hardware
            self._gpio_device = None
    
    def _load_config(self):
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.mode = EStopMode(config.get('mode', EStopMode.NC.value))
                    self._manual_override = config.get('manual_override', False)
                    logger.info(f"Loaded config: mode={self.mode.value}, manual_override={self._manual_override}")
        except Exception as e:
            logger.warning(f"Could not load config: {e}")
    
    def _save_config(self):
        """Save configuration to file"""
        try:
            config = {
                'mode': self.mode.value,
                'manual_override': self._manual_override,
                'gpio_pin': self.gpio_pin
            }
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            logger.info("Configuration saved")
        except Exception as e:
            logger.error(f"Could not save config: {e}")
    
    def _read_gpio_state(self) -> bool:
        """Read current GPIO state"""
        if self._gpio_device is None:
            # Simulate GPIO for testing
            return not self._manual_override
        
        try:
            return self._gpio_device.is_active
        except Exception as e:
            logger.error(f"Error reading GPIO: {e}")
            return False
    
    def get_estop_state(self) -> EStopState:
        """
        Get current e-stop state based on GPIO reading and configuration
        
        Returns:
            Current e-stop state (ACTIVE or INACTIVE)
        """
        if self._manual_override:
            return EStopState.ACTIVE
        
        gpio_active = self._read_gpio_state()
        
        # Interpret GPIO state based on wiring mode
        if self.mode == EStopMode.NC:
            # Normally Closed: Active when GPIO goes low (circuit broken)
            estop_active = not gpio_active
        else:
            # Normally Open: Active when GPIO goes high (circuit closed)
            estop_active = gpio_active
        
        self._current_state = EStopState.ACTIVE if estop_active else EStopState.INACTIVE
        return self._current_state
    
    def activate_estop(self) -> bool:
        """
        Manually activate e-stop (software override)
        
        Returns:
            True if successfully activated
        """
        try:
            self._manual_override = True
            self._current_state = EStopState.ACTIVE
            self._save_config()
            logger.info("E-stop manually activated")
            return True
        except Exception as e:
            logger.error(f"Failed to activate e-stop: {e}")
            return False
    
    def reset_estop(self) -> bool:
        """
        Reset/clear e-stop state (remove manual override)
        
        Returns:
            True if successfully reset
        """
        try:
            self._manual_override = False
            self._save_config()
            logger.info("E-stop reset (manual override cleared)")
            return True
        except Exception as e:
            logger.error(f"Failed to reset e-stop: {e}")
            return False
    
    def set_mode(self, mode: EStopMode) -> bool:
        """
        Set e-stop wiring mode (NC or NO)
        
        Args:
            mode: EStopMode.NC or EStopMode.NO
            
        Returns:
            True if successfully set
        """
        try:
            self.mode = mode
            self._save_config()
            logger.info(f"E-stop mode set to {mode.value}")
            return True
        except Exception as e:
            logger.error(f"Failed to set mode: {e}")
            return False
    
    def get_status(self) -> dict:
        """
        Get comprehensive status information
        
        Returns:
            Dictionary with status information
        """
        current_state = self.get_estop_state()
        gpio_state = self._read_gpio_state()
        
        # Detect Pi model for optimization info
        pi_model = "Unknown"
        try:
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = f.read()
                if 'BCM2712' in cpuinfo:  # Pi 5 processor
                    pi_model = "Raspberry Pi 5"
                elif 'BCM2711' in cpuinfo:  # Pi 4 processor  
                    pi_model = "Raspberry Pi 4"
                elif 'BCM' in cpuinfo:
                    pi_model = "Raspberry Pi (older model)"
        except:
            if platform.system() == "Darwin":
                pi_model = "macOS (simulation)"
            else:
                pi_model = "Non-Pi system"
        
        return {
            'estop_state': current_state.value,
            'gpio_pin': self.gpio_pin,
            'gpio_active': gpio_state,
            'mode': self.mode.value,
            'manual_override': self._manual_override,
            'gpio_available': self._gpio_device is not None,
            'pi_model': pi_model,
            'pi5_optimized': _PI5_OPTIMIZED,
            'gpio_backend': str(type(Device.pin_factory).__name__) if Device.pin_factory else "None"
        }
    
    def cleanup(self):
        """Clean up GPIO resources"""
        if self._gpio_device:
            try:
                self._gpio_device.close()
                logger.info("GPIO resources cleaned up")
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")
