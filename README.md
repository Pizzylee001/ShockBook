# ShockBook

**Multi-Token Portfolio Stress-Test Agent, Rebalance Desk & Track 3 MCP Skill Server built on RYO-CHAN**

ShockBook is an autonomous portfolio risk officer and practice rebalance desk built for the **RYO-CHAN Virtual Hackathon 2026** (Tracks 1, 2, and 3). It bridges the gap between RYO-CHAN's single-token/macro research tools (`market_overview`, `scan_market`, `analyze_token`, `deep_analysis`, `compare_tokens`, `monitor_market_sentiment_shift`) and multi-asset portfolio risk decisions.

---

## Why ShockBook Exists (The Value Beyond Raw Endpoints)

RYO-CHAN's native MCP tools analyze one token or macro regime at a time. When a market crash hits, a holder with a 4-token portfolio (`SOL`, `AVAX`, `BTC`, `USDC`) does not lose money on isolated tokens in a vacuum; they get wiped out because high-beta altcoins correlate toward `1.0` simultaneously.

1. **Multi-Step Job:** Input a multi-token portfolio and risk guardrails (max dollar drawdown ceiling, pairwise correlation cap) -> scrub tail shock scenarios (`BTC -5%` to `-30%`, `Corr-to-1 Liquidity Crunch`, `Perp Funding Squeeze`) -> inspect the 30-second risk diff, 168H realized + 48H shock confidence-band fan chart, Sankey capital rotation, waterfall variance attribution, and 168h pairwise correlation scatter lens -> commit a signed **Practice Rebalance Mandate** to SQLite (`WAL`) -> verify SHA-256 deterministic replay and grade live counterfactual P&L.
2. **State the App Owns:** SQLite (`WAL`) database (`data/shockbook.db`) storing user portfolios, guardrail ceilings, signed Rebalance Mandates (`MND-038`+), canonical JSON snapshots, SHA-256 evidence digests, and live counterfactual P&L settlement.
3. **Output That Exists Nowhere Else:** Exact minimum-variance rebalance target weights, dollar capital preserved under tail shock, pairwise 168-hour log-return correlation breach cluster (`SOL x AVAX`), and Track 3 MCP skills (`portfolio_stress_test`, `correlation_guard`) returning RYO's 10-field public response envelope.

---

## Routes & Architecture

- **`/desk` (Stress Desk):** Interactive BTC shock vector scrubber (`-5%` to `-30%`), 30-second monument risk diff (`Unhedged Shock Loss` vs. `Mandate Rebalanced Loss` vs. `Net Capital Preserved`), 168H realized + 48H shock confidence-band fan chart, Alluvial/Sankey capital rotation flow, 5-step cumulative waterfall attribution, 168H pairwise correlation matrix with live joint-return scatter lens, and 3-step Risk Officer Audit Trail (`DeepSeek-V4.1-Flash-1017` + deterministic engine).
- **`/ledger` (Mandate Ledger):** SQLite (`WAL`) ledger of committed rebalance mandates with live counterfactual P&L grading against current OKX spot prices and one-click SHA-256 deterministic replay verification.
- **`/skills` (MCP Skill Workbench):** Live Track 3 MCP skill runner and fault-injection resilience drill (`1. Live Mode`, `2. RYO 429 Quota Guard`, `3. Perp Lane = null`) over both REST (`POST /api/mcp/tools/{tool}/call`) and JSON-RPC 2.0 (`POST /api/mcp`).

---

## Track 1, Track 2, and Track 3 Judging Alignment

| Judging Criterion | How ShockBook Satisfies It |
| :--- | :--- |
| **Common: Combining Sources (20%)** | Composes RYO-CHAN MCP (`whoami`, `tools`, `deep_analysis` ATR/perp posture) + live OKX 168-hour 1H candles (`/api/v5/market/candles`) + River AI (`deepseek-ai/DeepSeek-V4.1-Flash-1017`) into a single signed Rebalance Mandate. |
| **Common: Coping with Failure (20%)** | Handles upstream `HTTP 429 RATE_LIMITED` (`call_allowance.allowed=false`) and missing perpetual funding lanes cleanly by switching to `status: "partial"`, `data_mode: "mixed"`, and preserving unmeasured fields as explicit `null` (never converting `null` to `0`). |
| **Track 1: Autonomous Reasoning & Repeatability (60%)** | Multi-step cause-and-effect risk audit with canonical JSON serialization and SHA-256 deterministic replay verification (`/api/mandates/{id}/verify`). |
| **Track 2: Sorted by Importance & Easy to Read (60%)** | Leads with the 30-second monument risk diff and thesis headline, sorts asset positions by worst dollar shock drawdown first, and pairs color status with explicit text/symbol markers (`[!]`, `BREACH`, `PASS`). |
| **Track 3: Composable MCP Skills & Envelope Spec (60%)** | Exposes `portfolio_stress_test` and `correlation_guard` over REST and JSON-RPC `2024-11-05` using the exact 10-field public response envelope (`schema_version`, `tool`, `status`, `data_mode`, `as_of`, `request`, `data`, `summary`, `availability`, `warnings`). |

---

## Quick Start

```bash
# 1. Copy environment template and configure keys
cp .env.example .env

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the automated test suite (TDD verification)
pytest -v

# 4. Launch the server
uvicorn main:app --host 0.0.0.0 --port 8000
```
