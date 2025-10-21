"""
E-Stop Manager - Core functionality for managing emergency stop via GPIO
"""
import json
import os
from pathlib import Path
from typing import Optional
from enum import Enum
import logging
import platform
import traceback

logger = logging.getLogger(__name__)

# Log module initialization
logger.info("=== EStopManager Module Initializing ===")

# Import GPIO libraries with detailed logging
try:
    logger.info("Importing gpiozero...")
    from gpiozero import DigitalInputDevice, DigitalOutputDevice, Device
    logger.info("✓ gpiozero imported successfully")
except ImportError as e:
    logger.error(f"✗ Failed to import gpiozero: {e}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    raise ImportError(f"gpiozero import failed: {e}") from e
except Exception as e:
    logger.error(f"✗ Unexpected error importing gpiozero: {e}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    raise

# Pi 5 optimization: Prefer lgpio backend for better performance
logger.info("Attempting Pi 5 optimization with lgpio backend...")
try:
    logger.info("Importing LGPIOFactory...")
    from gpiozero.pins.lgpio import LGPIOFactory
    logger.info("✓ LGPIOFactory imported successfully")
    
    logger.info("Setting LGPIOFactory as pin factory...")
    Device.pin_factory = LGPIOFactory()
    _PI5_OPTIMIZED = True
    logger.info("✓ Pi 5 optimization successful - lgpio backend active")
except ImportError as e:
    logger.warning(f"⚠ lgpio not available: {e}")
    logger.info("Falling back to default pin factory")
    _PI5_OPTIMIZED = False
except Exception as e:
    logger.warning(f"⚠ Unexpected error setting up lgpio: {e}")
    logger.info("Falling back to default pin factory")
    _PI5_OPTIMIZED = False

logger.info(f"GPIO backend initialization complete. Pi5 optimized: {_PI5_OPTIMIZED}")


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
        logger.info(f"=== EStopManager.__init__ called ===")
        logger.info(f"Parameters: gpio_pin={gpio_pin}, mode={mode}, config_file={config_file}")
        
        self.gpio_pin = gpio_pin
        self.mode = mode
        self.config_file = config_file or str(Path.home() / ".estop_config.json")
        logger.info(f"Config file path: {self.config_file}")
        
        # Initialize GPIO
        self._gpio_device = None
        self._current_state = EStopState.INACTIVE
        self._manual_override = False
        logger.info("Initial state variables set")
        
        # Load saved configuration
        logger.info("Loading saved configuration...")
        self._load_config()
        
        # Initialize GPIO device
        logger.info("Initializing GPIO device...")
        self._init_gpio()
        
        logger.info(f"✓ EStopManager initialization complete")
        logger.info(f"Final state: gpio_pin={self.gpio_pin}, mode={self.mode.value}, gpio_device={'Available' if self._gpio_device else 'None'}")
    
    def _init_gpio(self):
        """Initialize GPIO device as output for software e-stop control"""
        logger.info(f"Attempting to initialize GPIO pin {self.gpio_pin} as OUTPUT")
        logger.info(f"Current pin factory: {type(Device.pin_factory).__name__ if Device.pin_factory else 'None'}")
        
        try:
            logger.info("Creating DigitalOutputDevice...")
            self._gpio_device = DigitalOutputDevice(self.gpio_pin)
            logger.info(f"✓ GPIO pin {self.gpio_pin} initialized successfully as output")
            logger.info(f"GPIO device type: {type(self._gpio_device)}")
            
            # Set initial state based on current e-stop state
            self._update_gpio_output()
            logger.info("Initial GPIO output state set")
            
        except Exception as e:
            logger.error(f"✗ Failed to initialize GPIO pin {self.gpio_pin}: {e}")
            logger.error(f"Exception type: {type(e).__name__}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            logger.warning("Setting GPIO device to None (simulation mode)")
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
    
    def _update_gpio_output(self):
        """Update GPIO output based on current e-stop state and mode"""
        if self._gpio_device is None:
            logger.debug("No GPIO device available, skipping output update")
            return
        
        try:
            # Determine what the GPIO output should be
            estop_active = self._manual_override or self._current_state == EStopState.ACTIVE
            
            if self.mode == EStopMode.NC:
                # Normally Closed: Output HIGH when inactive, LOW when active (estop engaged)
                gpio_output = not estop_active
            else:
                # Normally Open: Output LOW when inactive, HIGH when active (estop engaged)  
                gpio_output = estop_active
            
            # Set the GPIO output
            if gpio_output:
                self._gpio_device.on()
                logger.debug(f"GPIO pin {self.gpio_pin} set to HIGH")
            else:
                self._gpio_device.off()
                logger.debug(f"GPIO pin {self.gpio_pin} set to LOW")
                
        except Exception as e:
            logger.error(f"Error updating GPIO output: {e}")

    def _read_gpio_state(self) -> bool:
        """Read current GPIO output state"""
        if self._gpio_device is None:
            # Simulate GPIO for testing - return state based on manual override
            if self.mode == EStopMode.NC:
                return not self._manual_override
            else:
                return self._manual_override
        
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
            self._update_gpio_output()  # Update GPIO output immediately
            self._save_config()
            logger.info("E-stop manually activated - GPIO output updated")
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
            self._current_state = EStopState.INACTIVE
            self._update_gpio_output()  # Update GPIO output immediately
            self._save_config()
            logger.info("E-stop reset (manual override cleared) - GPIO output updated")
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
        """Clean up GPIO resources and set safe state"""
        if self._gpio_device:
            try:
                # Before cleanup, set GPIO to safe state (e-stop active)
                logger.info("Setting GPIO to safe state before cleanup...")
                self._set_safe_state()
                
                # Brief delay to ensure state is set
                import time
                time.sleep(0.1)
                
                self._gpio_device.close()
                logger.info("GPIO resources cleaned up after setting safe state")
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")
    
    def _set_safe_state(self):
        """Set GPIO to safe state (e-stop active) for shutdown"""
        if self._gpio_device is None:
            logger.debug("No GPIO device available, skipping safe state setting")
            return
            
        try:
            # Safe state = e-stop active
            if self.mode == EStopMode.NC:
                # NC Mode: Safe state is LOW (e-stop active)
                self._gpio_device.off()
                logger.info("Set safe state: GPIO pin LOW (NC mode - e-stop active)")
            else:
                # NO Mode: Safe state is HIGH (e-stop active)  
                self._gpio_device.on()
                logger.info("Set safe state: GPIO pin HIGH (NO mode - e-stop active)")
                
        except Exception as e:
            logger.error(f"Error setting safe state: {e}")
