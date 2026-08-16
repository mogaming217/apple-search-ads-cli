<!-- Generated from the canonical SDK manifest and registered Typer trees. Do not edit by hand. -->

# Workflow command inventory

This namespace contains 6 public command leaves. Workflows are higher-level local logic, not one-to-one SDK endpoint coverage.

## Contents

- `asa workflows campaigns audit`
- `asa workflows campaigns plan-four-structure`
- `asa workflows campaigns plan-maximize-conversions`
- `asa workflows keywords genres`
- `asa workflows keywords pop`
- `asa workflows keywords sugg`

## `asa workflows campaigns audit`

Read and audit campaign strategy without changing live state.

- Usage: `Usage: asa workflows campaigns audit [OPTIONS]`

### Inputs

| Kind | Name or flags | Required | Type | Default | Environment | Help |
|---|---|---|---|---|---|---|
| option | `--ad-account` | no | `text` | — | `ASA_AD_ACCOUNT_ID` | Apple Ads Platform ad account ID |
| option | `--page-size` | no | `integer range` | `100` | — | Campaigns per SDK query |
| option | `--strategy` | no | `choice` | `RequestedStrategy.AUTO` | — | Audit auto-detected, manual search-results, or Maximize Conversions rules |
| option | `--evidence-file` | no | `file` | — | — | Optional JSON evidence for ad groups, negatives, eligibility, or target CPA |
| option | `--help` | no | `boolean` | `False` | — | Show this message and exit. |

## `asa workflows campaigns plan-four-structure`

Plan manual search-results themes with no live writes.

- Usage: `Usage: asa workflows campaigns plan-four-structure [OPTIONS]`

### Inputs

| Kind | Name or flags | Required | Type | Default | Environment | Help |
|---|---|---|---|---|---|---|
| option | `--countries` | no | `text` | — | — | Comma-separated country or region codes; defaults to configured app countries |
| option | `--daily-budget` | no | `float range` | — | — | Planning value per campaign; no API mutation is sent |
| option | `--grouping` | no | `text` | `separate-campaigns` | — | Use separate-campaigns or themed-ad-groups for manual search-results themes |
| option | `--objective` | no | `text` | `Manual search-results keyword control and learning` | — | Owner-supplied planning objective |
| option | `--help` | no | `boolean` | `False` | — | Show this message and exit. |

## `asa workflows campaigns plan-maximize-conversions`

Plan Maximize Conversions using optional safe live reads and no writes.

- Usage: `Usage: asa workflows campaigns plan-maximize-conversions [OPTIONS]`

### Inputs

| Kind | Name or flags | Required | Type | Default | Environment | Help |
|---|---|---|---|---|---|---|
| option | `--daily-budget` | yes | `float range` | — | — | Proposed daily budget; retained as unapproved planning data |
| option | `--target-cpa` | no | `float range` | — | — | Owner-proposed target CPA; otherwise use Apple or evidence suggestion |
| option | `--adam-id` | no | `text` | — | — | App Store adam ID |
| option | `--countries` | no | `text` | — | — | Comma-separated country or region codes; defaults to configured app countries |
| option | `--ad-account` | no | `text` | — | `ASA_AD_ACCOUNT_ID` | When supplied, collect read-only Apple eligibility and target-CPA evidence |
| option | `--evidence-file` | no | `file` | — | — | Optional saved Apple eligibility, suggestion, or recommendation JSON |
| option | `--pre-order` | no | `boolean` | `False` | — | Mark the app as pre-order |
| option | `--campaign-created-at` | no | `text` | — | — | ISO-8601 creation timestamp for the two-week learning guard |
| option | `--help` | no | `boolean` | `False` | — | Show this message and exit. |

## `asa workflows keywords genres`

List genre enum values present in the latest weekly popularity data.

- Usage: `Usage: asa workflows keywords genres [OPTIONS]`

### Inputs

| Kind | Name or flags | Required | Type | Default | Environment | Help |
|---|---|---|---|---|---|---|
| option | `--country` | yes | `text` | — | — | Storefront country code (US/GB/JP/...) |
| option | `--ad-account` | no | `text` | — | `ASA_AD_ACCOUNT_ID` | Apple Ads Platform ad account ID |
| option | `--help` | no | `boolean` | `False` | — | Show this message and exit. |

## `asa workflows keywords pop`

Search-term popularity ranking (top 500 per genre per storefront).

- Usage: `Usage: asa workflows keywords pop [OPTIONS]`

### Inputs

| Kind | Name or flags | Required | Type | Default | Environment | Help |
|---|---|---|---|---|---|---|
| option | `--country` | yes | `text` | — | — | Storefront country code (US/GB/JP/...) |
| option | `--genre` | no | `text` | — | — | Genre enum such as FOOD_DRINK (see `genres` command) |
| option | `--grep` | no | `text` | — | — | Case-insensitive regex filter on the search term |
| option | `--weeks` | no | `integer range` | `1` | — | Number of latest complete weeks |
| option | `--monthly` | no | `boolean` | `False` | — | Use monthly data instead of weekly |
| option | `--start` | no | `text` | — | — | Start date YYYY-MM-DD (auto if omitted) |
| option | `--end` | no | `text` | — | — | End date YYYY-MM-DD (auto if omitted) |
| option | `--limit` | no | `integer range` | `50` | — | Maximum rows to display |
| option | `--json` | no | `boolean` | `False` | — | Emit machine-readable JSON |
| option | `--ad-account` | no | `text` | — | `ASA_AD_ACCOUNT_ID` | Apple Ads Platform ad account ID |
| option | `--help` | no | `boolean` | `False` | — | Show this message and exit. |

## `asa workflows keywords sugg`

Apple keyword suggestions for the promoted app (optionally seeded).

- Usage: `Usage: asa workflows keywords sugg [OPTIONS]`

### Inputs

| Kind | Name or flags | Required | Type | Default | Environment | Help |
|---|---|---|---|---|---|---|
| option | `--country` | yes | `text` | — | — | Storefront country code (US/GB/JP/...) |
| option | `--seeds` | no | `text` | — | — | Comma-separated seed terms for long-tail expansion. Seeded popularity is worldwide, not per-country. |
| option | `--grep` | no | `text` | — | — | Case-insensitive regex filter on the suggestion text |
| option | `--app-id` | no | `text` | — | — | adamId override (defaults to the active app in config) |
| option | `--limit` | no | `integer range` | `50` | — | Maximum rows to display |
| option | `--json` | no | `boolean` | `False` | — | Emit machine-readable JSON |
| option | `--ad-account` | no | `text` | — | `ASA_AD_ACCOUNT_ID` | Apple Ads Platform ad account ID |
| option | `--help` | no | `boolean` | `False` | — | Show this message and exit. |
