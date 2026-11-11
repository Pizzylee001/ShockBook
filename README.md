# ShockBook

**Multi-Token Portfolio Stress-Test Agent, Rebalance Desk, and Track 3 MCP Skill Server for RYO-CHAN**

[![Live Deployment](https://img.shields.io/badge/Live_Deployment-shockbook.vercel.app-FF5526?style=flat-square)](https://shockbook.vercel.app)
[![Hackathon](https://img.shields.io/badge/RYO--CHAN_Hackathon_2026-Tracks_1_%7C_2_%7C_3-2B6BFF?style=flat-square)](https://ryobuild.com/hackathon)
[![Test Suite](https://img.shields.io/badge/Pytest_Suite-8%2F8_Passing-16C784?style=flat-square)](./tests/test_shockbook.py)
[![License: MIT](https://img.shields.io/badge/License-MIT-F2EFE9?style=flat-square)](./LICENSE)

- **Live Production App:** [https://shockbook.vercel.app](https://shockbook.vercel.app)
- **Stress Desk Cockpit (`/desk`):** [https://shockbook.vercel.app/desk](https://shockbook.vercel.app/desk)
- **Mandate Audit Ledger (`/ledger`):** [https://shockbook.vercel.app/ledger](https://shockbook.vercel.app/ledger)
- **Track 3 MCP Skill Workbench (`/skills`):** [https://shockbook.vercel.app/skills](https://shockbook.vercel.app/skills)
- **Track 3 MCP JSON-RPC Endpoint:** `POST https://shockbook.vercel.app/api/mcp/rpc`
- **Track 3 MCP Manifest:** `GET https://shockbook.vercel.app/api/mcp/manifest`

---

## Overview

RYO-CHAN provides 35+ single-token and market-regime research tools (`market_overview`, `scan_market`, `analyze_token`, `deep_analysis`, `compare_tokens`, `monitor_market_sentiment_shift`), but its native toolset is strictly single-token or pair-comparison (`compare_tokens` caps at 2 tokens and has no portfolio weight vector, covariance matrix, shock drawdown model, or position-sizing solver). When a trader holds a multi-token book (for example `SOL` + `AVAX` + `BTC` + `USDC`), looking at bullish single-token scores hides cross-asset tail risk during a market drawdown.

**ShockBook** closes that gap across all three RYO-CHAN Virtual Hackathon 2026 tracks:

1. **Track 1 (AI Agent & Decision System):** Synthesizes RYO-CHAN token/regime signals with live 168-hour OKX `1H` OHLCV price series and River AI (`deepseek-ai/DeepSeek-V4.1-Flash-1017`) to turn raw research into a specific, repeatable rebalance mandate backed by an immutable SQLite `WAL` ledger and SHA-256 replay verification.
2. **Track 2 (Operator Interface & Visualization):** Presents a single-glance quantitative risk cockpit (`Architectural Chiaroscuro` design system) with a 24-hour $1\sigma$/$2\sigma$ Portfolio Shock Cone, a Rebalance Flow Sankey diagram, a Pairwise Covariance Heatmap, and a Token Drawdown Waterfall sorted by dollar risk impact.
3. **Track 3 (MCP Skill Extension):** Packages two production-ready MCP skills (`portfolio_stress_test` and `correlation_guard`) over both JSON-RPC `2024-11-05` (`POST /api/mcp/rpc`) and REST (`POST /api/mcp/call`) so any RYO-CHAN agent can call multi-token covariance and shock sizing as native tools.

---

## System Architecture

![ShockBook System Architecture](./docs/screenshots/architecture-diagram.png)

*Self-contained HTML/SVG source: [`docs/diagrams/architecture.html`](./docs/diagrams/architecture.html)*

---

## Product Walkthrough & Screenshots

### 1. Stress Desk Cockpit (`/desk`)

The primary operator surface combines a live portfolio shock controls rail with a 62%-viewport primary canvas:
- **Portfolio Shock Trajectory Cone:** Projects unhedged vs. post-mandate equity across a 24-hour shock horizon with $1\sigma$ (68%) and $2\sigma$ (95%) volatility bands derived from 14-day ATR.
- **Rebalance Mandate Flow (Sankey):** Maps exact dollar trims from over-correlated high-beta positions (`SOL`, `AVAX`) into the `USDC` reserve buffer.
- **168h Pairwise Correlation Matrix & Drawdown Waterfall:** Highlights correlation breaches ($r > 0.75$) and ranks token drawdown contributions from largest to smallest dollar loss.
- **Risk Officer Audit:** Provides plain-language cause-and-effect synthesis with interactive beginner glosses for quantitative terms (`Beta`, `Covariance`, `ATR`, `Drawdown`).

![ShockBook Stress Desk Cockpit](./docs/screenshots/stress-desk-1440.png)

---

### 2. Mandate Audit Ledger & Counterfactual P&L (`/ledger`)

Every committed rebalance mandate is stored in SQLite (`WAL` mode, `synchronous = NORMAL`, `foreign_keys = ON`) with a canonical JSON payload and a deterministic `SHA-256` digest:
- **Counterfactual P&L Tracking:** Compares how the unhedged portfolio vs. the committed rebalance mandate performed against live market prices, surfacing total drawdown avoided.
- **Deterministic Replay Verification:** Clicking **Verify Replay Hash** recomputes the canonical `SHA-256` digest from stored weights, shock parameters, and covariance inputs to prove audit repeatability.

![ShockBook Mandate Audit Ledger](./docs/screenshots/mandate-ledger-1440.png)

---

### 3. Track 3 MCP Skill Workbench & Resilience Drill (`/skills`)

Interactive workbench for inspecting, testing, and fault-drilling the two Track 3 MCP skills (`portfolio_stress_test` and `correlation_guard`):
- **Live & Fault-Drill Modes:** Execute live calls or inject simulated upstream faults (`429 Quota Guard`, `Upstream Timeout`, `Partial Null Token`) to verify graceful degradation.
- **Full JSON Envelope Inspector:** Displays `status`, `degraded`, `cache_age_seconds`, `sources_used`, `missing_fields`, `confidence_penalty`, and `verification_hash` on every call.

![ShockBook MCP Skill Workbench](./docs/screenshots/mcp-skills-1440.png)

---

### 4. Mobile Responsive View (`375px`)

Designed for full readability across desktop (`1440px`) and mobile (`375px`) viewports without horizontal overflow or clipped controls:

<p align="center">
  <img src="./docs/screenshots/stress-desk-mobile-375.png" alt="ShockBook Mobile Stress Desk (375px)" width="375" />
</p>

---

## Hackathon Judging Alignment (Tracks 1, 2, and 3)

| Judging Criterion | Weight | How ShockBook Delivers It |
| :--- | :--- | :--- |
| **Common: Combining Sources** | 20% | Combines RYO-CHAN MCP research (`analyze_token`, `deep_analysis`, `market_overview`, `monitor_market_sentiment_shift`), OKX V5 168-hour `1H` OHLCV candles, and River AI (`deepseek-ai/DeepSeek-V4.1-Flash-1017`) into a concrete rebalance mandate. |
| **Common: Coping with Failure** | 20% | Enforces a sliding-window quota guard for RYO-CHAN's `60 RPM` cap, falls back to SQLite `WAL` cached snapshots (`DEGRADED_CACHED`) on HTTP `429` or timeout, and preserves missing upstream fields as explicit JSON `null` (`N/A (upstream null)`) rather than fabricating zeroes. |
| **Track 1: Real Thinking & Cause/Effect** | 45% | Links upstream evidence (`SOL`/`AVAX` 168h correlation $r = 0.89$, $\beta_{\text{SOL}} = 1.44$) directly to projected dollar drawdown ($-\$16,133$) and exact trim sizes ($-\$5,500$ `SOL`, $-\$3,000$ `AVAX` $\rightarrow +\$8,500$ `USDC`). |
| **Track 1: Repeatability & Execution** | 15% | Canonical JSON serialization and `SHA-256` replay verification (`POST /api/mandates/{id}/verify`) guarantee bit-identical audit verification across restarts. |
| **Track 2: Easy to Read & Sorted by Importance** | 50% | Priority-sorted KPI strip (`Mandate Verdict` $\rightarrow$ `Unhedged Shock Loss` $\rightarrow$ `Post-Mandate Loss` $\rightarrow$ `Drawdown Saved`), token rows sorted by dollar drawdown impact, and dual dark/light architectural themes (`#0D0F12` Obsidian / `#F5F2EB` Warm Alabaster). |
| **Track 2: Works for Everyone** | 10% | Responsive down to `375px`, keyboard-accessible tabs, `prefers-reduced-motion` support, and inline plain-English definitions for quantitative metrics. |
| **Track 3: Fills a Gap, Follows Spec & Usable** | 60% | Exposes `portfolio_stress_test` and `correlation_guard` via MCP JSON-RPC `2024-11-05` (`tools/list`, `tools/call`) and REST (`POST /api/mcp/call`) with strict input validation and machine-checkable error codes. |

---

## Quantitative Methodology & Explicit Null Integrity

1. **168-Hour Log/Simple Hourly Returns & Pairwise Covariance:**
   For each asset $i \in \{\text{SOL}, \text{AVAX}, \text{BTC}, \text{ETH}\}$, ShockBook computes hourly returns $r_{i,t} = (P_{i,t} - P_{i,t-1}) / P_{i,t-1}$ over $T = 168$ hours and evaluates pairwise Pearson correlation:
   $$r_{i,j} = \frac{\sum_{t=1}^{T} (r_{i,t} - \bar{r}_i)(r_{j,t} - \bar{r}_j)}{\sqrt{\sum_{t=1}^{T} (r_{i,t} - \bar{r}_i)^2} \sqrt{\sum_{t=1}^{T} (r_{j,t} - \bar{r}_j)^2}}$$
2. **Shock Beta & Volatility Penalty:**
   Each token's empirical beta against `BTC` ($\beta_i = \text{Cov}(r_i, r_{\text{BTC}}) / \text{Var}(r_{\text{BTC}})$) is combined with its 14-day Average True Range ($\text{ATR}_{14}$) to project token-level drawdown under a user-selected `BTC` shock ($\Delta_{\text{BTC}} \in [-30\%, -5\%]$).
3. **Correlation-Capped Rebalance Solver:**
   When projected portfolio loss breaches `max_drawdown_usd` or pairwise correlation exceeds `correlation_cap`, the solver trims the highest-drawdown correlated legs in proportion to their excess risk contribution and routes those proceeds into `USDC` until the portfolio satisfies the mandate ceiling.
4. **Never Zero-Fill Missing Data:**
   If an upstream token feed returns `null` or times out (for example an unindexed token symbol), ShockBook preserves `price_usd: null`, `beta_btc: null`, `atr_pct: null`, and `shock_drawdown_usd: null`, adds the path to `missing_fields`, increments `confidence_penalty`, and renders `N/A (upstream null)` in the UI.

---

## Track 3 MCP Skill Server API

### 1. Discover Skills (`GET /api/mcp/manifest` or JSON-RPC `tools/list`)

```bash
curl -s https://shockbook.vercel.app/api/mcp/manifest | jq .
```

### 2. Call `portfolio_stress_test` via JSON-RPC `2024-11-05` (`POST /api/mcp/rpc`)

```bash
curl -s -X POST https://shockbook.vercel.app/api/mcp/rpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "judge-test-1",
    "method": "tools/call",
    "params": {
      "name": "portfolio_stress_test",
      "arguments": {
        "portfolio_usd": 50000,
        "shock_btc_pct": -18.0,
        "max_drawdown_usd": -4500,
        "correlation_cap": 0.75,
        "fault_mode": "live"
      }
    }
  }' | jq .
```

### 3. Call `correlation_guard` via REST (`POST /api/mcp/call`)

```bash
curl -s -X POST https://shockbook.vercel.app/api/mcp/call \
  -H "Content-Type: application/json" \
  -d '{
    "skill": "correlation_guard",
    "portfolio_usd": 50000,
    "shock_btc_pct": -18.0,
    "correlation_cap": 0.75,
    "fault_mode": "rate_limit_429"
  }' | jq .
```

---

## Repository Structure

```text
shockbook/
├── api/
│   └── index.py                # Vercel serverless ASGI entrypoint
├── backend/
│   ├── __init__.py
│   ├── db.py                   # SQLite WAL mandate ledger, canonical JSON, SHA-256 replay
│   ├── market_math.py          # 168h OKX candles, Pearson correlation, beta, ATR, shock cone
│   ├── mcp_server.py           # Track 3 MCP skills (REST + JSON-RPC 2024-11-05)
│   ├── risk_officer.py         # River AI (DeepSeek-V4.1-Flash-1017) audit synthesis + fallback
│   └── ryo_client.py           # RYO-CHAN MCP client with 60 RPM quota guard & null safety
├── design-system/
│   └── LEDGER.md               # Project design system ledger record
├── docs/
│   ├── diagrams/
│   │   └── architecture.html   # Self-contained HTML/SVG system architecture diagram
│   └── screenshots/            # Verified desktop (1440px) and mobile (375px) screenshots
├── static/
│   ├── app.js                  # Interactive SVG charts, Stress-Field shader, MCP fault drills
│   ├── fonts.css               # Self-hosted Chakra Petch, Public Sans, and Space Mono WOFF2
│   └── styles.css              # Architectural Chiaroscuro grid and dual-polarity themes
├── templates/
│   └── app.html                # Unified template for /desk, /ledger, and /skills
├── tests/
│   └── test_shockbook.py       # 8-test TDD verification suite (math, nulls, WAL, MCP, hygiene)
├── .env.example                # Environment variable template (no secrets committed)
├── DESIGN.md                   # Governing design system specification
├── LICENSE                     # MIT License
├── main.py                     # FastAPI application entrypoint
├── requirements.txt            # Python dependencies
└── vercel.json                 # Vercel serverless routing configuration
```

---

## Local Setup & Verification

### 1. Clone and Install Dependencies

```bash
git clone https://github.com/Pizzylee001/ShockBook.git
cd ShockBook
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and populate your credentials:

```bash
cp .env.example .env
```

```ini
RYO_MCP_URL=https://app-ryochan.com/api/mcp
RYO_MCP_KEY=your_ryo_mcp_credential_here
RIVER_BASE_URL=https://api.river.ai/v1
RIVER_MODEL=deepseek-ai/DeepSeek-V4.1-Flash-1017
RIVER_API_KEY=your_river_api_key_here
PORT=8000
```

### 3. Run the Test Suite

```bash
pytest tests/test_shockbook.py -v
```

All 8 automated verification tests validate:
1. `test_market_math_covariance_and_shock`: 168h covariance matrix, beta, ATR, and rebalance mandate reduction.
2. `test_null_integrity_never_zero_fills`: Missing upstream token fields stay `None`/`null` and never become `0.0`.
3. `test_sqlite_wal_mandate_commit_and_deterministic_replay`: SQLite `WAL` persistence and `SHA-256` replay hash verification.
4. `test_track3_mcp_rest_and_jsonrpc_endpoints`: Track 3 MCP JSON-RPC `2024-11-05` and REST fault-drill modes (`live`, `rate_limit_429`, `upstream_timeout`, `partial_null_token`).
5. `test_all_three_routes_render_and_link`: `/desk`, `/ledger`, and `/skills` return HTTP `200` with complete navigation.
6. `test_end_to_end_stress_and_mandate_http_workflow`: Full HTTP stress simulation, mandate commit, and hash verification.
7. `test_zero_em_dashes_across_codebase`: Enforces prose hygiene across templates, scripts, and backend modules.
8. `test_no_secrets_in_tracked_files`: Scans all git-tracked files to guarantee zero credential leaks.

### 4. Start the Local Server

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

Open `http://localhost:8000/desk` in your browser.

---

## License

Released under the [MIT License](./LICENSE).
