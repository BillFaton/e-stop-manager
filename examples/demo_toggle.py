#!/usr/bin/env python3
"""
E-Stop Toggle Demo - Activates and deactivates e-stop every 1 second

This script demonstrates the EStopManager library by alternating between
e-stop active and inactive states every second. Perfect for testing GPIO
output behavior and verifying hardware connections.

Usage:
    python demo_toggle.py [--gpio-pin PIN] [--mode nc|no]

Press Ctrl+C to stop gracefully.
"""

import time
import signal
import sys
import argparse
from datetime import datetime
from app.e_stop_manager import EStopManager, EStopMode, EStopState

# Global manager for cleanup
manager = None


def signal_handler(signum, frame):
    """Handle termination signals gracefully"""
    global manager
    signal_name = signal.Signals(signum).name
    print(f"\n⚠️ Received {signal_name} - stopping toggle demo...")
    
    if manager:
        print("🛡️ Setting e-stop to safe state and cleaning up...")
        try:
            manager.cleanup()
            print("✅ Cleanup completed successfully")
        except Exception as e:
            print(f"❌ Error during cleanup: {e}")
    
    print("👋 Demo stopped")
    sys.exit(0)


def display_status(manager: EStopManager, cycle_count: int):
    """Display current status with formatting"""
    status = manager.get_status()
    current_time = datetime.now().strftime("%H:%M:%S.%f")[:-3]  # Include milliseconds
    
    # Color codes for terminal output
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    RESET = '\033[0m'
    
    # State colors
    if status['estop_state'] == 'active':
        state_color = RED
        gpio_color = RED if not status['gpio_active'] else GREEN  # LOW=red, HIGH=green
    else:
        state_color = GREEN
        gpio_color = GREEN if status['gpio_active'] else RED
    
    # GPIO output display
    gpio_level = "HIGH" if status['gpio_active'] else "LOW"
    
    print(f"[{BLUE}{current_time}{RESET}] "
          f"Cycle: {BOLD}{cycle_count:3d}{RESET} | "
          f"State: {state_color}{BOLD}{status['estop_state'].upper():8s}{RESET} | "
          f"GPIO: {gpio_color}{BOLD}{gpio_level:4s}{RESET} | "
          f"Mode: {YELLOW}{status['mode'].upper()}{RESET}")


def main():
    """Main demo function"""
    global manager
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='E-Stop Toggle Demo')
    parser.add_argument('--gpio-pin', type=int, default=4, 
                       help='GPIO pin number (default: 4)')
    parser.add_argument('--mode', choices=['nc', 'no'], default='nc',
                       help='E-stop mode: nc (normally closed) or no (normally open)')
    parser.add_argument('--interval', type=float, default=1.0,
                       help='Toggle interval in seconds (default: 1.0)')
    args = parser.parse_args()
    
    # Convert mode to enum
    estop_mode = EStopMode.NC if args.mode == 'nc' else EStopMode.NO
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Termination
    
    try:
        # Initialize E-Stop Manager
        print("🚀 Starting E-Stop Toggle Demo")
        print("=" * 50)
        print(f"📌 GPIO Pin: {args.gpio_pin}")
        print(f"⚙️ Mode: {args.mode.upper()} ({'Normally Closed' if args.mode == 'nc' else 'Normally Open'})")
        print(f"⏱️ Interval: {args.interval}s")
        print("🔄 Press Ctrl+C to stop")
        print("=" * 50)
        
        manager = EStopManager(gpio_pin=args.gpio_pin, mode=estop_mode)
        
        # Show initial status
        status = manager.get_status()
        print(f"✅ Initialized successfully")
        print(f"🔧 GPIO Backend: {status['gpio_backend']}")
        if status.get('pi5_optimized'):
            print(f"⚡ Pi 5 Optimized (lgpio backend)")
        print()
        
        # Reset to known state
        print("🔄 Resetting to inactive state...")
        manager.reset_estop()
        time.sleep(0.1)  # Brief pause for state to settle
        
        # Main toggle loop
        cycle_count = 0
        is_active = False
        
        print("🎯 Starting toggle sequence:")
        print()
        
        while True:
            cycle_count += 1
            
            if is_active:
                # Deactivate e-stop
                if manager.reset_estop():
                    is_active = False
                else:
                    print("❌ Failed to reset e-stop!")
            else:
                # Activate e-stop
                if manager.activate_estop():
                    is_active = True
                else:
                    print("❌ Failed to activate e-stop!")
            
            # Display current status
            display_status(manager, cycle_count)
            
            # Wait for next cycle
            time.sleep(args.interval)
            
    except KeyboardInterrupt:
        # This should be handled by signal_handler, but just in case
        print("\n🛑 Interrupted by user")
        signal_handler(signal.SIGINT, None)
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        if manager:
            print("🛡️ Attempting emergency cleanup...")
            try:
                manager.cleanup()
                print("✅ Emergency cleanup completed")
            except Exception as cleanup_error:
                print(f"❌ Emergency cleanup failed: {cleanup_error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
