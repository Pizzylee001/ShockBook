# ShockBook Design System (`DESIGN.md`)

## 1. Visual Direction & Ledger Rotation Proof
- **Product Name:** ShockBook (Multi-Token Stress-Test Agent, Rebalance Desk, and Track 3 MCP Skill Server for RYO-CHAN Virtual Hackathon 2026)
- **Primary Task Category:** Operate / Monitor + Research / Analyze (`#34 Exaggerated Minimalism` + `#29 Kinetic Typography` + `#52 Predictive Analytics` [supplemental] + `#46 Heat Map & Heatmap Style` [supplemental])
- **Dials:** `VARIANCE = 8`, `MOTION = 6`, `DENSITY = 8` (`ENERGY = 7`, `RHYTHM = 8`, `MOTION = 6`)
- **Theme Polarity:** `Both` (`Carbon Void #07080C` default + `Alabaster Paper #ECE9E1` toggle)
- **Structural Fingerprint (`08-anti-slop-filter.md`):**
  1. Hero layout: `1-sticky-pinned` (Command Bar + Monumental 30-Second Stress-Field Hero Strip)
  2. Grid rhythm: `2-asymmetric-grid-spans` (`5:7` and `7:5` exposed architectural cells)
  3. Divider treatment: `3-double-rule` (`3px double` structural header rule + `2px solid` cell hairlines + `+` corner registration marks)
  4. CTA pattern: `4-form-as-CTA` (Interactive BTC Shock Vector Scrubber + Seal & Commit Mandate action)
  5. Card chrome: `5-none` (`0px` border radius, zero drop shadows, zero rounded container boxes)
  6. Motion signature: `6-horizontal-sweep` + `DecryptScramble` cryptographic hash reveal

## 2. Color Tokens (Architectural Chiaroscuro)
### Dark Mode (`Carbon Void` - Default)
- `--bg-void`: `#07080C`
- `--bg-paper`: `#0C0E14`
- `--bg-elevated`: `#11151F`
- `--ink-primary`: `#F3F1EC`
- `--ink-secondary`: `#B8B5AD`
- `--ink-muted`: `#7E7B74`
- `--cobalt`: `#2952FF`
- `--cobalt-bright`: `#4D73FF`
- `--crimson`: `#FF2A4B`
- `--emerald`: `#00D68F`
- `--gold`: `#EAB308`

### Light Mode (`Alabaster Paper` - Toggle)
- `--bg-void`: `#ECE9E1`
- `--bg-paper`: `#F5F3EE`
- `--bg-elevated`: `#FFFFFF`
- `--ink-primary`: `#090B10`
- `--ink-secondary`: `#363942`
- `--ink-muted`: `#646873`
- `--cobalt`: `#0038FF`
- `--cobalt-bright`: `#1A4BFF`
- `--crimson`: `#D91E36`
- `--emerald`: `#047857`
- `--gold`: `#B45309`

## 3. Self-Hosted Typography (`/static/fonts.css`)
All fonts are self-hosted Latin WOFF2 files with zero external network calls:
- **Display & Architectural Headers:** `Chakra Petch` (`600`, `700`), uppercase tracking `-0.02em`
- **Body & Analytical Evidence:** `Public Sans` (`400`, `500`, `600`, `700`), `60ch-70ch` max measure
- **Tabular Numerals, Equations & Hashes:** `Space Mono` (`400`, `700`) with `font-variant-numeric: tabular-nums`

## 4. Custom Visual & Chart Components
1. **HTML5 Canvas Stress-Field Contour Shader:** Topographic shock-wave contour lines behind the command stage whose wave amplitude and frequency respond to the active shock scenario (`-5%` to `-30%`), pausing offscreen and under `prefers-reduced-motion`.
2. **168H Realized Equity + 48H Shock Cone Fan Chart (`Line with Confidence Band`):** Compares realized 7-day portfolio equity and branches at `T0` into the Unhedged Shock Cone (`1sigma/2sigma` crimson confidence fan) vs. the Rebalance Mandate Path (`1sigma/2sigma` cobalt/emerald fan) against the user's max dollar drawdown guardrail line.
3. **Alluvial / Sankey Capital Rotation Vector:** Maps exact dollar re-allocation from high-beta correlated assets (`SOL`, `AVAX`) into core anchor (`BTC`) and drawdown shield (`USDC`).
4. **Cumulative Waterfall Variance Attribution Chart:** Decomposes how each trim and correlation relief step recovers tail drawdown to bring the book back under the dollar cap.
5. **168H Pairwise Correlation Matrix + Joint-Return Scatter Lens:** Interactive `N x N` correlation heatmap with non-color `[!]` breach markers paired with a live 168-hour joint log-return scatter plot and OLS regression slope (`beta`).
6. **DecryptScramble SHA-256 Receipt Verification:** Cryptographic character-scramble verification on deterministic replay of SQLite WAL committed mandates.

## 5. Navigation & Routes (`N3` + `Ft5`)
- `/desk`: **Stress Desk** (Multi-token portfolio builder, live shock vector scrubber, 30-second risk diff, fan cone, Sankey rotation, waterfall attribution, correlation matrix + scatter lens, Risk Officer audit trail, and practice mandate commit)
- `/ledger`: **Mandate Ledger** (SQLite WAL committed rebalance mandates, live counterfactual P&L settlement against current OKX spot prices, and one-click SHA-256 deterministic replay verification)
- `/skills`: **MCP Skill Workbench** (Interactive Track 3 MCP skill runner and fault-injection resilience drill for `portfolio_stress_test` and `correlation_guard` over both REST and JSON-RPC `2024-11-05`)
