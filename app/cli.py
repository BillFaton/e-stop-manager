"""
E-Stop Manager CLI - Command line interface for emergency stop management
"""
import click
import logging
import sys
from datetime import datetime
from .estop_manager import EStopManager, EStopMode, EStopState

# Configure logging
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Global manager instance
_manager = None


def get_manager(gpio_pin: int = 4) -> EStopManager:
    """Get or create EStopManager instance"""
    global _manager
    if _manager is None:
        _manager = EStopManager(gpio_pin=gpio_pin)
    return _manager


@click.group()
@click.option('--gpio-pin', default=4, help='GPIO pin number (default: 4)')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.pass_context
def cli(ctx, gpio_pin, verbose):
    """E-Stop Manager - Emergency stop control via GPIO"""
    if verbose:
        logging.getLogger().setLevel(logging.INFO)
        logging.getLogger('app.estop_manager').setLevel(logging.INFO)
    
    # Store gpio_pin in context for subcommands
    ctx.ensure_object(dict)
    ctx.obj['gpio_pin'] = gpio_pin


@cli.command()
@click.pass_context
def estop(ctx):
    """Activate the emergency stop"""
    manager = get_manager(ctx.obj['gpio_pin'])
    
    if manager.activate_estop():
        click.echo(click.style("✓ E-stop activated", fg='red', bold=True))
        status = manager.get_status()
        click.echo(f"Status: {status['estop_state']}")
    else:
        click.echo(click.style("✗ Failed to activate e-stop", fg='red'), err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def reset(ctx):
    """Reset/clear the emergency stop state"""
    manager = get_manager(ctx.obj['gpio_pin'])
    
    if manager.reset_estop():
        click.echo(click.style("✓ E-stop reset", fg='green', bold=True))
        status = manager.get_status()
        click.echo(f"Status: {status['estop_state']}")
    else:
        click.echo(click.style("✗ Failed to reset e-stop", fg='red'), err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def status(ctx):
    """Show current e-stop status"""
    manager = get_manager(ctx.obj['gpio_pin'])
    status = manager.get_status()
    
    # Format status display
    state_color = 'red' if status['estop_state'] == 'active' else 'green'
    
    click.echo("E-Stop Manager Status")
    click.echo("=" * 20)
    click.echo(f"State: {click.style(status['estop_state'].upper(), fg=state_color, bold=True)}")
    click.echo(f"GPIO Pin: {status['gpio_pin']}")
    click.echo(f"GPIO Active: {status['gpio_active']}")
    click.echo(f"Mode: {status['mode'].upper()} ({'Normally Closed' if status['mode'] == 'nc' else 'Normally Open'})")
    click.echo(f"Manual Override: {status['manual_override']}")
    click.echo(f"GPIO Available: {status['gpio_available']}")
    
    if not status['gpio_available']:
        click.echo(click.style("⚠ Warning: GPIO not available (simulation mode)", fg='yellow'))


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
