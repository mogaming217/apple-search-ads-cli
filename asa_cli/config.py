"""Configuration management for Apple Search Ads CLI."""

import json
import os
from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field
from rich.console import Console
from rich.prompt import Prompt

console = Console()

CONFIG_DIR = Path.home() / ".asa-cli"
CONFIG_FILE = CONFIG_DIR / "config.json"
CREDENTIALS_FILE = CONFIG_DIR / "credentials.json"


class CampaignType(str, Enum):
    """Campaign types following Apple's 4-campaign structure."""

    BRAND = "brand"
    CATEGORY = "category"
    COMPETITOR = "competitor"
    DISCOVERY = "discovery"


class MatchType(str, Enum):
    """Keyword match types."""

    EXACT = "EXACT"
    BROAD = "BROAD"


class AdGroupType(str, Enum):
    """Ad group types within campaigns."""

    EXACT = "exact"
    BROAD = "broad"
    SEARCH_MATCH = "search_match"


class AdGroupConfig(BaseModel):
    """Configuration for an ad group."""

    name: str
    match_type: Optional[MatchType] = None
    search_match_enabled: bool = False


class CampaignConfig(BaseModel):
    """Configuration for a campaign type."""

    name_suffix: str
    description: str
    ad_groups: list[AdGroupConfig]
    recommended_budget: float = 50.0


# Apple's recommended 4-campaign structure
CAMPAIGN_STRUCTURE: dict[CampaignType, CampaignConfig] = {
    CampaignType.BRAND: CampaignConfig(
        name_suffix="Brand",
        description="Target keywords related to your app/company name",
        ad_groups=[
            AdGroupConfig(name="Brand-Exact", match_type=MatchType.EXACT, search_match_enabled=False)
        ],
        recommended_budget=50.0,
    ),
    CampaignType.CATEGORY: CampaignConfig(
        name_suffix="Category",
        description="Non-branded keywords describing app category/functionality",
        ad_groups=[
            AdGroupConfig(
                name="Category-Exact", match_type=MatchType.EXACT, search_match_enabled=False
            )
        ],
        recommended_budget=50.0,
    ),
    CampaignType.COMPETITOR: CampaignConfig(
        name_suffix="Competitor",
        description="Target competitor app brand terms",
        ad_groups=[
            AdGroupConfig(
                name="Competitor-Exact", match_type=MatchType.EXACT, search_match_enabled=False
            )
        ],
        recommended_budget=50.0,
    ),
    CampaignType.DISCOVERY: CampaignConfig(
        name_suffix="Discovery",
        description="Keyword mining and audience expansion",
        ad_groups=[
            AdGroupConfig(
                name="Discovery-Broad", match_type=MatchType.BROAD, search_match_enabled=False
            ),
            AdGroupConfig(name="Discovery-SearchMatch", match_type=None, search_match_enabled=True),
        ],
        recommended_budget=50.0,
    ),
}

# Simple campaign names (Apple's recommended types)
# These are detected by looking for the type name in the campaign name (case-insensitive)
CAMPAIGN_TYPE_NAMES = {
    CampaignType.BRAND: "Brand",
    CampaignType.CATEGORY: "Category",
    CampaignType.COMPETITOR: "Competitor",
    CampaignType.DISCOVERY: "Discovery",
}


class Credentials(BaseModel):
    """API credentials for Apple Search Ads."""

    org_id: int = Field(..., description="Organization ID")
    client_id: str = Field(..., description="Client ID from Apple Ads API settings")
    team_id: str = Field(..., description="Team ID from Apple Ads API settings")
    key_id: str = Field(..., description="Key ID from Apple Ads API settings")
    private_key_path: str = Field(..., description="Path to private key PEM file")
    public_key_path: Optional[str] = Field(None, description="Path to public key PEM file")


class AppConfig(BaseModel):
    """Application configuration."""

    app_id: int = Field(..., description="Apple App ID (adam_id)")
    app_name: str = Field(..., description="App name for display")
    default_countries: list[str] = Field(default=["US"], description="Default target countries")
    default_bid: float = Field(default=1.50, description="Default keyword bid in USD")
    default_cpa_goal: Optional[float] = Field(None, description="Default CPA goal in USD")


def ensure_config_dir() -> None:
    """Ensure the config directory exists."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_credentials() -> Optional[Credentials]:
    """Load credentials from config file."""
    if not CREDENTIALS_FILE.exists():
        return None
    try:
        with open(CREDENTIALS_FILE) as f:
            data = json.load(f)
        return Credentials(**data)
    except (json.JSONDecodeError, ValueError) as e:
        console.print(f"[red]Error loading credentials: {e}[/red]")
        return None


def save_credentials(credentials: Credentials) -> None:
    """Save credentials to config file."""
    ensure_config_dir()
    with open(CREDENTIALS_FILE, "w") as f:
        json.dump(credentials.model_dump(), f, indent=2)
    os.chmod(CREDENTIALS_FILE, 0o600)  # Restrict permissions
    console.print(f"[green]Credentials saved to {CREDENTIALS_FILE}[/green]")


def load_app_config() -> Optional[AppConfig]:
    """Load app configuration from config file."""
    if not CONFIG_FILE.exists():
        return None
    try:
        with open(CONFIG_FILE) as f:
            data = json.load(f)
        return AppConfig(**data)
    except (json.JSONDecodeError, ValueError) as e:
        console.print(f"[red]Error loading config: {e}[/red]")
        return None


def save_app_config(config: AppConfig) -> None:
    """Save app configuration to config file."""
    ensure_config_dir()
    with open(CONFIG_FILE, "w") as f:
        json.dump(config.model_dump(), f, indent=2)
    console.print(f"[green]Config saved to {CONFIG_FILE}[/green]")


def get_campaign_name(campaign_type: CampaignType) -> str:
    """Get the simple campaign name for a type.

    Returns simple names like "Brand", "Category", "Competitor", "Discovery".
    """
    return CAMPAIGN_TYPE_NAMES[campaign_type]


def detect_campaign_type(name: str) -> Optional[CampaignType]:
    """Detect campaign type from a campaign name (case-insensitive).

    Looks for type keywords in the campaign name:
    - "brand" -> CampaignType.BRAND
    - "category" -> CampaignType.CATEGORY
    - "competitor" -> CampaignType.COMPETITOR
    - "discovery" -> CampaignType.DISCOVERY

    Returns the CampaignType or None if not detected.
    """
    name_lower = name.lower()
    for ctype, type_name in CAMPAIGN_TYPE_NAMES.items():
        if type_name.lower() in name_lower:
            return ctype
    return None


def parse_campaign_name(name: str, prefix: Optional[str] = None) -> Optional[tuple[str, CampaignType, list[str]]]:
    """Parse a campaign name to detect its type.

    This function provides backward compatibility. It now uses simple name detection.
    Returns (app_name, campaign_type, countries) or None if type not detected.

    The app_name and countries are placeholder values since we no longer encode them in the name.
    """
    ctype = detect_campaign_type(name)
    if ctype:
        # Return placeholder values for backward compatibility
        app_config = load_app_config()
        app_name = app_config.app_name if app_config else "App"
        countries = app_config.default_countries if app_config else ["US"]
        return (app_name, ctype, countries)
    return None


def prompt_for_credentials() -> Credentials:
    """Interactively prompt for API credentials."""
    console.print("\n[bold]Apple Search Ads API Credentials Setup[/bold]\n")
    console.print("You'll need to create API credentials in Apple Ads dashboard first.")
    console.print("See: https://ads.apple.com/help/campaigns/0022-use-the-campaign-management-api\n")

    org_id = int(Prompt.ask("Organization ID"))
    client_id = Prompt.ask("Client ID")
    team_id = Prompt.ask("Team ID")
    key_id = Prompt.ask("Key ID")
    private_key_path = Prompt.ask("Path to private key PEM file")

    # Expand user path
    private_key_path = os.path.expanduser(private_key_path)

    if not os.path.exists(private_key_path):
        console.print(f"[yellow]Warning: Private key file not found at {private_key_path}[/yellow]")

    return Credentials(
        org_id=org_id,
        client_id=client_id,
        team_id=team_id,
        key_id=key_id,
        private_key_path=private_key_path,
    )


def prompt_for_app_config() -> AppConfig:
    """Interactively prompt for app configuration."""
    console.print("\n[bold]App Configuration Setup[/bold]\n")

    app_id = int(Prompt.ask("Apple App ID (adam_id)", default="0"))
    app_name = Prompt.ask("App name (for display)")
    countries = Prompt.ask("Default target countries (comma-separated)", default="US")
    default_bid = float(Prompt.ask("Default keyword bid (USD)", default="1.50"))

    return AppConfig(
        app_id=app_id,
        app_name=app_name,
        default_countries=[c.strip().upper() for c in countries.split(",")],
        default_bid=default_bid,
    )

