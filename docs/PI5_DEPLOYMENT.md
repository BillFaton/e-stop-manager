# Raspberry Pi 5 Deployment Guide

This guide will help you deploy the e-stop manager on your Raspberry Pi 5 for optimal performance.

## Pre-requisites

- Raspberry Pi 5 with Raspberry Pi OS
- SSH access or direct terminal access
- E-stop switch (normally closed recommended)

## Step 1: System Setup

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install required system dependencies for lgpio
sudo apt install -y swig python3-dev git

# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env
```

## Step 2: Clone and Install

```bash
# Clone the repository
git clone https://github.com/BillFaton/e-stop-manager.git
cd e-stop-manager

# Install dependencies with Pi 5 optimization
uv add gpiozero click lgpio
```

## Step 3: Hardware Wiring

### Recommended: Normally Closed (NC) Configuration

```
Pi 5 GPIO 4 (Pin 7) ----[E-Stop Switch]---- GND (Pin 6)
                   |
                 Pull-up resistor (internal)
```

**Physical Pin Layout:**
- GPIO 4 → Physical Pin 7
- GND → Physical Pin 6 (or any other GND pin)

### Wiring Steps:
1. **Power off** your Pi 5 completely
2. Connect one terminal of the e-stop switch to GPIO 4 (Pin 7)
3. Connect the other terminal to GND (Pin 6)
4. Power on your Pi 5

## Step 4: Test Installation

```bash
# Test the CLI (should show Pi 5 optimization)
uv run python -m app status

# Expected output should include:
# Platform: Raspberry Pi 5
# ✓ Pi 5 Optimized (lgpio backend active)
```

## Step 5: Basic Operation

```bash
# Check current status
uv run python -m app status

# Manually activate e-stop
uv run python -m app estop

# Reset e-stop
uv run python -m app reset

# Monitor in real-time
uv run python -m app monitor
```

## Step 6: Test Physical E-Stop

1. **Initial State**: With switch closed (normal state)
   ```bash
   uv run python -m app status
   # Should show: State: INACTIVE
   ```

2. **Activate E-Stop**: Press/open the e-stop switch
   ```bash
   uv run python -m app status
   # Should show: State: ACTIVE
   ```

3. **Reset**: Close the switch and run reset
   ```bash
   uv run python -m app reset
   # Should show: ✓ E-stop reset
   ```

## Step 7: Create System Service (Optional)

For production use, create a systemd service:

```bash
# Create service file
sudo nano /etc/systemd/system/estop-manager.service
```

Add the following content:

```ini
[Unit]
Description=E-Stop Manager
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/e-stop-manager
ExecStart=/home/pi/e-stop-manager/.venv/bin/python -m app monitor
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
# Enable and start the service
sudo systemctl enable estop-manager.service
sudo systemctl start estop-manager.service

# Check status
sudo systemctl status estop-manager.service
```

## Troubleshooting

### Permission Issues
```bash
# Add user to gpio group
sudo usermod -a -G gpio $USER
# Logout and login again for changes to take effect
```

### lgpio Not Working
```bash
# Reinstall with system dependencies
sudo apt install -y swig python3-dev
uv remove lgpio
uv add lgpio
```

### GPIO Pin Not Responding
```bash
# Test GPIO pin directly
uv run python -c "
from gpiozero import DigitalInputDevice
pin = DigitalInputDevice(4, pull_up=True)
print(f'GPIO 4 state: {pin.is_active}')
"
```

## Performance Verification

Verify Pi 5 optimization is active:

```bash
uv run python -m app status

# Look for these indicators:
# Platform: Raspberry Pi 5
# GPIO Backend: LGPIOFactory
# ✓ Pi 5 Optimized (lgpio backend active)
```

## Safety Notes

- **Always test** the e-stop functionality before deploying in a critical system
- **Use NC (Normally Closed)** wiring for maximum safety
- **Test regularly** to ensure the e-stop responds correctly
- **Have a backup** safety system for critical applications

## Integration Example

```python
# Example: Integrate with a robot controller
from app import EStopManager, EStopState
import time

estop = EStopManager(gpio_pin=4)

def robot_control_loop():
    while True:
        if estop.get_estop_state() == EStopState.ACTIVE:
            print("E-STOP ACTIVE - STOPPING ALL MOTORS")
            # Stop all robot movement
            break
        else:
            # Normal operation
            print("Robot running normally...")
        
        time.sleep(0.1)  # Fast response time

try:
    robot_control_loop()
finally:
    estop.cleanup()
```

Your Pi 5 e-stop manager is now ready for deployment! 🚀
