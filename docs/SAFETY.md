# E-Stop Manager Safety Documentation

## Overview

This document outlines the safety considerations and hardware requirements for the E-Stop Manager software when used in safety-critical applications.

## Safety Features Implemented

### Software Safety Features

1. **Safe State on Exit**: GPIO automatically set to safe state (e-stop active) when program exits normally
2. **Signal Handlers**: Graceful shutdown on SIGINT, SIGTERM, and SIGHUP signals
3. **Exception Handling**: Safe state set even when exceptions occur
4. **Cleanup Registration**: `atexit` handler ensures cleanup runs on normal program termination

### GPIO Output Logic

#### NC (Normally Closed) Mode - RECOMMENDED
- **Normal Operation**: GPIO outputs HIGH (3.3V)
- **E-Stop Active**: GPIO outputs LOW (0V)
- **Safe State**: LOW (e-stop active)

#### NO (Normally Open) Mode
- **Normal Operation**: GPIO outputs LOW (0V)  
- **E-Stop Active**: GPIO outputs HIGH (3.3V)
- **Safe State**: HIGH (e-stop active)

## CRITICAL HARDWARE REQUIREMENTS

### External Pull Resistors (MANDATORY)

**⚠️ WARNING**: The software alone cannot guarantee safety. External hardware is required.

When the Pi loses power, crashes, or the GPIO pin floats, external resistors ensure predictable behavior:

#### For NC Mode (Recommended):
```
Pi GPIO Pin 4 ────[10kΩ]──── GND
     │
     └─── To External E-Stop Circuit
```
- **10kΩ pull-down resistor** to ground
- When GPIO floats, pin goes LOW → E-Stop ACTIVE (safe state)

#### For NO Mode:
```
Pi GPIO Pin 4 ────[10kΩ]──── 3.3V
     │
     └─── To External E-Stop Circuit
```
- **10kΩ pull-up resistor** to 3.3V
- When GPIO floats, pin goes HIGH → E-Stop ACTIVE (safe state)

### External Circuit Design

Your external safety circuit should:

1. **Monitor the GPIO signal** from the Pi
2. **Have its own safety logic** (don't rely solely on Pi)
3. **Default to safe state** when Pi signal is lost/invalid
4. **Include hardware watchdog** if required by safety standards

## Testing Safety Features

### Test Graceful Shutdown
```bash
# Start status monitoring
uv run python -m app reset
uv run python -m app status

# Test signal handling
pkill -TERM python  # Should set safe state before exit
```

### Test Emergency Conditions
```bash
# Test Ctrl+C handling
uv run python -m app monitor
# Press Ctrl+C - should show safe state message

# Test power loss simulation
# (Disconnect Pi power while running - GPIO should go to pull resistor state)
```

## Safety Standards Compliance

### IEC 61508 / ISO 13849 Considerations

For safety-critical applications:

1. **Redundancy**: Consider dual-channel e-stop systems
2. **Diagnostics**: Monitor GPIO output with separate input pin
3. **Watchdog**: Implement external hardware watchdog
4. **Fail-Safe**: External circuit must fail to safe state
5. **Regular Testing**: Periodic verification of safety functions

### Risk Assessment

**Residual Risks**:
- Pi hardware failure could cause GPIO to output unexpected voltages
- Software bugs could prevent proper cleanup execution
- Race conditions during system shutdown

**Mitigation**:
- Use external safety-rated relays/contactors for final switching
- Implement independent hardware safety monitoring
- Regular testing and validation procedures

## Configuration Examples

### Safety-Critical Applications
```bash
# Use NC mode (safer default)
uv run python -m app config --mode nc

# Verify configuration
uv run python -m app status
```

### Development/Testing
```bash
# Can use either mode for testing
uv run python -m app config --mode no
```

## Troubleshooting

### GPIO Not Going to Safe State
1. Verify pull resistor is installed correctly
2. Check resistor value (10kΩ recommended)
3. Verify external circuit input impedance
4. Test with multimeter during Pi power-off

### Signal Handlers Not Working
1. Check system logs for signal delivery
2. Verify program has proper permissions
3. Test with `kill -TERM <pid>` command

## Legal Notice

This software is provided as-is for educational and development purposes. For safety-critical applications, proper risk assessment, hardware design, and compliance with applicable safety standards is required. The authors accept no responsibility for safety-related incidents.
