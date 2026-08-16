"""Keyword research workflows built on Platform API v1 insights and suggestions.

Wraps ``search_term_popularity_query`` and ``query_keyword_suggestions`` so that
routine keyword research does not require hand-written JSON request files.
Computes the latest complete weekly window (generated Mondays 07:00 UTC for the
preceding Sunday–Saturday week) and the latest finalized month (published on the
5th) automatically.
"""

from __future__ import annotations

import calendar
import json
import re
from datetime import UTC, datetime, timedelta
from typing import Any, Optional

import typer
from rich.console import Console

from ..config import get_current_app_config
from ..platform.runtime import PlatformAPIError, hydrate_model, invoke

app = typer.Typer(help="Keyword research: search-term popularity and keyword suggestions.")
console = Console()

_POP_PAGE_SIZE = 5000
_POP_MAX_ROWS = 40_000
_SUGG_PAGE_SIZE = 100
_SUGG_MAX_ROWS = 1000


def latest_complete_week(now: datetime) -> tuple[str, str]:
    """Return the latest Sunday–Saturday week whose Monday 07:00 UTC publish has passed."""
    now = now.astimezone(UTC)
    day = now.date()
    while True:
        if day.weekday() == 0:  # Monday
            published = datetime(day.year, day.month, day.day, 7, tzinfo=UTC)
            if now >= published:
                end = day - timedelta(days=2)  # preceding Saturday
                return (end - timedelta(days=6)).isoformat(), end.isoformat()
        day -= timedelta(days=1)


def latest_complete_month(now: datetime) -> tuple[str, str]:
    """Return the latest finalized month (monthly data publishes on the 5th)."""
    today = now.astimezone(UTC).date()
    year, month = today.year, today.month
    steps = 1 if today.day >= 5 else 2
    for _ in range(steps):
        month -= 1
        if month == 0:
            year, month = year - 1, 12
    last_day = calendar.monthrange(year, month)[1]
    return f"{year:04d}-{month:02d}-01", f"{year:04d}-{month:02d}-{last_day:02d}"


def _fail(exc: PlatformAPIError) -> None:
    console.print(f"[red]{exc}[/red]")
    raise typer.Exit(1)


def fetch_popularity(
    *,
    country: str,
    genre: str | None,
    start: str,
    end: str,
    granularity: str,
    ad_account_id: str | None,
) -> list[dict[str, Any]]:
    """Fetch popularity rows with explicit pagination."""
    filters: list[dict[str, Any]] = [
        {"field": "countryOrRegion", "operator": "EQUALS", "value": country}
    ]
    if genre:
        filters.append({"field": "genre", "operator": "EQUALS", "value": genre})
    rows: list[dict[str, Any]] = []
    offset = 0
    while offset < _POP_MAX_ROWS:
        request = hydrate_model(
            "SearchTermPopularityQueryRequest",
            {
                "timeRange": {"start": start, "end": end, "granularity": granularity},
                "filters": filters,
                "pagination": {"offset": offset, "pageSize": _POP_PAGE_SIZE},
            },
        )
        response = invoke(
            "search_term_popularity_query",
            arguments={"search_term_popularity_query_request": request},
            ad_account_id=ad_account_id,
        )
        page = ((response or {}).get("result") or {}).get("rows") or []
        rows.extend(page)
        offset += len(page)
        if len(page) < _POP_PAGE_SIZE:
            break
    return rows


@app.command("pop")
def popularity(
    country: str = typer.Option(..., "--country", help="Storefront country code (US/GB/JP/...)"),
    genre: Optional[str] = typer.Option(
        None, "--genre", help="Genre enum such as FOOD_DRINK (see `genres` command)"
    ),
    grep: Optional[str] = typer.Option(
        None, "--grep", help="Case-insensitive regex filter on the search term"
    ),
    weeks: int = typer.Option(1, "--weeks", min=1, help="Number of latest complete weeks"),
    monthly: bool = typer.Option(False, "--monthly", help="Use monthly data instead of weekly"),
    start: Optional[str] = typer.Option(None, "--start", help="Start date YYYY-MM-DD (auto if omitted)"),
    end: Optional[str] = typer.Option(None, "--end", help="End date YYYY-MM-DD (auto if omitted)"),
    limit: int = typer.Option(50, "--limit", min=1, help="Maximum rows to display"),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON"),
    ad_account: Optional[str] = typer.Option(
        None, "--ad-account", envvar="ASA_AD_ACCOUNT_ID", help="Apple Ads Platform ad account ID"
    ),
) -> None:
    """Search-term popularity ranking (top 500 per genre per storefront)."""
    now = datetime.now(UTC)
    if monthly:
        granularity = "MONTHLY"
        window = (start, end) if start and end else latest_complete_month(now)
    else:
        granularity = "WEEKLY_SUN_SAT"
        if start and end:
            window = (start, end)
        else:
            first, last = latest_complete_week(now)
            if weeks > 1:
                first = (
                    datetime.fromisoformat(first) - timedelta(days=7 * (weeks - 1))
                ).date().isoformat()
            window = (first, last)
    try:
        rows = fetch_popularity(
            country=country,
            genre=genre,
            start=window[0],
            end=window[1],
            granularity=granularity,
            ad_account_id=ad_account,
        )
    except PlatformAPIError as exc:
        _fail(exc)
    if grep:
        pattern = re.compile(grep, re.IGNORECASE)
        rows = [row for row in rows if pattern.search(row.get("searchTerm", ""))]
    rows.sort(key=lambda row: (-row.get("searchPopularity1to100", 0), row.get("rankInGenre", 0)))
    rows = rows[:limit]
    if json_output:
        typer.echo(json.dumps(rows, ensure_ascii=False, indent=1))
        return
    scope = genre or "all genres"
    console.print(
        f"[bold]{country} / {scope} / {granularity} {window[0]}..{window[1]} / {len(rows)} rows[/bold]"
    )
    console.print(f"{'pop':>4} {'rank':>5}  {'genre':<22} {'period':<11} term")
    for row in rows:
        period = row.get("week") or row.get("month") or ""
        console.print(
            f"{row.get('searchPopularity1to100', '-'):>4} "
            f"{row.get('rankInGenre', '-'):>5}  "
            f"{row.get('genre', ''):<22} {period:<11} {row.get('searchTerm', '')}"
        )


@app.command("genres")
def genres(
    country: str = typer.Option(..., "--country", help="Storefront country code (US/GB/JP/...)"),
    ad_account: Optional[str] = typer.Option(
        None, "--ad-account", envvar="ASA_AD_ACCOUNT_ID", help="Apple Ads Platform ad account ID"
    ),
) -> None:
    """List genre enum values present in the latest weekly popularity data."""
    start, end = latest_complete_week(datetime.now(UTC))
    try:
        rows = fetch_popularity(
            country=country,
            genre=None,
            start=start,
            end=end,
            granularity="WEEKLY_SUN_SAT",
            ad_account_id=ad_account,
        )
    except PlatformAPIError as exc:
        _fail(exc)
    counts: dict[str, int] = {}
    for row in rows:
        counts[row.get("genre", "")] = counts.get(row.get("genre", ""), 0) + 1
    console.print(f"[bold]{country} / week {start}..{end} / {len(rows)} rows[/bold]")
    for name, count in sorted(counts.items(), key=lambda item: -item[1]):
        console.print(f"  {count:>5}  {name}")


@app.command("sugg")
def suggestions(
    country: str = typer.Option(..., "--country", help="Storefront country code (US/GB/JP/...)"),
    seeds: Optional[str] = typer.Option(
        None,
        "--seeds",
        help=(
            "Comma-separated seed terms for long-tail expansion. "
            "Seeded popularity is worldwide, not per-country."
        ),
    ),
    grep: Optional[str] = typer.Option(
        None, "--grep", help="Case-insensitive regex filter on the suggestion text"
    ),
    app_id: Optional[str] = typer.Option(
        None, "--app-id", help="adamId override (defaults to the active app in config)"
    ),
    limit: int = typer.Option(50, "--limit", min=1, help="Maximum rows to display"),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON"),
    ad_account: Optional[str] = typer.Option(
        None, "--ad-account", envvar="ASA_AD_ACCOUNT_ID", help="Apple Ads Platform ad account ID"
    ),
) -> None:
    """Apple keyword suggestions for the promoted app (optionally seeded)."""
    if app_id is None:
        app_config = get_current_app_config()
        if app_config is None or not app_config.app_id:
            console.print(
                "[red]No active app in config. Pass --app-id or run 'asa config setup'.[/red]"
            )
            raise typer.Exit(1)
        app_id = str(app_config.app_id)
    filters: list[dict[str, Any]] = [
        {"field": "promotedObjectId", "operator": "EQUALS", "value": [app_id]},
        {"field": "promotedObjectType", "operator": "EQUALS", "value": ["APPSTORE_APP"]},
        {"field": "countriesOrRegions", "operator": "IN", "value": [country]},
    ]
    seed_terms = [term.strip() for term in (seeds or "").split(",") if term.strip()]
    if seed_terms:
        filters.append({"field": "terms", "operator": "IN", "value": seed_terms})
    rows: list[dict[str, Any]] = []
    offset = 0
    try:
        while offset < _SUGG_MAX_ROWS:
            request = hydrate_model(
                "RecommendationQueryRequest",
                {
                    "filters": filters,
                    "pagination": {"offset": offset, "pageSize": _SUGG_PAGE_SIZE},
                },
            )
            response = invoke(
                "query_keyword_suggestions",
                arguments={"recommendation_query_request": request},
                ad_account_id=ad_account,
            )
            page = (response or {}).get("result") or []
            rows.extend(page)
            total = ((response or {}).get("pagination") or {}).get("totalCount", len(rows))
            offset += len(page)
            if not page or offset >= total:
                break
    except PlatformAPIError as exc:
        _fail(exc)
    if grep:
        pattern = re.compile(grep, re.IGNORECASE)
        rows = [row for row in rows if pattern.search(row.get("text", ""))]
    rows.sort(key=lambda row: -(row.get("popularity") or 0))
    rows = rows[:limit]
    if json_output:
        typer.echo(json.dumps(rows, ensure_ascii=False, indent=1))
        return
    scope = (
        f"seeds: {', '.join(seed_terms)} (worldwide popularity)"
        if seed_terms
        else "unseeded (per-country popularity)"
    )
    console.print(f"[bold]{country} / app {app_id} / {scope} / {len(rows)} rows[/bold]")
    for row in rows:
        console.print(f"  {row.get('popularity', '-'):>4}  {row.get('text', '')}")
