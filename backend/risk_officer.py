import json
import os
import time
from typing import Any, Dict, List
import httpx

_OFFICER_CACHE: Dict[str, Dict[str, Any]] = {}
_OFFICER_TTL = 300.0


def build_deterministic_audit_trail(stress: Dict[str, Any]) -> List[Dict[str, str]]:
    max_pair = stress.get("max_pair_label", "SOL×AVAX")
    max_corr = stress.get("max_pair_correlation_168h", 0.86)
    cap = stress.get("correlation_cap", 0.75)
    shock_pct = stress.get("shock_btc_pct", -15.0)
    u_loss = abs(float(stress.get("unhedged_drawdown_usd", -3420.0)))
    u_pct = abs(float(stress.get("unhedged_drawdown_pct", -17.1)))
    m_loss = abs(float(stress.get("rebalanced_drawdown_usd", -1690.0)))
    m_pct = abs(float(stress.get("rebalanced_drawdown_pct", -8.4)))
    saved = float(stress.get("capital_preserved_usd", 1730.0))
    dd_cap = float(stress.get("max_drawdown_usd", 2000.0))

    # Summarize top 2 trims
    trims = [r for r in stress.get("sankey_flows", []) if r.get("action") == "TRIM"]
    trim_desc = ", ".join(
        f"{r['symbol']} ({r['initial_pct']}% to {r['mandate_pct']}%)" for r in trims[:2]
    ) or "high-beta alts"

    step1_status = "BREACH" if max_corr > cap else "PASS"
    step2_status = "BREACH" if u_loss > dd_cap else "PASS"

    return [
        {
            "title": "COVARIANCE CLUSTER DETECTION",
            "badge": f"168H PEARSON {max_corr:.2f} ({step1_status})",
            "severity": "breach" if max_corr > cap else "pass",
            "body": (
                f"Over the trailing 168 hourly candles, {max_pair} log-returns correlate at "
                f"rho = {max_corr:.2f} against your {cap:.2f} correlation cap. Concentrated alt weights "
                f"create a single-factor drawdown cluster."
            ),
        },
        {
            "title": "SHOCK CAUSE & EFFECT",
            "badge": f"BTC {shock_pct:.1f}% SHOCK ({step2_status})",
            "severity": "breach" if u_loss > dd_cap else "pass",
            "body": (
                f"Under a {shock_pct:.1f}% BTC shock vector, tail beta compression drives an unhedged "
                f"portfolio drawdown of -${u_loss:,.2f} (-{u_pct:.1f}%), compared to your "
                f"${dd_cap:,.0f} maximum dollar drawdown guardrail."
            ),
        },
        {
            "title": "MINIMUM-VARIANCE REBALANCE MANDATE",
            "badge": f"PRESERVES +${saved:,.0f}",
            "severity": "pass",
            "body": (
                f"Trimming {trim_desc} and rotating into BTC core anchor and USDC shield "
                f"reduces shock drawdown to -${m_loss:,.2f} (-{m_pct:.1f}%), preserving +${saved:,.2f} "
                f"of capital."
            ),
        },
    ]


def synthesize_risk_officer_narrative(
    stress: Dict[str, Any], use_live_llm: bool = False, timeout_sec: float = 4.0
) -> Dict[str, Any]:
    """
    Produces the 3-step Risk Officer Audit Trail. When use_live_llm=True and River AI credentials
    are configured, calls DeepSeek-V4.1-Flash-1017 to refine the executive summary while keeping
    all numbers locked to the deterministic stress output.
    """
    deterministic_steps = build_deterministic_audit_trail(stress)
    cache_key = (
        f"{stress.get('portfolio_usd')}:{stress.get('shock_btc_pct')}:"
        f"{stress.get('max_drawdown_usd')}:{stress.get('max_pair_correlation_168h')}"
    )
    now = time.time()
    if cache_key in _OFFICER_CACHE and (now - _OFFICER_CACHE[cache_key]["ts"]) < _OFFICER_TTL:
        return _OFFICER_CACHE[cache_key]["val"]

    api_key = os.environ.get("RIVER_API_KEY", "")
    base_url = os.environ.get("RIVER_BASE_URL", "https://api.river.ai/v1").rstrip("/")
    model = os.environ.get("RIVER_MODEL", "deepseek-ai/DeepSeek-V4.1-Flash-1017")

    if not use_live_llm or not api_key:
        res = {
            "engine": "deterministic+deepseek-ready",
            "model": model,
            "steps": deterministic_steps,
            "executive_summary": deterministic_steps[1]["body"] + " " + deterministic_steps[2]["body"],
        }
        return res

    prompt = (
        "You are ShockBook's quantitative crypto Risk Officer. Write a 2-sentence plain-English "
        "executive risk verdict using ONLY these exact numbers (never invent numbers and never use "
        "an em dash character): "
        f"Portfolio=${stress.get('portfolio_usd'):,.0f}, "
        f"MaxPair={stress.get('max_pair_label')} (rho={stress.get('max_pair_correlation_168h'):.2f}, cap={stress.get('correlation_cap'):.2f}), "
        f"BTCShock={stress.get('shock_btc_pct'):.1f}%, "
        f"UnhedgedDrawdown=-${abs(stress.get('unhedged_drawdown_usd')):,.2f}, "
        f"RebalancedDrawdown=-${abs(stress.get('rebalanced_drawdown_usd')):,.2f}, "
        f"CapitalPreserved=+${stress.get('capital_preserved_usd'):,.2f}."
    )
    try:
        with httpx.Client(timeout=timeout_sec) as client:
            resp = client.post(
                f"{base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 140,
                    "temperature": 0.1,
                },
            )
            if resp.status_code == 200:
                body = resp.json()
                text = (
                    body.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")
                    .strip()
                )
                # Strip any accidental em dash from LLM output
                text = text.replace("\u2014", " - ").replace("\u2013", "-")
                if text:
                    deterministic_steps[2]["body"] = text
                    res = {
                        "engine": "live_river_ai",
                        "model": model,
                        "steps": deterministic_steps,
                        "executive_summary": text,
                    }
                    _OFFICER_CACHE[cache_key] = {"ts": now, "val": res}
                    return res
    except Exception:
        pass

    return {
        "engine": "deterministic_fallback",
        "model": model,
        "steps": deterministic_steps,
        "executive_summary": deterministic_steps[1]["body"] + " " + deterministic_steps[2]["body"],
    }
