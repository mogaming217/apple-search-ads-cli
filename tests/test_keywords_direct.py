"""Tests for direct-mode keyword addition (asa keywords add --campaign --ad-group)."""

from unittest.mock import MagicMock

import pytest
import typer

from asa_cli.commands.keywords import _add_keywords_direct
from asa_cli.config import MatchType


@pytest.fixture
def mock_client_direct():
    client = MagicMock()
    client.get_campaign.return_value = {"id": 1001, "name": "Keyword"}
    client.get_ad_groups.return_value = [
        {"id": 2001, "name": "Recipe", "defaultBidAmount": {"amount": "350", "currency": "JPY"}},
        {"id": 2002, "name": "Menu"},
    ]
    client.add_keywords.return_value = (
        [
            {"id": 3001, "text": "recipe save", "matchType": "EXACT"},
            {"id": 3002, "text": "recipe stock", "matchType": "EXACT"},
        ],
        [],
    )
    return client


def test_direct_mode_dry_run_does_not_call_api(mock_client_direct):
    _add_keywords_direct(
        client=mock_client_direct,
        campaign_id=1001,
        ad_group_id=2001,
        keyword_list=["recipe save", "recipe stock"],
        match_type=MatchType.EXACT,
        bid=300,
        dry_run=True,
        force=True,
    )
    mock_client_direct.add_keywords.assert_not_called()


def test_direct_mode_happy_path_calls_add_keywords(mock_client_direct):
    _add_keywords_direct(
        client=mock_client_direct,
        campaign_id=1001,
        ad_group_id=2001,
        keyword_list=["recipe save", "recipe stock"],
        match_type=MatchType.EXACT,
        bid=300,
        dry_run=False,
        force=True,
    )
    mock_client_direct.add_keywords.assert_called_once_with(
        campaign_id=1001,
        ad_group_id=2001,
        keywords=["recipe save", "recipe stock"],
        match_type=MatchType.EXACT,
        bid_amount=300,
    )


def test_direct_mode_unknown_ad_group_raises(mock_client_direct):
    with pytest.raises(typer.Exit):
        _add_keywords_direct(
            client=mock_client_direct,
            campaign_id=1001,
            ad_group_id=9999,
            keyword_list=["recipe save"],
            match_type=MatchType.EXACT,
            bid=None,
            dry_run=False,
            force=True,
        )
    mock_client_direct.add_keywords.assert_not_called()


def test_direct_mode_unknown_campaign_raises():
    client = MagicMock()
    client.get_campaign.return_value = None
    with pytest.raises(typer.Exit):
        _add_keywords_direct(
            client=client,
            campaign_id=9999,
            ad_group_id=1,
            keyword_list=["x"],
            match_type=MatchType.EXACT,
            bid=None,
            dry_run=False,
            force=True,
        )
    client.add_keywords.assert_not_called()


def test_direct_mode_broad_match_passes_through(mock_client_direct):
    _add_keywords_direct(
        client=mock_client_direct,
        campaign_id=1001,
        ad_group_id=2001,
        keyword_list=["recipe save"],
        match_type=MatchType.BROAD,
        bid=None,
        dry_run=False,
        force=True,
    )
    args, kwargs = mock_client_direct.add_keywords.call_args
    assert kwargs["match_type"] == MatchType.BROAD
    # bid omitted -> the ad group default is resolved explicitly (the v5 API
    # layer would otherwise silently substitute AppConfig.default_bid)
    assert kwargs["bid_amount"] == 350.0


def test_direct_mode_bid_none_without_ad_group_default_raises(mock_client_direct):
    with pytest.raises(typer.Exit):
        _add_keywords_direct(
            client=mock_client_direct,
            campaign_id=1001,
            ad_group_id=2002,  # no defaultBidAmount
            keyword_list=["recipe save"],
            match_type=MatchType.EXACT,
            bid=None,
            dry_run=False,
            force=True,
        )
    mock_client_direct.add_keywords.assert_not_called()


def test_direct_mode_bid_zero_passes_through(mock_client_direct):
    _add_keywords_direct(
        client=mock_client_direct,
        campaign_id=1001,
        ad_group_id=2001,
        keyword_list=["recipe save"],
        match_type=MatchType.EXACT,
        bid=0.0,
        dry_run=False,
        force=True,
    )
    args, kwargs = mock_client_direct.add_keywords.call_args
    assert kwargs["bid_amount"] == 0.0


def test_direct_mode_non_duplicate_error_exits_1(mock_client_direct):
    mock_client_direct.add_keywords.return_value = (
        [],
        [{"messageCode": "INVALID_KEYWORD", "message": "bad keyword"}],
    )
    with pytest.raises(typer.Exit) as exc_info:
        _add_keywords_direct(
            client=mock_client_direct,
            campaign_id=1001,
            ad_group_id=2001,
            keyword_list=["recipe save"],
            match_type=MatchType.EXACT,
            bid=300,
            dry_run=False,
            force=True,
        )
    assert exc_info.value.exit_code == 1


def test_direct_mode_empty_response_exits_1(mock_client_direct):
    mock_client_direct.add_keywords.return_value = ([], [])
    with pytest.raises(typer.Exit) as exc_info:
        _add_keywords_direct(
            client=mock_client_direct,
            campaign_id=1001,
            ad_group_id=2001,
            keyword_list=["recipe save"],
            match_type=MatchType.EXACT,
            bid=300,
            dry_run=False,
            force=True,
        )
    assert exc_info.value.exit_code == 1


def test_direct_mode_all_duplicates_exits_0(mock_client_direct):
    mock_client_direct.add_keywords.return_value = (
        [],
        [{"messageCode": "DUPLICATE_KEYWORD", "message": "dup"}],
    )
    # Idempotent no-op: should not raise
    _add_keywords_direct(
        client=mock_client_direct,
        campaign_id=1001,
        ad_group_id=2001,
        keyword_list=["recipe save"],
        match_type=MatchType.EXACT,
        bid=300,
        dry_run=False,
        force=True,
    )


def test_match_without_direct_mode_fails_closed():
    from typer.testing import CliRunner

    from asa_cli.commands.keywords import app as keywords_app

    result = CliRunner().invoke(keywords_app, ["add", "recipe box", "--match", "broad", "--force"])
    assert result.exit_code == 1
    assert "--match requires both --campaign and --ad-group" in result.output
