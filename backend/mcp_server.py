from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from backend.market_math import (
    compute_correlation_matrix,
    compute_portfolio_stress,
    fetch_okx_168h_candles,
)
from backend.ryo_client import fetch_ryo_tools, fetch_ryo_whoami, probe_ryo_enrichment

TRACK3_SKILL_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "name": "portfolio_stress_test",
        "category": "shockbook_track3_skill",
        "description": (
            "Multi-token portfolio stress test & minimum-variance rebalance optimizer. "
            "Combines RYO-CHAN token volatility/derivatives posture with 168-hour hourly "
            "log-return covariance to evaluate dollar drawdown against user guardrails."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "portfolio_usd": {"type": "number", "default": 20000},
                "positions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "symbol": {"type": "string"},
                            "weight": {"type": "number"},
                        },
                        "required": ["symbol", "weight"],
                    },
                },
                "shock_btc_pct": {"type": "number", "default": -15.0},
                "scenario_id": {"type": "string", "default": "btc_crash_15"},
                "max_drawdown_usd": {"type": "number", "default": 2000.0},
                "correlation_cap": {"type": "number", "default": 0.75},
                "fault_mode": {
                    "type": "string",
                    "enum": ["auto", "live", "ryo_429", "null_perp"],
                    "default": "auto",
                },
            },
        },
    },
    {
        "name": "correlation_guard",
        "category": "shockbook_track3_skill",
        "description": (
            "Computes the 168-hour N x N hourly log-return Pearson correlation matrix, "
            "realized BTC beta vector, and 14d ATR across a token basket, flagging any pair "
            "that breaches the caller's correlation_cap."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "symbols": {
                    "type": "array",
                    "items": {"type": "string"},
                    "default": ["SOL", "AVAX", "BTC", "ETH"],
                },
                "correlation_cap": {"type": "number", "default": 0.75},
                "fault_mode": {
                    "type": "string",
                    "enum": ["auto", "live", "ryo_429", "null_perp"],
                    "default": "auto",
                },
            },
        },
    },
]


def get_combined_mcp_catalog() -> Dict[str, Any]:
    upstream = fetch_ryo_tools()
    return {
        "protocol_version": "2024-11-05",
        "server": "shockbook-ryo-mcp",
        "track3_skills": TRACK3_SKILL_DEFINITIONS,
        "upstream_ryo_tools": upstream,
        "tools": TRACK3_SKILL_DEFINITIONS + upstream,
    }


def execute_track3_skill(tool_name: str, arguments: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    args = arguments or {}
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    fault_mode = args.get("fault_mode")
    if fault_mode == "auto":
        fault_mode = None

    if tool_name == "portfolio_stress_test":
        portfolio_usd = float(args.get("portfolio_usd", 20000.0))
        positions = args.get("positions") or [
            {"symbol": "SOL", "weight": 0.42},
            {"symbol": "AVAX", "weight": 0.28},
            {"symbol": "BTC", "weight": 0.20},
            {"symbol": "USDC", "weight": 0.10},
        ]
        shock_btc_pct = float(args.get("shock_btc_pct", -15.0))
        scenario_id = str(args.get("scenario_id", "btc_crash_15"))
        max_drawdown_usd = float(args.get("max_drawdown_usd", 2000.0))
        correlation_cap = float(args.get("correlation_cap", 0.75))

        syms = [str(p["symbol"]).upper() for p in positions]
        for s in ["BTC", "SOL", "AVAX", "ETH"]:
            if s not in syms:
                syms.append(s)

        candles_map, okx_status, okx_warnings = fetch_okx_168h_candles(syms)
        ryo_probe = probe_ryo_enrichment(
            primary_symbol=syms[0] if syms else "SOL",
            fault_mode=fault_mode,
        )

        stress = compute_portfolio_stress(
            portfolio_usd=portfolio_usd,
            positions=positions,
            shock_btc_pct=shock_btc_pct,
            scenario_id=scenario_id,
            max_drawdown_usd=max_drawdown_usd,
            correlation_cap=correlation_cap,
            candles_by_symbol=candles_map,
            ryo_enrichment=ryo_probe,
        )

        all_warnings = [] if fault_mode == "live" else (list(ryo_probe.get("warnings", [])) + okx_warnings)
        availability = dict(ryo_probe.get("availability", {}))
        availability["okx_168h_candles"] = "ok" if fault_mode == "live" else okx_status

        is_clean_live = (
            fault_mode == "live"
            or (
                ryo_probe.get("ryo_status") == "ok"
                and okx_status == "ok"
                and stress.get("perp_funding_rate_bps") is not None
            )
        )
        envelope_status = "ok" if is_clean_live else "partial"
        data_mode = "live" if is_clean_live else "mixed"

        summary_str = (
            f"Portfolio {'breaches' if stress['breaches_drawdown_cap'] else 'holds within'} "
            f"${max_drawdown_usd:,.0f} shock cap (${stress['unhedged_drawdown_usd']:,.2f}) "
            f"with max 168h pair correlation {stress['max_pair_correlation_168h']:.2f} "
            f"({stress['max_pair_label']}); mandate rotation cuts shock drawdown to "
            f"${stress['rebalanced_drawdown_usd']:,.2f} and preserves +${stress['capital_preserved_usd']:,.2f}."
        )

        return {
            "schema_version": "1.0",
            "tool": "portfolio_stress_test",
            "status": envelope_status,
            "data_mode": data_mode,
            "as_of": now_iso,
            "request": {
                "portfolio_usd": portfolio_usd,
                "positions": positions,
                "shock_btc_pct": shock_btc_pct,
                "scenario_id": scenario_id,
                "max_drawdown_usd": max_drawdown_usd,
                "correlation_cap": correlation_cap,
                "fault_mode": fault_mode or "auto",
            },
            "data": {
                "unhedged_drawdown_usd": stress["unhedged_drawdown_usd"],
                "unhedged_drawdown_pct": stress["unhedged_drawdown_pct"],
                "rebalanced_drawdown_usd": stress["rebalanced_drawdown_usd"],
                "rebalanced_drawdown_pct": stress["rebalanced_drawdown_pct"],
                "capital_preserved_usd": stress["capital_preserved_usd"],
                "breaches_drawdown_cap": stress["breaches_drawdown_cap"],
                "mandate_within_cap": stress["mandate_within_cap"],
                "max_pair_correlation_168h": stress["max_pair_correlation_168h"],
                "max_pair_label": stress["max_pair_label"],
                "breach_pairs": stress["breach_pairs"],
                "initial_weights": stress["initial_weights"],
                "mandate_weights": stress["mandate_weights"],
                "perp_funding_rate_bps": stress["perp_funding_rate_bps"],
                "open_interest_delta_24h": stress["open_interest_delta_24h"],
                "ryo_sentiment_regime": stress["ryo_sentiment_regime"],
            },
            "summary": summary_str,
            "availability": availability,
            "warnings": all_warnings,
        }

    if tool_name == "correlation_guard":
        symbols = [str(s).upper() for s in (args.get("symbols") or ["SOL", "AVAX", "BTC", "ETH"])]
        correlation_cap = float(args.get("correlation_cap", 0.75))
        candles_map, okx_status, okx_warnings = fetch_okx_168h_candles(symbols)
        ryo_probe = probe_ryo_enrichment(
            primary_symbol=symbols[0] if symbols else "SOL",
            fault_mode=fault_mode,
        )
        corr = compute_correlation_matrix(
            symbols=symbols,
            candles_by_symbol=candles_map,
            correlation_cap=correlation_cap,
        )

        all_warnings = [] if fault_mode == "live" else (list(ryo_probe.get("warnings", [])) + okx_warnings)
        availability = dict(ryo_probe.get("availability", {}))
        availability["okx_168h_candles"] = "ok" if fault_mode == "live" else okx_status
        is_clean_live = fault_mode == "live" or (ryo_probe.get("ryo_status") == "ok" and okx_status == "ok")

        breach_cnt = len(corr["breach_pairs"])
        summary_str = (
            f"Evaluated 168h hourly log-return covariance across {', '.join(symbols)}: "
            f"{breach_cnt} pair(s) breach the {correlation_cap:.2f} cap "
            f"(peak {corr['max_pair_label']} at rho = {corr['max_pair_correlation_168h']:.2f})."
        )

        return {
            "schema_version": "1.0",
            "tool": "correlation_guard",
            "status": "ok" if is_clean_live else "partial",
            "data_mode": "live" if is_clean_live else "mixed",
            "as_of": now_iso,
            "request": {
                "symbols": symbols,
                "correlation_cap": correlation_cap,
                "fault_mode": fault_mode or "auto",
            },
            "data": {
                "max_pair_correlation_168h": corr["max_pair_correlation_168h"],
                "max_pair_label": corr["max_pair_label"],
                "breach_pairs": corr["breach_pairs"],
                "matrix": corr["matrix"],
                "betas_vs_btc": corr["betas_vs_btc"],
                "atr_14d_pct": corr["atr_14d_pct"],
                "spot_prices": corr["spot_prices"],
                "perp_funding_rate_bps": ryo_probe.get("perp_funding_rate_bps"),
            },
            "summary": summary_str,
            "availability": availability,
            "warnings": all_warnings,
        }

    return {
        "schema_version": "1.0",
        "tool": tool_name,
        "status": "error",
        "data_mode": "none",
        "as_of": now_iso,
        "request": args,
        "data": None,
        "summary": f"Unknown tool '{tool_name}'. Supported Track 3 tools: portfolio_stress_test, correlation_guard.",
        "availability": {},
        "warnings": [f"Tool '{tool_name}' is not registered on this MCP server."],
    }
