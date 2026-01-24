"""Configuration commands."""

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ..config import (
    CONFIG_FILE,
    CREDENTIALS_FILE,
    load_app_config,
    load_credentials,
    prompt_for_app_config,
    prompt_for_credentials,
    save_app_config,
    save_credentials,
)

app = typer.Typer(help="Configuration management commands")
console = Console()


@app.command("setup")
def setup_config(
    credentials_only: bool = typer.Option(False, "--credentials", "-c", help="Only configure credentials"),
    app_only: bool = typer.Option(False, "--app", "-a", help="Only configure app settings"),
):
    """Set up API credentials and app configuration."""
    if not app_only:
        console.print(Panel("[bold]Step 1: API Credentials[/bold]", expand=False))

        existing_creds = load_credentials()
        if existing_creds:
            console.print("[yellow]Existing credentials found.[/yellow]")
            console.print(f"  Org ID: {existing_creds.org_id}")
            console.print(f"  Client ID: {existing_creds.client_id[:20]}...")

            from rich.prompt import Confirm

            if not Confirm.ask("Overwrite existing credentials?"):
                if credentials_only:
                    return
            else:
                credentials = prompt_for_credentials()
                save_credentials(credentials)
        else:
            credentials = prompt_for_credentials()
            save_credentials(credentials)

    if credentials_only:
        console.print("\n[green]Credentials configured![/green]")
        return

    if not credentials_only:
        console.print(Panel("\n[bold]Step 2: App Configuration[/bold]", expand=False))

        existing_config = load_app_config()
        if existing_config:
            console.print("[yellow]Existing app config found.[/yellow]")
            console.print(f"  App Name: {existing_config.app_name}")
            console.print(f"  App ID: {existing_config.app_id}")
            console.print(f"  Countries: {', '.join(existing_config.default_countries)}")

            from rich.prompt import Confirm

            if not Confirm.ask("Overwrite existing config?"):
                if app_only:
                    return
            else:
                config = prompt_for_app_config()
                save_app_config(config)
        else:
            config = prompt_for_app_config()
            save_app_config(config)

    console.print("\n[bold green]Configuration complete![/bold green]")
    console.print("\nNext steps:")
    console.print("  1. Run [cyan]asa campaigns audit[/cyan] to check existing campaigns")
    console.print("  2. Run [cyan]asa campaigns setup[/cyan] to create the 4-campaign structure")


@app.command("show")
def show_config():
    """Display current configuration."""
    credentials = load_credentials()
    app_config = load_app_config()

    console.print(Panel("[bold]Current Configuration[/bold]", expand=False))

    # Credentials
    console.print("\n[bold]API Credentials:[/bold]")
    if credentials:
        table = Table(show_header=False, box=None)
        table.add_column("Key", style="cyan")
        table.add_column("Value")

        table.add_row("Org ID", str(credentials.org_id))
        table.add_row("Client ID", credentials.client_id[:30] + "...")
        table.add_row("Team ID", credentials.team_id)
        table.add_row("Key ID", credentials.key_id)
        table.add_row("Private Key", credentials.private_key_path)
        table.add_row("Config File", str(CREDENTIALS_FILE))

        console.print(table)
    else:
        console.print("[yellow]  Not configured. Run 'asa config setup'.[/yellow]")

    # App config
    console.print("\n[bold]App Configuration:[/bold]")
    if app_config:
        table = Table(show_header=False, box=None)
        table.add_column("Key", style="cyan")
        table.add_column("Value")

        table.add_row("App Name", app_config.app_name)
        table.add_row("App ID", str(app_config.app_id))
        table.add_row("Countries", ", ".join(app_config.default_countries))
        table.add_row("Default Bid", f"${app_config.default_bid}")
        table.add_row("CPA Goal", f"${app_config.default_cpa_goal}" if app_config.default_cpa_goal else "Not set")
        table.add_row("Config File", str(CONFIG_FILE))

        console.print(table)
    else:
        console.print("[yellow]  Not configured. Run 'asa config setup'.[/yellow]")


@app.command("test")
def test_connection():
    """Test API connection with current credentials."""
    credentials = load_credentials()
    if not credentials:
        console.print("[red]No credentials configured. Run 'asa config setup' first.[/red]")
        raise typer.Exit(1)

    console.print("[bold]Testing API connection...[/bold]\n")

    try:
        from ..api import SearchAdsClient

        client = SearchAdsClient(credentials)

        with console.status("[bold blue]Connecting to Apple Search Ads API..."):
            campaigns = client.get_campaigns(limit=1)

        console.print("[green]✓ Connection successful![/green]")
        console.print(f"  Organization ID: {credentials.org_id}")

        # Get campaign count
        with console.status("[bold blue]Fetching campaign count..."):
            all_campaigns = client.get_campaigns()

        console.print(f"  Total campaigns: {len(all_campaigns)}")

    except ImportError as e:
        console.print(f"[red]✗ Missing dependency: {e}[/red]")
        console.print("  Run: pip install -e . (from the apple-search-ads directory)")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]✗ Connection failed: {e}[/red]")
        console.print("\nTroubleshooting:")
        console.print("  1. Verify your credentials in Apple Ads dashboard")
        console.print("  2. Ensure private key file exists and is readable")
        console.print("  3. Check that your API user has appropriate permissions")
        raise typer.Exit(1)

