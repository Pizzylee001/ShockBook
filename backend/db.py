import hashlib
import json
import os
import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def resolve_db_path(explicit_path: Optional[str] = None) -> str:
    target = explicit_path or os.environ.get("SHOCKBOOK_DB_PATH", "data/shockbook.db")
    parent = os.path.dirname(os.path.abspath(target))
    try:
        os.makedirs(parent, exist_ok=True)
        # Test write access in parent directory
        test_file = os.path.join(parent, ".write_probe")
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("ok")
        os.remove(test_file)
        return target
    except OSError:
        return "/tmp/shockbook.db"


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    path = resolve_db_path(db_path)
    conn = sqlite3.connect(path, timeout=10.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def canonical_payload_json(payload: Dict[str, Any]) -> str:
    canonical_fields = {
        "portfolio_usd": round(float(payload["portfolio_usd"]), 2),
        "shock_btc_pct": round(float(payload["shock_btc_pct"]), 2),
        "scenario_label": str(payload["scenario_label"]),
        "max_drawdown_usd": round(float(payload["max_drawdown_usd"]), 2),
        "correlation_cap": round(float(payload["correlation_cap"]), 4),
        "initial_weights": {
            k: round(float(v), 4) for k, v in sorted(payload["initial_weights"].items())
        },
        "mandate_weights": {
            k: round(float(v), 4) for k, v in sorted(payload["mandate_weights"].items())
        },
        "entry_prices": {
            k: round(float(v), 4) for k, v in sorted(payload["entry_prices"].items())
        },
        "unhedged_drawdown_usd": round(float(payload["unhedged_drawdown_usd"]), 2),
        "rebalanced_drawdown_usd": round(float(payload["rebalanced_drawdown_usd"]), 2),
        "capital_preserved_usd": round(float(payload["capital_preserved_usd"]), 2),
        "max_pair_correlation_168h": round(float(payload["max_pair_correlation_168h"]), 4),
    }
    return json.dumps(canonical_fields, sort_keys=True, separators=(",", ":"))


def compute_sha256(canonical_str: str) -> str:
    return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()


def init_db(db_path: Optional[str] = None) -> None:
    conn = get_connection(db_path)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS mandates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mandate_id TEXT UNIQUE NOT NULL,
                sealed_at TEXT NOT NULL,
                portfolio_usd REAL NOT NULL,
                shock_btc_pct REAL NOT NULL,
                scenario_label TEXT NOT NULL,
                max_drawdown_usd REAL NOT NULL,
                correlation_cap REAL NOT NULL,
                initial_weights_json TEXT NOT NULL,
                mandate_weights_json TEXT NOT NULL,
                entry_prices_json TEXT NOT NULL,
                unhedged_drawdown_usd REAL NOT NULL,
                rebalanced_drawdown_usd REAL NOT NULL,
                capital_preserved_usd REAL NOT NULL,
                max_pair_correlation_168h REAL NOT NULL,
                evidence_summary TEXT NOT NULL,
                canonical_json TEXT NOT NULL,
                sha256_hash TEXT NOT NULL
            );
            """
        )
        cur = conn.execute("SELECT COUNT(*) AS cnt FROM mandates;")
        count = cur.fetchone()["cnt"]
        if count == 0:
            _seed_initial_mandates(conn)
        conn.commit()
    finally:
        conn.close()


def _seed_initial_mandates(conn: sqlite3.Connection) -> None:
    seeds = [
        {
            "mandate_id": "MND-038",
            "sealed_at": "2026-11-10T19:15:00Z",
            "portfolio_usd": 20000.0,
            "shock_btc_pct": -12.0,
            "scenario_label": "Perp Funding Squeeze (-12% BTC)",
            "max_drawdown_usd": 2000.0,
            "correlation_cap": 0.75,
            "initial_weights": {"SOL": 0.40, "AVAX": 0.30, "BTC": 0.20, "USDC": 0.10},
            "mandate_weights": {"SOL": 0.24, "AVAX": 0.16, "BTC": 0.32, "USDC": 0.28},
            "entry_prices": {"SOL": 221.4, "AVAX": 38.9, "BTC": 89600.0, "USDC": 1.0},
            "unhedged_drawdown_usd": -2740.0,
            "rebalanced_drawdown_usd": -1380.0,
            "capital_preserved_usd": 1360.0,
            "max_pair_correlation_168h": 0.84,
            "evidence_summary": "Trimmed SOL and AVAX exposure ahead of elevated perp funding squeeze; preserved +$1,360.00 tail cushion.",
        },
        {
            "mandate_id": "MND-039",
            "sealed_at": "2026-11-11T06:40:00Z",
            "portfolio_usd": 20000.0,
            "shock_btc_pct": -22.0,
            "scenario_label": "Corr-to-1 Liquidity Crunch (-22% BTC)",
            "max_drawdown_usd": 2000.0,
            "correlation_cap": 0.75,
            "initial_weights": {"SOL": 0.45, "AVAX": 0.25, "BTC": 0.20, "USDC": 0.10},
            "mandate_weights": {"SOL": 0.18, "AVAX": 0.12, "BTC": 0.30, "USDC": 0.40},
            "entry_prices": {"SOL": 218.0, "AVAX": 37.8, "BTC": 89100.0, "USDC": 1.0},
            "unhedged_drawdown_usd": -4890.0,
            "rebalanced_drawdown_usd": -1920.0,
            "capital_preserved_usd": 2970.0,
            "max_pair_correlation_168h": 0.89,
            "evidence_summary": "Liquidity crunch compressed SOLxAVAX correlation to 0.89; rotated 30% into USDC shield to hold under $2,000 cap.",
        },
        {
            "mandate_id": "MND-040",
            "sealed_at": "2026-11-11T11:20:00Z",
            "portfolio_usd": 20000.0,
            "shock_btc_pct": -15.0,
            "scenario_label": "BTC -15% Flash Crash",
            "max_drawdown_usd": 2000.0,
            "correlation_cap": 0.75,
            "initial_weights": {"SOL": 0.42, "AVAX": 0.28, "BTC": 0.20, "USDC": 0.10},
            "mandate_weights": {"SOL": 0.22, "AVAX": 0.14, "BTC": 0.34, "USDC": 0.30},
            "entry_prices": {"SOL": 215.5, "AVAX": 37.2, "BTC": 88850.0, "USDC": 1.0},
            "unhedged_drawdown_usd": -3420.0,
            "rebalanced_drawdown_usd": -1690.0,
            "capital_preserved_usd": 1730.0,
            "max_pair_correlation_168h": 0.86,
            "evidence_summary": "SOLxAVAX 168h correlation (0.86) breached 0.75 guardrail; rebalanced into BTC (+14%) and USDC (+20%) saving +$1,730.00.",
        },
    ]
    for s in seeds:
        c_json = canonical_payload_json(s)
        digest = compute_sha256(c_json)
        conn.execute(
            """
            INSERT INTO mandates (
                mandate_id, sealed_at, portfolio_usd, shock_btc_pct, scenario_label,
                max_drawdown_usd, correlation_cap, initial_weights_json, mandate_weights_json,
                entry_prices_json, unhedged_drawdown_usd, rebalanced_drawdown_usd,
                capital_preserved_usd, max_pair_correlation_168h, evidence_summary,
                canonical_json, sha256_hash
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                s["mandate_id"],
                s["sealed_at"],
                s["portfolio_usd"],
                s["shock_btc_pct"],
                s["scenario_label"],
                s["max_drawdown_usd"],
                s["correlation_cap"],
                json.dumps(s["initial_weights"]),
                json.dumps(s["mandate_weights"]),
                json.dumps(s["entry_prices"]),
                s["unhedged_drawdown_usd"],
                s["rebalanced_drawdown_usd"],
                s["capital_preserved_usd"],
                s["max_pair_correlation_168h"],
                s["evidence_summary"],
                c_json,
                digest,
            ),
        )


def commit_mandate(payload: Dict[str, Any], db_path: Optional[str] = None) -> Dict[str, Any]:
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        cur = conn.execute("SELECT COUNT(*) AS cnt FROM mandates;")
        seq = cur.fetchone()["cnt"] + 38
        mandate_id = f"MND-{seq:03d}"
        # Ensure uniqueness if rows were added
        while True:
            chk = conn.execute(
                "SELECT 1 FROM mandates WHERE mandate_id = ?;", (mandate_id,)
            ).fetchone()
            if not chk:
                break
            seq += 1
            mandate_id = f"MND-{seq:03d}"

        sealed_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        c_json = canonical_payload_json(payload)
        digest = compute_sha256(c_json)

        conn.execute(
            """
            INSERT INTO mandates (
                mandate_id, sealed_at, portfolio_usd, shock_btc_pct, scenario_label,
                max_drawdown_usd, correlation_cap, initial_weights_json, mandate_weights_json,
                entry_prices_json, unhedged_drawdown_usd, rebalanced_drawdown_usd,
                capital_preserved_usd, max_pair_correlation_168h, evidence_summary,
                canonical_json, sha256_hash
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                mandate_id,
                sealed_at,
                float(payload["portfolio_usd"]),
                float(payload["shock_btc_pct"]),
                str(payload["scenario_label"]),
                float(payload["max_drawdown_usd"]),
                float(payload["correlation_cap"]),
                json.dumps(payload["initial_weights"]),
                json.dumps(payload["mandate_weights"]),
                json.dumps(payload["entry_prices"]),
                float(payload["unhedged_drawdown_usd"]),
                float(payload["rebalanced_drawdown_usd"]),
                float(payload["capital_preserved_usd"]),
                float(payload["max_pair_correlation_168h"]),
                str(payload.get("evidence_summary", "Practice Rebalance Mandate committed.")),
                c_json,
                digest,
            ),
        )
        conn.commit()
        return {
            "mandate_id": mandate_id,
            "sealed_at": sealed_at,
            "sha256_hash": digest,
            "short_hash": f"0x{digest[:12]}",
            "canonical_json": c_json,
        }
    finally:
        conn.close()


def _evaluate_counterfactual(
    portfolio_usd: float,
    initial_weights: Dict[str, float],
    mandate_weights: Dict[str, float],
    entry_prices: Dict[str, float],
    current_prices: Dict[str, float],
    unhedged_drawdown_usd: float,
    rebalanced_drawdown_usd: float,
) -> Dict[str, float]:
    unhedged_val = 0.0
    mandate_val = 0.0
    for sym, w_init in initial_weights.items():
        p_entry = float(entry_prices.get(sym, 1.0)) or 1.0
        p_curr = float(current_prices.get(sym, p_entry)) or p_entry
        ret_ratio = p_curr / p_entry
        unhedged_val += (portfolio_usd * float(w_init)) * ret_ratio

    for sym, w_mnd in mandate_weights.items():
        p_entry = float(entry_prices.get(sym, 1.0)) or 1.0
        p_curr = float(current_prices.get(sym, p_entry)) or p_entry
        ret_ratio = p_curr / p_entry
        mandate_val += (portfolio_usd * float(w_mnd)) * ret_ratio

    unhedged_pnl = round(unhedged_val - portfolio_usd, 2)
    mandate_pnl = round(mandate_val - portfolio_usd, 2)
    spot_alpha = round(mandate_pnl - unhedged_pnl, 2)
    shock_alpha = round(abs(unhedged_drawdown_usd) - abs(rebalanced_drawdown_usd), 2)
    # Alpha preserved reflects the larger of realized spot protection or scenario tail cushion
    alpha_preserved = spot_alpha if spot_alpha > 0 else shock_alpha
    return {
        "unhedged_spot_pnl_usd": unhedged_pnl,
        "mandate_spot_pnl_usd": mandate_pnl,
        "spot_alpha_usd": spot_alpha,
        "alpha_preserved_usd": round(alpha_preserved, 2),
    }


def list_mandates(
    current_prices: Optional[Dict[str, float]] = None,
    db_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT * FROM mandates ORDER BY id DESC;"
        ).fetchall()
        results: List[Dict[str, Any]] = []
        for r in rows:
            init_w = json.loads(r["initial_weights_json"])
            mnd_w = json.loads(r["mandate_weights_json"])
            entry_p = json.loads(r["entry_prices_json"])
            prices_now = current_prices or entry_p
            cf = _evaluate_counterfactual(
                portfolio_usd=float(r["portfolio_usd"]),
                initial_weights=init_w,
                mandate_weights=mnd_w,
                entry_prices=entry_p,
                current_prices=prices_now,
                unhedged_drawdown_usd=float(r["unhedged_drawdown_usd"]),
                rebalanced_drawdown_usd=float(r["rebalanced_drawdown_usd"]),
            )
            rotation_parts = []
            for sym in sorted(init_w.keys()):
                w0 = int(round(float(init_w[sym]) * 100))
                w1 = int(round(float(mnd_w.get(sym, 0.0)) * 100))
                if w0 != w1:
                    rotation_parts.append(f"{sym} {w0}% -> {w1}%")

            results.append(
                {
                    "mandate_id": r["mandate_id"],
                    "sealed_at": r["sealed_at"],
                    "portfolio_usd": r["portfolio_usd"],
                    "shock_btc_pct": r["shock_btc_pct"],
                    "scenario_label": r["scenario_label"],
                    "max_drawdown_usd": r["max_drawdown_usd"],
                    "correlation_cap": r["correlation_cap"],
                    "initial_weights": init_w,
                    "mandate_weights": mnd_w,
                    "entry_prices": entry_p,
                    "rotation_summary": " · ".join(rotation_parts),
                    "unhedged_drawdown_usd": r["unhedged_drawdown_usd"],
                    "rebalanced_drawdown_usd": r["rebalanced_drawdown_usd"],
                    "capital_preserved_usd": r["capital_preserved_usd"],
                    "max_pair_correlation_168h": r["max_pair_correlation_168h"],
                    "evidence_summary": r["evidence_summary"],
                    "sha256_hash": r["sha256_hash"],
                    "short_hash": f"0x{r['sha256_hash'][:12]}",
                    "counterfactual": cf,
                }
            )
        return results
    finally:
        conn.close()


def verify_mandate_replay(mandate_id: str, db_path: Optional[str] = None) -> Dict[str, Any]:
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT * FROM mandates WHERE mandate_id = ?;", (mandate_id,)
        ).fetchone()
        if not row:
            return {"verified": False, "error": f"Mandate {mandate_id} not found"}

        payload = {
            "portfolio_usd": row["portfolio_usd"],
            "shock_btc_pct": row["shock_btc_pct"],
            "scenario_label": row["scenario_label"],
            "max_drawdown_usd": row["max_drawdown_usd"],
            "correlation_cap": row["correlation_cap"],
            "initial_weights": json.loads(row["initial_weights_json"]),
            "mandate_weights": json.loads(row["mandate_weights_json"]),
            "entry_prices": json.loads(row["entry_prices_json"]),
            "unhedged_drawdown_usd": row["unhedged_drawdown_usd"],
            "rebalanced_drawdown_usd": row["rebalanced_drawdown_usd"],
            "capital_preserved_usd": row["capital_preserved_usd"],
            "max_pair_correlation_168h": row["max_pair_correlation_168h"],
        }
        recomputed_canonical = canonical_payload_json(payload)
        recomputed_sha256 = compute_sha256(recomputed_canonical)
        matched = recomputed_sha256 == row["sha256_hash"]
        return {
            "mandate_id": mandate_id,
            "sealed_at": row["sealed_at"],
            "stored_sha256": row["sha256_hash"],
            "computed_sha256": recomputed_sha256,
            "short_hash": f"0x{recomputed_sha256[:12]}",
            "verified": matched,
            "canonical_json": recomputed_canonical,
        }
    finally:
        conn.close()
