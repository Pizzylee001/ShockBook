import os
import tempfile
import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def temp_db_path():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.environ["SHOCKBOOK_DB_PATH"] = path
    yield path
    if os.path.exists(path):
        os.remove(path)


def test_market_math_covariance_and_shock():
    from backend.market_math import (
        compute_portfolio_stress,
        compute_correlation_matrix,
        generate_deterministic_candles,
    )

    candles_by_symbol = {
        "BTC": generate_deterministic_candles("BTC", base_price=88500.0, vol=0.014),
        "SOL": generate_deterministic_candles("SOL", base_price=212.0, vol=0.026, btc_coupling=0.84),
        "AVAX": generate_deterministic_candles("AVAX", base_price=36.5, vol=0.028, btc_coupling=0.82),
        "ETH": generate_deterministic_candles("ETH", base_price=3280.0, vol=0.018, btc_coupling=0.79),
        "USDC": generate_deterministic_candles("USDC", base_price=1.0, vol=0.0001, btc_coupling=0.0),
    }

    corr_result = compute_correlation_matrix(
        symbols=["SOL", "AVAX", "BTC", "ETH"],
        candles_by_symbol=candles_by_symbol,
        correlation_cap=0.75,
    )
    assert "matrix" in corr_result
    assert "breach_pairs" in corr_result
    assert corr_result["max_pair_correlation_168h"] > 0.75
    assert len(corr_result["breach_pairs"]) >= 1

    stress = compute_portfolio_stress(
        portfolio_usd=20000.0,
        positions=[
            {"symbol": "SOL", "weight": 0.42},
            {"symbol": "AVAX", "weight": 0.28},
            {"symbol": "BTC", "weight": 0.20},
            {"symbol": "USDC", "weight": 0.10},
        ],
        shock_btc_pct=-15.0,
        scenario_id="btc_crash_15",
        max_drawdown_usd=2000.0,
        correlation_cap=0.75,
        candles_by_symbol=candles_by_symbol,
        ryo_enrichment={"perp_funding_rate_bps": 1.42, "ryo_sentiment_regime": "cautious_bullish"},
    )

    # Unhedged drawdown should be worse (more negative) than rebalanced drawdown
    assert stress["unhedged_drawdown_usd"] < stress["rebalanced_drawdown_usd"]
    assert stress["capital_preserved_usd"] > 0
    assert abs(sum(stress["mandate_weights"].values()) - 1.0) < 1e-4
    assert len(stress["fan_chart"]["realized_168h"]) >= 8
    assert len(stress["fan_chart"]["unhedged_48h"]) >= 4
    assert len(stress["fan_chart"]["mandate_48h"]) >= 4
    assert len(stress["waterfall_steps"]) == 5
    assert len(stress["sankey_flows"]) >= 2


def test_null_integrity_never_zero_fills():
    from backend.market_math import compute_portfolio_stress, generate_deterministic_candles

    candles_by_symbol = {
        "BTC": generate_deterministic_candles("BTC", base_price=88500.0, vol=0.014),
        "SOL": generate_deterministic_candles("SOL", base_price=212.0, vol=0.026, btc_coupling=0.84),
        "AVAX": generate_deterministic_candles("AVAX", base_price=36.5, vol=0.028, btc_coupling=0.82),
        "USDC": generate_deterministic_candles("USDC", base_price=1.0, vol=0.0001, btc_coupling=0.0),
    }

    # Explicitly pass None for perp_funding_rate_bps and ryo_sentiment_regime
    stress = compute_portfolio_stress(
        portfolio_usd=20000.0,
        positions=[
            {"symbol": "SOL", "weight": 0.42},
            {"symbol": "AVAX", "weight": 0.28},
            {"symbol": "BTC", "weight": 0.20},
            {"symbol": "USDC", "weight": 0.10},
        ],
        shock_btc_pct=-15.0,
        scenario_id="btc_crash_15",
        max_drawdown_usd=2000.0,
        correlation_cap=0.75,
        candles_by_symbol=candles_by_symbol,
        ryo_enrichment={"perp_funding_rate_bps": None, "ryo_sentiment_regime": None},
    )

    assert stress["perp_funding_rate_bps"] is None
    assert stress["ryo_sentiment_regime"] is None


def test_sqlite_wal_mandate_commit_and_deterministic_replay(temp_db_path):
    from backend.db import init_db, commit_mandate, list_mandates, verify_mandate_replay

    init_db(temp_db_path)
    payload = {
        "portfolio_usd": 20000.0,
        "shock_btc_pct": -15.0,
        "scenario_label": "BTC -15% Flash Crash",
        "max_drawdown_usd": 2000.0,
        "correlation_cap": 0.75,
        "initial_weights": {"SOL": 0.42, "AVAX": 0.28, "BTC": 0.20, "USDC": 0.10},
        "mandate_weights": {"SOL": 0.22, "AVAX": 0.14, "BTC": 0.34, "USDC": 0.30},
        "entry_prices": {"SOL": 212.0, "AVAX": 36.5, "BTC": 88500.0, "USDC": 1.0},
        "unhedged_drawdown_usd": -3420.0,
        "rebalanced_drawdown_usd": -1690.0,
        "capital_preserved_usd": 1730.0,
        "max_pair_correlation_168h": 0.86,
        "evidence_summary": "SOLxAVAX correlation 0.86 breaches 0.75 cap under -15% BTC shock.",
    }

    created = commit_mandate(payload, db_path=temp_db_path)
    assert created["mandate_id"].startswith("MND-")
    assert len(created["sha256_hash"]) == 64

    rows = list_mandates(
        current_prices={"SOL": 195.0, "AVAX": 32.8, "BTC": 85200.0, "USDC": 1.0},
        db_path=temp_db_path,
    )
    assert len(rows) >= 1
    first = rows[0]
    assert first["mandate_id"] == created["mandate_id"]
    assert first["counterfactual"]["alpha_preserved_usd"] > 0

    replay = verify_mandate_replay(created["mandate_id"], db_path=temp_db_path)
    assert replay["verified"] is True
    assert replay["computed_sha256"] == created["sha256_hash"]


def test_track3_mcp_rest_and_jsonrpc_endpoints(temp_db_path):
    from main import app

    client = TestClient(app)

    # 1. Health check
    r_health = client.get("/api/mcp/health")
    assert r_health.status_code == 200
    assert r_health.json()["protocol_version"] == "2024-11-05"

    # 2. Catalog
    r_tools = client.get("/api/mcp/tools")
    assert r_tools.status_code == 200
    tool_names = [t["name"] for t in r_tools.json()["tools"]]
    assert "portfolio_stress_test" in tool_names
    assert "correlation_guard" in tool_names

    # 3. Call portfolio_stress_test (REST)
    r_call = client.post(
        "/api/mcp/tools/portfolio_stress_test/call",
        json={
            "arguments": {
                "portfolio_usd": 20000,
                "positions": [
                    {"symbol": "SOL", "weight": 0.42},
                    {"symbol": "AVAX", "weight": 0.28},
                    {"symbol": "BTC", "weight": 0.20},
                    {"symbol": "USDC", "weight": 0.10},
                ],
                "shock_btc_pct": -15.0,
                "max_drawdown_usd": 2000.0,
                "correlation_cap": 0.75,
            }
        },
    )
    assert r_call.status_code == 200
    env = r_call.json()
    required_keys = {
        "schema_version",
        "tool",
        "status",
        "data_mode",
        "as_of",
        "request",
        "data",
        "summary",
        "availability",
        "warnings",
    }
    assert required_keys.issubset(set(env.keys()))
    assert env["tool"] == "portfolio_stress_test"
    assert env["status"] in ("ok", "partial")

    # 4. Call with fault_mode="null_perp" to verify explicit null preservation
    r_null = client.post(
        "/api/mcp/tools/portfolio_stress_test/call",
        json={
            "arguments": {
                "portfolio_usd": 20000,
                "shock_btc_pct": -15.0,
                "fault_mode": "null_perp",
            }
        },
    )
    assert r_null.status_code == 200
    null_env = r_null.json()
    assert null_env["status"] == "partial"
    assert null_env["data_mode"] == "mixed"
    assert null_env["data"]["perp_funding_rate_bps"] is None

    # 5. JSON-RPC 2.0 tools/call
    r_rpc = client.post(
        "/api/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 99,
            "method": "tools/call",
            "params": {
                "name": "correlation_guard",
                "arguments": {
                    "symbols": ["SOL", "AVAX", "BTC", "ETH"],
                    "correlation_cap": 0.75,
                },
            },
        },
    )
    assert r_rpc.status_code == 200
    rpc_body = r_rpc.json()
    assert rpc_body["jsonrpc"] == "2.0"
    assert rpc_body["id"] == 99
    assert "structuredContent" in rpc_body["result"]
    assert rpc_body["result"]["structuredContent"]["tool"] == "correlation_guard"


def test_all_three_routes_render_and_link(temp_db_path):
    from main import app

    client = TestClient(app)
    for route in ["/desk", "/ledger", "/skills"]:
        resp = client.get(route)
        assert resp.status_code == 200
        html = resp.text
        assert "/static/fonts.css" in html
        assert 'href="/desk"' in html
        assert 'href="/ledger"' in html
        assert 'href="/skills"' in html
        # Ensure zero em dashes in rendered HTML
        assert "\u2014" not in html
        # Ensure no raw /desk, /ledger, /skills route pills in nav text
        assert '<span class="route-pill">' not in html


def test_end_to_end_stress_and_mandate_http_workflow(temp_db_path):
    from main import app

    client = TestClient(app)

    # 1. Run custom Book B stress test via POST /api/stress/run
    r_stress = client.post(
        "/api/stress/run",
        json={
            "portfolio_usd": 25000.0,
            "positions": [
                {"symbol": "INJ", "weight": 0.45},
                {"symbol": "SUI", "weight": 0.30},
                {"symbol": "ETH", "weight": 0.15},
                {"symbol": "USDC", "weight": 0.10},
            ],
            "shock_btc_pct": -18.0,
            "scenario_id": "corr_to_1_crunch",
            "max_drawdown_usd": 2200.0,
            "correlation_cap": 0.75,
            "use_live_llm": False,
        },
    )
    assert r_stress.status_code == 200
    body = r_stress.json()
    assert body["stress"]["portfolio_usd"] == 25000.0
    assert body["stress"]["capital_preserved_usd"] > 0
    assert len(body["evidence_sha256"]) == 64

    # 2. Commit mandate via POST /api/mandates/commit
    r_commit = client.post(
        "/api/mandates/commit",
        json={
            "portfolio_usd": 25000.0,
            "positions": [
                {"symbol": "INJ", "weight": 0.45},
                {"symbol": "SUI", "weight": 0.30},
                {"symbol": "ETH", "weight": 0.15},
                {"symbol": "USDC", "weight": 0.10},
            ],
            "shock_btc_pct": -18.0,
            "scenario_label": "Corr-to-1 Crunch (-18%)",
            "max_drawdown_usd": 2200.0,
            "correlation_cap": 0.75,
        },
    )
    assert r_commit.status_code == 200
    committed = r_commit.json()
    m_id = committed["mandate_id"]

    # 3. Verify SHA-256 deterministic replay via GET /api/mandates/{id}/verify
    r_verify = client.get(f"/api/mandates/{m_id}/verify")
    assert r_verify.status_code == 200
    ver = r_verify.json()
    assert ver["verified"] is True
    assert ver["computed_sha256"] == committed["sha256_hash"]


def test_zero_em_dashes_across_codebase():
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    for ext in ("*.py", "*.html", "*.js", "*.css", "*.md"):
        for fpath in root.rglob(ext):
            if ".git" in fpath.parts or ".venv" in fpath.parts:
                continue
            text = fpath.read_text(encoding="utf-8")
            assert "\u2014" not in text, f"Found forbidden em dash in {fpath}"


def test_no_secrets_in_tracked_files():
    import re
    from pathlib import Path

    ryo_secret_re = re.compile(r"ryo_mcp_[0-9a-f]{8}_[A-Za-z0-9_-]{20,}")
    river_secret_re = re.compile(r"rv_[A-Za-z0-9_-]{25,}")

    root = Path(__file__).resolve().parent.parent
    for ext in ("*.py", "*.html", "*.js", "*.css", "*.md", "*.json"):
        for fpath in root.rglob(ext):
            if ".git" in fpath.parts or ".venv" in fpath.parts or fpath.name == ".env":
                continue
            text = fpath.read_text(encoding="utf-8")
            assert not ryo_secret_re.search(text), f"RYO secret leaked in {fpath}"
            assert not river_secret_re.search(text), f"River AI key leaked in {fpath}"



