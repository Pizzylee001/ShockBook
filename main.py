import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

from backend.db import (  # noqa: E402
    canonical_payload_json,
    commit_mandate,
    compute_sha256,
    init_db,
    list_mandates,
    verify_mandate_replay,
)
from backend.market_math import (  # noqa: E402
    compute_portfolio_stress,
    fetch_okx_168h_candles,
)
from backend.mcp_server import (  # noqa: E402
    execute_track3_skill,
    get_combined_mcp_catalog,
)
from backend.risk_officer import synthesize_risk_officer_narrative  # noqa: E402
from backend.ryo_client import fetch_ryo_whoami, probe_ryo_enrichment  # noqa: E402

app = FastAPI(
    title="ShockBook - RYO-CHAN Portfolio Stress-Test & Rebalance Desk",
    version="1.0.0",
)

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


class StressRunRequest(BaseModel):
    portfolio_usd: float = 20000.0
    positions: Optional[List[Dict[str, Any]]] = None
    shock_btc_pct: float = -15.0
    scenario_id: str = "btc_crash_15"
    max_drawdown_usd: float = 2000.0
    correlation_cap: float = 0.75
    use_live_llm: bool = False


class MandateCommitRequest(BaseModel):
    portfolio_usd: float = 20000.0
    positions: Optional[List[Dict[str, Any]]] = None
    shock_btc_pct: float = -15.0
    scenario_label: str = "BTC -15% Flash Crash"
    max_drawdown_usd: float = 2000.0
    correlation_cap: float = 0.75


def _build_workspace_context(active_route: str) -> Dict[str, Any]:
    init_db()
    positions = [
        {"symbol": "SOL", "weight": 0.42},
        {"symbol": "AVAX", "weight": 0.28},
        {"symbol": "BTC", "weight": 0.20},
        {"symbol": "USDC", "weight": 0.10},
    ]
    candles_map, _, _ = fetch_okx_168h_candles(["SOL", "AVAX", "BTC", "ETH"])
    ryo_probe = probe_ryo_enrichment("SOL", fault_mode="live")
    stress = compute_portfolio_stress(
        portfolio_usd=20000.0,
        positions=positions,
        shock_btc_pct=-15.0,
        scenario_id="btc_crash_15",
        max_drawdown_usd=2000.0,
        correlation_cap=0.75,
        candles_by_symbol=candles_map,
        ryo_enrichment=ryo_probe,
    )
    officer = synthesize_risk_officer_narrative(stress, use_live_llm=False)
    whoami = fetch_ryo_whoami()

    canon_payload = {
        "portfolio_usd": stress["portfolio_usd"],
        "shock_btc_pct": stress["shock_btc_pct"],
        "scenario_label": "BTC -15% Flash Crash",
        "max_drawdown_usd": stress["max_drawdown_usd"],
        "correlation_cap": stress["correlation_cap"],
        "initial_weights": stress["initial_weights"],
        "mandate_weights": stress["mandate_weights"],
        "entry_prices": stress["spot_prices"],
        "unhedged_drawdown_usd": stress["unhedged_drawdown_usd"],
        "rebalanced_drawdown_usd": stress["rebalanced_drawdown_usd"],
        "capital_preserved_usd": stress["capital_preserved_usd"],
        "max_pair_correlation_168h": stress["max_pair_correlation_168h"],
    }
    evidence_sha256 = compute_sha256(canonical_payload_json(canon_payload))
    mandates = list_mandates(current_prices=stress["spot_prices"])
    sample_envelope = execute_track3_skill(
        "portfolio_stress_test",
        {"portfolio_usd": 20000.0, "shock_btc_pct": -15.0, "fault_mode": "live"},
    )

    return {
        "active_route": active_route,
        "stress": stress,
        "officer": officer,
        "whoami": whoami,
        "evidence_sha256": evidence_sha256,
        "mandates": mandates,
        "sample_envelope": sample_envelope,
        "sample_envelope_json": json.dumps(sample_envelope, indent=2),
    }


@app.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def root_redirect(request: Request):
    return RedirectResponse(url="/desk", status_code=302)


@app.api_route("/desk", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def route_desk(request: Request):
    ctx = _build_workspace_context("desk")
    return templates.TemplateResponse(request, "app.html", ctx)


@app.api_route("/ledger", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def route_ledger(request: Request):
    ctx = _build_workspace_context("ledger")
    return templates.TemplateResponse(request, "app.html", ctx)


@app.api_route("/skills", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def route_skills(request: Request):
    ctx = _build_workspace_context("skills")
    return templates.TemplateResponse(request, "app.html", ctx)


@app.post("/api/stress/run")
async def api_stress_run(req: StressRunRequest):
    positions = req.positions or [
        {"symbol": "SOL", "weight": 0.42},
        {"symbol": "AVAX", "weight": 0.28},
        {"symbol": "BTC", "weight": 0.20},
        {"symbol": "USDC", "weight": 0.10},
    ]
    candles_map, _, _ = fetch_okx_168h_candles(["SOL", "AVAX", "BTC", "ETH"])
    ryo_probe = probe_ryo_enrichment("SOL")
    stress = compute_portfolio_stress(
        portfolio_usd=req.portfolio_usd,
        positions=positions,
        shock_btc_pct=req.shock_btc_pct,
        scenario_id=req.scenario_id,
        max_drawdown_usd=req.max_drawdown_usd,
        correlation_cap=req.correlation_cap,
        candles_by_symbol=candles_map,
        ryo_enrichment=ryo_probe,
    )
    officer = synthesize_risk_officer_narrative(stress, use_live_llm=req.use_live_llm)
    canon_payload = {
        "portfolio_usd": stress["portfolio_usd"],
        "shock_btc_pct": stress["shock_btc_pct"],
        "scenario_label": f"BTC {req.shock_btc_pct}% Shock",
        "max_drawdown_usd": stress["max_drawdown_usd"],
        "correlation_cap": stress["correlation_cap"],
        "initial_weights": stress["initial_weights"],
        "mandate_weights": stress["mandate_weights"],
        "entry_prices": stress["spot_prices"],
        "unhedged_drawdown_usd": stress["unhedged_drawdown_usd"],
        "rebalanced_drawdown_usd": stress["rebalanced_drawdown_usd"],
        "capital_preserved_usd": stress["capital_preserved_usd"],
        "max_pair_correlation_168h": stress["max_pair_correlation_168h"],
    }
    evidence_sha256 = compute_sha256(canonical_payload_json(canon_payload))
    return {
        "stress": stress,
        "officer": officer,
        "evidence_sha256": evidence_sha256,
    }


@app.get("/api/mandates")
async def api_list_mandates():
    candles_map, _, _ = fetch_okx_168h_candles(["SOL", "AVAX", "BTC", "ETH"])
    spot_prices = {
        sym: float(c[-1]["close"]) for sym, c in candles_map.items() if c
    }
    spot_prices["USDC"] = 1.0
    return {"mandates": list_mandates(current_prices=spot_prices)}


@app.post("/api/mandates/commit")
async def api_commit_mandate(req: MandateCommitRequest):
    positions = req.positions or [
        {"symbol": "SOL", "weight": 0.42},
        {"symbol": "AVAX", "weight": 0.28},
        {"symbol": "BTC", "weight": 0.20},
        {"symbol": "USDC", "weight": 0.10},
    ]
    candles_map, _, _ = fetch_okx_168h_candles(["SOL", "AVAX", "BTC", "ETH"])
    stress = compute_portfolio_stress(
        portfolio_usd=req.portfolio_usd,
        positions=positions,
        shock_btc_pct=req.shock_btc_pct,
        max_drawdown_usd=req.max_drawdown_usd,
        correlation_cap=req.correlation_cap,
        candles_by_symbol=candles_map,
    )
    payload = {
        "portfolio_usd": stress["portfolio_usd"],
        "shock_btc_pct": stress["shock_btc_pct"],
        "scenario_label": req.scenario_label,
        "max_drawdown_usd": stress["max_drawdown_usd"],
        "correlation_cap": stress["correlation_cap"],
        "initial_weights": stress["initial_weights"],
        "mandate_weights": stress["mandate_weights"],
        "entry_prices": stress["spot_prices"],
        "unhedged_drawdown_usd": stress["unhedged_drawdown_usd"],
        "rebalanced_drawdown_usd": stress["rebalanced_drawdown_usd"],
        "capital_preserved_usd": stress["capital_preserved_usd"],
        "max_pair_correlation_168h": stress["max_pair_correlation_168h"],
        "evidence_summary": (
            f"Committed rebalance mandate under {req.scenario_label}; "
            f"preserves +${stress['capital_preserved_usd']:,.2f}."
        ),
    }
    return commit_mandate(payload)


@app.get("/api/mandates/{mandate_id}/verify")
async def api_verify_mandate(mandate_id: str):
    return verify_mandate_replay(mandate_id)


# ==================== TRACK 3 MCP SKILL SERVER ENDPOINTS ====================

@app.get("/api/mcp/health")
async def mcp_health():
    return {
        "status": "ok",
        "protocol_version": "2024-11-05",
        "server": "shockbook-ryo-mcp",
        "track3_skills": 2,
        "upstream_ryo_tools": 6,
        "tools": 8,
    }


@app.get("/api/mcp/whoami")
async def mcp_whoami():
    return fetch_ryo_whoami()


@app.get("/api/mcp/tools")
async def mcp_tools():
    return get_combined_mcp_catalog()


@app.post("/api/mcp/tools/{tool_name}/call")
async def mcp_call_tool(tool_name: str, request: Request):
    try:
        body = await request.json()
    except Exception:
        body = {}
    arguments = body.get("arguments") if isinstance(body, dict) and "arguments" in body else body
    envelope = execute_track3_skill(tool_name, arguments)
    return JSONResponse(content=envelope)


@app.post("/api/mcp")
async def mcp_jsonrpc(request: Request):
    try:
        payload = await request.json()
    except Exception:
        return JSONResponse(
            status_code=400,
            content={"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}},
        )

    rpc_id = payload.get("id")
    method = payload.get("method", "")
    params = payload.get("params") or {}

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": rpc_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "shockbook-ryo-mcp", "version": "1.0.0"},
            },
        }

    if method == "tools/list":
        cat = get_combined_mcp_catalog()
        return {
            "jsonrpc": "2.0",
            "id": rpc_id,
            "result": {"tools": cat["tools"]},
        }

    if method == "tools/call":
        tool_name = params.get("name", "")
        arguments = params.get("arguments") or {}
        envelope = execute_track3_skill(tool_name, arguments)
        return {
            "jsonrpc": "2.0",
            "id": rpc_id,
            "result": {
                "content": [{"type": "text", "text": json.dumps(envelope)}],
                "structuredContent": envelope,
                "isError": envelope.get("status") == "error",
            },
        }

    return {
        "jsonrpc": "2.0",
        "id": rpc_id,
        "error": {"code": -32601, "message": f"Method '{method}' not found"},
    }
