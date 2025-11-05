"""
E-Stop Manager CLI - Command line interface for emergency stop management
"""
import click
import logging
import sys
import traceback
import signal
import atexit
from datetime import datetime

# Configure logging early with more visible output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Log CLI startup
logger.info("=== E-Stop Manager CLI Starting ===")

# Import with error handling
try:
    logger.info("Importing EStopManager components...")
    from src.e_stop_manager import EStopManager, EStopMode, EStopState
    logger.info("✓ Successfully imported EStopManager components")
except ImportError as e:
    logger.error(f"✗ Failed to import EStopManager: {e}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    click.echo(click.style(f"Import Error: {e}", fg='red'), err=True)
    sys.exit(1)
except Exception as e:
    logger.error(f"✗ Unexpected error during import: {e}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    click.echo(click.style(f"Unexpected Import Error: {e}", fg='red'), err=True)
    sys.exit(1)

# Global manager instance
_manager = None


def _emergency_cleanup():
    """Emergency cleanup function for signals and atexit"""
    global _manager
    if _manager:
        logger.warning("⚠ Emergency cleanup triggered - setting GPIO to safe state")
        try:
            _manager.cleanup()
        except Exception as e:
            logger.error(f"Error during emergency cleanup: {e}")


def _signal_handler(signum, frame):
    """Handle termination signals gracefully"""
    signal_name = signal.Signals(signum).name
    logger.warning(f"⚠ Received signal {signal_name} ({signum}) - initiating graceful shutdown")
    _emergency_cleanup()
    click.echo(f"\nReceived {signal_name} - E-Stop set to safe state")
    sys.exit(0)


# Register signal handlers for graceful shutdown
logger.info("Registering signal handlers for graceful shutdown...")
signal.signal(signal.SIGINT, _signal_handler)   # Ctrl+C
signal.signal(signal.SIGTERM, _signal_handler)  # Termination signal
if hasattr(signal, 'SIGHUP'):
    signal.signal(signal.SIGHUP, _signal_handler)  # Hangup signal (Unix only)

# Register cleanup function to run at exit
atexit.register(_emergency_cleanup)
logger.info("✓ Signal handlers and cleanup registered")


def get_manager(gpio_pin: int = 4) -> EStopManager:
    """Get or create EStopManager instance"""
    global _manager
    logger.info(f"get_manager called with gpio_pin={gpio_pin}")
    if _manager is None:
        logger.info("Creating new EStopManager instance...")
        try:
            _manager = EStopManager(gpio_pin=gpio_pin)
            logger.info("✓ EStopManager instance created successfully")
        except Exception as e:
            logger.error(f"✗ Failed to create EStopManager: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    else:
        logger.info("Using existing EStopManager instance")
    return _manager


@click.group()
@click.option('--gpio-pin', default=4, help='GPIO pin number (default: 4)')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--debug', is_flag=True, help='Enable debug logging')
@click.pass_context
def cli(ctx, gpio_pin, verbose, debug):
    """E-Stop Manager - Emergency stop control via GPIO"""
    logger.info(f"CLI called with gpio_pin={gpio_pin}, verbose={verbose}, debug={debug}")
    
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.getLogger('app.e_stop_manager').setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    elif verbose:
        logging.getLogger().setLevel(logging.INFO)
        logging.getLogger('app.e_stop_manager').setLevel(logging.INFO)
        logger.info("Verbose logging enabled")
    
    # Store parameters in context for subcommands
    ctx.ensure_object(dict)
    ctx.obj['gpio_pin'] = gpio_pin
    ctx.obj['verbose'] = verbose
    ctx.obj['debug'] = debug
    
    logger.info(f"Context initialized: {ctx.obj}")


@cli.command()
@click.pass_context
def estop(ctx):
    """Activate the emergency stop"""
    logger.info("=== ESTOP COMMAND STARTED ===")
    try:
        logger.info(f"Getting manager with GPIO pin {ctx.obj['gpio_pin']}")
        manager = get_manager(ctx.obj['gpio_pin'])
        
        logger.info("Attempting to activate e-stop...")
        if manager.activate_estop():
            logger.info("✓ E-stop activation successful")
            click.echo(click.style("✓ E-stop activated", fg='red', bold=True))
            status = manager.get_status()
            click.echo(f"Status: {status['estop_state']}")
        else:
            logger.error("✗ E-stop activation failed")
            click.echo(click.style("✗ Failed to activate e-stop", fg='red'), err=True)
            sys.exit(1)
    except Exception as e:
        logger.error(f"✗ Exception in estop command: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        click.echo(click.style(f"Error: {e}", fg='red'), err=True)
        sys.exit(1)
    finally:
        logger.info("=== ESTOP COMMAND FINISHED ===")


@cli.command()
@click.pass_context
def reset(ctx):
    """Reset/clear the emergency stop state"""
    logger.info("=== RESET COMMAND STARTED ===")
    try:
        logger.info(f"Getting manager with GPIO pin {ctx.obj['gpio_pin']}")
        manager = get_manager(ctx.obj['gpio_pin'])
        
        logger.info("Attempting to reset e-stop...")
        if manager.reset_estop():
            logger.info("✓ E-stop reset successful")
            click.echo(click.style("✓ E-stop reset", fg='green', bold=True))
            status = manager.get_status()
            click.echo(f"Status: {status['estop_state']}")
        else:
            logger.error("✗ E-stop reset failed")
            click.echo(click.style("✗ Failed to reset e-stop", fg='red'), err=True)
            sys.exit(1)
    except Exception as e:
        logger.error(f"✗ Exception in reset command: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        click.echo(click.style(f"Error: {e}", fg='red'), err=True)
        sys.exit(1)
    finally:
        logger.info("=== RESET COMMAND FINISHED ===")


@cli.command()
@click.pass_context
def status(ctx):
    """Show current e-stop status"""
    logger.info("=== STATUS COMMAND STARTED ===")
    try:
        logger.info(f"Getting manager with GPIO pin {ctx.obj['gpio_pin']}")
        manager = get_manager(ctx.obj['gpio_pin'])
        
        logger.info("Getting status information...")
        status = manager.get_status()
        logger.info(f"Status retrieved: {status}")
        
        # Format status display
        state_color = 'red' if status['estop_state'] == 'active' else 'green'
        
        click.echo("E-Stop Manager Status (Software E-Stop)")
        click.echo("=" * 40)
        click.echo(f"E-Stop State: {click.style(status['estop_state'].upper(), fg=state_color, bold=True)}")
        click.echo(f"GPIO Pin: {status['gpio_pin']} (OUTPUT)")
        click.echo(f"GPIO Output: {click.style('HIGH' if status['gpio_active'] else 'LOW', fg='green' if status['gpio_active'] else 'red', bold=True)}")
        click.echo(f"Mode: {status['mode'].upper()} ({'Normally Closed' if status['mode'] == 'nc' else 'Normally Open'})")
        click.echo(f"Manual Override: {status['manual_override']}")
        click.echo(f"GPIO Available: {status['gpio_available']}")
        click.echo()
        click.echo("Output Logic")
        click.echo("-" * 12)
        if status['mode'] == 'nc':
            click.echo("• NC Mode: HIGH when inactive, LOW when e-stop active")
        else:
            click.echo("• NO Mode: LOW when inactive, HIGH when e-stop active")
        click.echo()
        click.echo("System Information")
        click.echo("-" * 18)
        click.echo(f"Platform: {status['pi_model']}")
        click.echo(f"GPIO Backend: {status['gpio_backend']}")
        
        if status.get('pi5_optimized'):
            click.echo(click.style("✓ Pi 5 Optimized (lgpio backend active)", fg='green'))
        elif 'Raspberry Pi 5' in status['pi_model']:
            click.echo(click.style("⚠ Pi 5 detected but not optimized (install lgpio)", fg='yellow'))
        
        if not status['gpio_available']:
            click.echo(click.style("⚠ Warning: GPIO not available (simulation mode)", fg='yellow'))
            
        logger.info("✓ Status display completed successfully")
    except Exception as e:
        logger.error(f"✗ Exception in status command: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        click.echo(click.style(f"Error: {e}", fg='red'), err=True)
        sys.exit(1)
    finally:
        logger.info("=== STATUS COMMAND FINISHED ===")


@cli.command()
@click.option('--mode', type=click.Choice(['nc', 'no'], case_sensitive=False), 
              help='Set e-stop mode: nc (normally closed) or no (normally open)')
@click.pass_context
def config(ctx, mode):
    """Configure e-stop settings"""
    manager = get_manager(ctx.obj['gpio_pin'])
    
    if mode:
        estop_mode = EStopMode.NC if mode.lower() == 'nc' else EStopMode.NO
        if manager.set_mode(estop_mode):
            click.echo(click.style(f"✓ Mode set to {mode.upper()}", fg='green'))
            mode_desc = "Normally Closed (safer)" if mode.lower() == 'nc' else "Normally Open"
            click.echo(f"Description: {mode_desc}")
        else:
            click.echo(click.style("✗ Failed to set mode", fg='red'), err=True)
            sys.exit(1)
    else:
        # Show current configuration
        status = manager.get_status()
        click.echo("Current Configuration")
        click.echo("=" * 20)
        click.echo(f"Mode: {status['mode'].upper()}")
        click.echo(f"GPIO Pin: {status['gpio_pin']}")
        click.echo(f"Manual Override: {status['manual_override']}")


@cli.command()
@click.pass_context
def monitor(ctx):
    """Monitor e-stop state in real-time (Ctrl+C to stop)"""
    manager = get_manager(ctx.obj['gpio_pin'])
    
    click.echo("Monitoring e-stop state (Press Ctrl+C to stop)")
    click.echo("=" * 45)
    
    last_state = None
    try:
        while True:
            current_state = manager.get_estop_state()
            if current_state != last_state:
                timestamp = datetime.now().strftime("%H:%M:%S")
                state_color = 'red' if current_state == EStopState.ACTIVE else 'green'
                click.echo(f"[{timestamp}] State: {click.style(current_state.value.upper(), fg=state_color, bold=True)}")
                last_state = current_state
            
            # Small delay to avoid excessive CPU usage
            import time
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        click.echo("\nMonitoring stopped")
    finally:
        manager.cleanup()


if __name__ == '__main__':
    try:
        cli()
    except KeyboardInterrupt:
        if _manager:
            _manager.cleanup()
        click.echo("\nOperation cancelled")
        sys.exit(1)
    except Exception as e:
        if _manager:
            _manager.cleanup()
        click.echo(click.style(f"Error: {e}", fg='red'), err=True)
        sys.exit(1)
