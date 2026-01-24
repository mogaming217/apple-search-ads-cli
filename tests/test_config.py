"""Tests for configuration module."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from asa_cli.config import (
    CAMPAIGN_STRUCTURE,
    CAMPAIGN_TYPE_NAMES,
    AppConfig,
    CampaignType,
    Credentials,
    detect_campaign_type,
    get_campaign_name,
    load_app_config,
    load_credentials,
    save_app_config,
    save_credentials,
)


class TestCampaignNaming:
    """Tests for campaign name generation and detection."""

    def test_get_campaign_name_brand(self):
        """Test brand campaign name generation."""
        name = get_campaign_name(CampaignType.BRAND)
        assert name == "Brand"

    def test_get_campaign_name_category(self):
        """Test category campaign name generation."""
        name = get_campaign_name(CampaignType.CATEGORY)
        assert name == "Category"

    def test_get_campaign_name_competitor(self):
        """Test competitor campaign name generation."""
        name = get_campaign_name(CampaignType.COMPETITOR)
        assert name == "Competitor"

    def test_get_campaign_name_discovery(self):
        """Test discovery campaign name generation."""
        name = get_campaign_name(CampaignType.DISCOVERY)
        assert name == "Discovery"

    def test_all_campaign_types_have_names(self):
        """Test all campaign types have names defined."""
        for ctype in CampaignType:
            assert ctype in CAMPAIGN_TYPE_NAMES
            assert get_campaign_name(ctype) is not None


class TestCampaignTypeDetection:
    """Tests for campaign type detection from names."""

    def test_detect_brand_campaign(self):
        """Test detecting brand campaign."""
        assert detect_campaign_type("Brand") == CampaignType.BRAND
        assert detect_campaign_type("My Brand Campaign") == CampaignType.BRAND
        assert detect_campaign_type("BRAND_US") == CampaignType.BRAND

    def test_detect_category_campaign(self):
        """Test detecting category campaign."""
        assert detect_campaign_type("Category") == CampaignType.CATEGORY
        assert detect_campaign_type("MyApp Category") == CampaignType.CATEGORY

    def test_detect_competitor_campaign(self):
        """Test detecting competitor campaign."""
        assert detect_campaign_type("Competitor") == CampaignType.COMPETITOR
        assert detect_campaign_type("competitor-us") == CampaignType.COMPETITOR

    def test_detect_discovery_campaign(self):
        """Test detecting discovery campaign."""
        assert detect_campaign_type("Discovery") == CampaignType.DISCOVERY
        assert detect_campaign_type("My Discovery Campaign") == CampaignType.DISCOVERY

    def test_detect_case_insensitive(self):
        """Test detection is case insensitive."""
        assert detect_campaign_type("BRAND") == CampaignType.BRAND
        assert detect_campaign_type("brand") == CampaignType.BRAND
        assert detect_campaign_type("BrAnD") == CampaignType.BRAND

    def test_detect_unknown_campaign(self):
        """Test unknown campaign returns None."""
        assert detect_campaign_type("Some Random Name") is None
        assert detect_campaign_type("Test Campaign") is None


class TestCampaignStructure:
    """Tests for campaign structure configuration."""

    def test_all_campaign_types_defined(self):
        """Test that all campaign types have structure defined."""
        for ctype in CampaignType:
            assert ctype in CAMPAIGN_STRUCTURE

    def test_brand_has_exact_ad_group(self):
        """Test brand campaign has exact match ad group."""
        config = CAMPAIGN_STRUCTURE[CampaignType.BRAND]
        assert len(config.ad_groups) == 1
        assert config.ad_groups[0].name == "Brand-Exact"
        assert config.ad_groups[0].search_match_enabled is False

    def test_discovery_has_two_ad_groups(self):
        """Test discovery campaign has broad and search match ad groups."""
        config = CAMPAIGN_STRUCTURE[CampaignType.DISCOVERY]
        assert len(config.ad_groups) == 2

        # Check for broad match ad group
        broad_ag = next((ag for ag in config.ad_groups if "Broad" in ag.name), None)
        assert broad_ag is not None
        assert broad_ag.search_match_enabled is False

        # Check for search match ad group
        search_ag = next((ag for ag in config.ad_groups if "SearchMatch" in ag.name), None)
        assert search_ag is not None
        assert search_ag.search_match_enabled is True


class TestCredentials:
    """Tests for credentials management."""

    def test_credentials_model(self):
        """Test credentials model validation."""
        creds = Credentials(
            org_id=123456,
            client_id="SEARCHADS.abc123",
            team_id="SEARCHADS.team456",
            key_id="key789",
            private_key_path="/path/to/key.pem",
        )
        assert creds.org_id == 123456
        assert creds.client_id == "SEARCHADS.abc123"

    def test_save_and_load_credentials(self):
        """Test saving and loading credentials."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            creds_file = config_dir / "credentials.json"

            creds = Credentials(
                org_id=123456,
                client_id="test_client",
                team_id="test_team",
                key_id="test_key",
                private_key_path="/path/to/key.pem",
            )

            # Save
            with patch("asa_cli.config.CREDENTIALS_FILE", creds_file):
                with patch("asa_cli.config.CONFIG_DIR", config_dir):
                    save_credentials(creds)

            # Verify file was created
            assert creds_file.exists()

            # Load
            with patch("asa_cli.config.CREDENTIALS_FILE", creds_file):
                loaded = load_credentials()

            assert loaded is not None
            assert loaded.org_id == 123456
            assert loaded.client_id == "test_client"


class TestAppConfig:
    """Tests for app configuration."""

    def test_app_config_model(self):
        """Test app config model validation."""
        config = AppConfig(
            app_id=123456789,
            app_name="TestApp",
            default_countries=["US", "CA"],
            default_bid=2.00,
        )
        assert config.app_id == 123456789
        assert config.app_name == "TestApp"
        assert "US" in config.default_countries

    def test_app_config_defaults(self):
        """Test app config default values."""
        config = AppConfig(app_id=123, app_name="TestApp")
        assert config.default_countries == ["US"]
        assert config.default_bid == 1.50

    def test_save_and_load_app_config(self):
        """Test saving and loading app config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            config_file = config_dir / "config.json"

            config = AppConfig(
                app_id=123456789,
                app_name="TestApp",
                default_countries=["US"],
                default_bid=2.50,
            )

            # Save
            with patch("asa_cli.config.CONFIG_FILE", config_file):
                with patch("asa_cli.config.CONFIG_DIR", config_dir):
                    save_app_config(config)

            # Verify file was created
            assert config_file.exists()

            # Load
            with patch("asa_cli.config.CONFIG_FILE", config_file):
                loaded = load_app_config()

            assert loaded is not None
            assert loaded.app_id == 123456789
            assert loaded.app_name == "TestApp"
            assert loaded.default_bid == 2.50
