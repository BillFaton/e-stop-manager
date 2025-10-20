# E-Stop Manager

A simple and reliable emergency stop manager for Raspberry Pi using GPIO control. This project provides both CLI and library interfaces for managing emergency stops with support for both Normally Closed (NC) and Normally Open (NO) configurations.

## Features

- 🔴 **Emergency Stop Control**: Activate and reset e-stop states via GPIO pin 4
- ⚙️ **Flexible Configuration**: Support for both NC (safer) and NO wiring modes
- 🖥️ **CLI Interface**: Easy-to-use command-line interface with colored output
- 📚 **Library API**: Use as a Python library in your own projects
- 💾 **State Persistence**: Remembers configuration and manual override states
- 🔍 **Real-time Monitoring**: Monitor e-stop state changes in real-time
- 🛡️ **Safety Features**: Graceful fallback and proper GPIO cleanup
- 🧪 **Simulation Mode**: Works without GPIO hardware for testing

## Installation

This project uses [uv](https://github.com/astral-sh/uv) for fast Python package management.

```bash
# Clone the repository
git clone <your-repo-url>
cd e-stop-manager

# Install dependencies (uv will create a virtual environment automatically)
uv add gpiozero click

# For Raspberry Pi 5 - Install lgpio for optimal performance
uv add lgpio
```

### Raspberry Pi 5 Optimization

For the best performance on Raspberry Pi 5, install the lgpio backend:

```bash
# On Raspberry Pi 5, you may need to install system dependencies first
sudo apt update
sudo apt install swig python3-dev

# Then install lgpio for optimal GPIO performance
uv add lgpio
```

The e-stop manager automatically detects and uses the lgpio backend when available, providing:
- Better performance and lower latency
- More reliable GPIO operations  
- Improved compatibility with Pi 5 hardware

## CLI Usage

### Basic Commands

```bash
# Show help
uv run python -m app --help

# Show current e-stop status
uv run python -m app status

# Activate emergency stop
uv run python -m app estop

# Reset/clear emergency stop
uv run python -m app reset

# Show current configuration
uv run python -m app config

# Set e-stop mode (nc = normally closed, no = normally open)
uv run python -m app config --mode nc
uv run python -m app config --mode no

# Monitor e-stop state in real-time (Ctrl+C to stop)
uv run python -m app monitor

# Use verbose logging
uv run python -m app -v status

# Use different GPIO pin
uv run python -m app --gpio-pin 18 status
```

### Example CLI Output

```bash
$ uv run python -m app status
E-Stop Manager Status
====================
State: INACTIVE
GPIO Pin: 4
GPIO Active: True
Mode: NC (Normally Closed)
Manual Override: False
GPIO Available: True

$ uv run python -m app estop
✓ E-stop activated
Status: active

$ uv run python -m app reset
✓ E-stop reset
Status: inactive
```

## Library Usage

You can also use the e-stop manager as a Python library:

### Basic Library Usage

```python
from app import EStopManager, EStopMode, EStopState

# Create manager instance
estop = EStopManager(gpio_pin=4, mode=EStopMode.NC)

# Check current status
status = estop.get_status()
print(f"E-stop state: {status['estop_state']}")

# Activate e-stop
estop.activate_estop()

# Reset e-stop
estop.reset_estop()

# Change configuration
estop.set_mode(EStopMode.NO)

# Clean up when done
estop.cleanup()
```

### Convenience Functions

```python
from app import quick_estop_status, quick_activate_estop, quick_reset_estop

# Quick status check
status = quick_estop_status(gpio_pin=4)

# Quick activate
success = quick_activate_estop(gpio_pin=4)

# Quick reset
success = quick_reset_estop(gpio_pin=4)
```

### Advanced Usage

```python
from app import create_estop_manager, EStopMode

# Create with custom configuration
estop = create_estop_manager(gpio_pin=18, mode=EStopMode.NO)

# Monitor state changes
import time
while True:
    current_state = estop.get_estop_state()
    print(f"Current state: {current_state}")
    time.sleep(1)
```

## GPIO Wiring

### Normally Closed (NC) - Recommended for Safety

```
Raspberry Pi GPIO 4 ----[E-Stop Switch]---- GND
                   |
                 Pull-up resistor (internal)
```

- **Safe State**: Switch closed, GPIO reads HIGH
- **E-Stop Active**: Switch open, GPIO reads LOW
- **Advantage**: If wiring breaks, e-stop automatically activates

### Normally Open (NO)

```
Raspberry Pi GPIO 4 ----[E-Stop Switch]---- 3.3V
                   |
                 Pull-down resistor (external)
```

- **Safe State**: Switch open, GPIO reads LOW  
- **E-Stop Active**: Switch closed, GPIO reads HIGH
- **Note**: Requires external pull-down resistor

## Configuration

The e-stop manager stores configuration in `~/.estop_config.json`:

```json
{
  "mode": "nc",
  "manual_override": false,
  "gpio_pin": 4
}
```

## Safety Features

- **Default NC Mode**: Normally Closed mode is the default for safety
- **State Persistence**: Manual override state survives restarts
- **GPIO Cleanup**: Proper cleanup of GPIO resources
- **Error Handling**: Graceful handling of GPIO initialization failures
- **Simulation Mode**: Works without GPIO hardware for development/testing

## Hardware Requirements

- Raspberry Pi (any model with GPIO)
- E-stop switch (normally closed recommended)
- Optional: External pull-down resistor for NO mode

## Development

### Project Structure

```
e-stop-manager/
├── app/
│   ├── __init__.py          # Library exports and convenience functions
│   ├── __main__.py          # Module entry point
│   ├── cli.py               # CLI interface with Click
│   └── estop_manager.py     # Core e-stop logic
├── pyproject.toml           # Project configuration
├── uv.lock                  # Dependency lock file
└── README.md                # This file
```

### Running Tests

```bash
# Test CLI commands (works without GPIO hardware)
uv run python -m app status
uv run python -m app estop
uv run python -m app reset
uv run python -m app config --mode no

# Test library usage
uv run python -c "from app import quick_estop_status; print(quick_estop_status())"
```

## Troubleshooting

### GPIO Warnings

If you see warnings about missing GPIO modules:
```
PinFactoryFallback: Falling back from lgpio: No module named 'lgpio'
```

This is normal when running on non-Raspberry Pi systems. The e-stop manager will run in simulation mode.

### No GPIO Hardware

The system automatically detects when GPIO hardware is unavailable and switches to simulation mode, allowing development and testing on any system.

### Permission Issues

If you get permission errors accessing GPIO:
```bash
# Add user to gpio group (Raspberry Pi OS)
sudo usermod -a -G gpio $USER
```

## License

This project is open source. Feel free to modify and use it in your projects.

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.
