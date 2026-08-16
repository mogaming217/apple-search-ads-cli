"""Payload contracts for fork-ported v5 features (budget orders, bid edge cases)."""

from unittest.mock import patch

import pytest

from asa_cli.config import AppConfig, Credentials, MatchType
from asa_cli.v5.api import SearchAdsClient


@pytest.fixture
def mock_client():
    credentials = Credentials(
        org_id=123456,
        client_id="test_client",
        team_id="test_team",
        key_id="test_key",
        private_key_path="/path/to/key.pem",
    )
    app_config = AppConfig(
        app_id=999999,
        app_name="TestApp",
        default_countries=["US"],
        default_bid=1.50,
    )
    with patch.object(SearchAdsClient, "_get_access_token", return_value="mock_token"):
        client = SearchAdsClient(credentials, app_config=app_config)
        client._currency = "JPY"
        return client


def test_add_keywords_bid_zero_is_not_replaced_by_default(mock_client):
    """bid_amount=0 must reach the payload as "0", not fall back to default_bid."""
    with patch.object(mock_client, "_request", return_value={"data": []}) as request:
        mock_client.add_keywords(1, 2, ["fax"], MatchType.EXACT, bid_amount=0)

    payload = request.call_args.kwargs.get("data") or request.call_args.args[-1]
    assert payload[0]["bidAmount"]["amount"] == "0"


def test_add_keywords_bid_none_falls_back_to_app_default(mock_client):
    with patch.object(mock_client, "_request", return_value={"data": []}) as request:
        mock_client.add_keywords(1, 2, ["fax"], MatchType.EXACT, bid_amount=None)

    payload = request.call_args.kwargs.get("data") or request.call_args.args[-1]
    assert payload[0]["bidAmount"]["amount"] == "1.5"


def test_create_campaign_includes_budget_orders(mock_client):
    with patch.object(mock_client, "_request", return_value={"data": {"id": 1}}) as request:
        mock_client.create_campaign(
            name="Test",
            daily_budget=500,
            countries=["US"],
            budget_order_ids=[21450441],
        )

    payload = request.call_args.kwargs.get("data") or request.call_args.args[-1]
    assert payload["budgetOrders"] == [21450441]


def test_create_campaign_omits_budget_orders_by_default(mock_client):
    with patch.object(mock_client, "_request", return_value={"data": {"id": 1}}) as request:
        mock_client.create_campaign(name="Test", daily_budget=500, countries=["US"])

    payload = request.call_args.kwargs.get("data") or request.call_args.args[-1]
    assert "budgetOrders" not in payload
