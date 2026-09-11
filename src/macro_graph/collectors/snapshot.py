"""Assemble the stable JSON snapshot contract from normalized storage."""

from __future__ import annotations

from datetime import date, datetime

from macro_graph.analysis import aligned_correlation, classify, summarize_market, summarize_rate
from macro_graph.storage import Database

RATE_IDS = (
    "FED_FUNDS_EFFECTIVE",
    "US02Y",
    "US10Y",
    "US_REAL_YIELD_10Y",
    "US_BREAKEVEN_10Y",
)
MARKET_IDS = (
    "DXY",
    "GOLD",
    "BRENT",
    "SP500",
    "NASDAQ",
    "SOXX",
    "NVDA",
    "AVGO",
    "MU",
    "SNDK",
    "INTC",
    "LITE",
    "GLW",
)
COMPANY_IDS = ("NVDA", "AVGO", "MU", "SNDK", "INTC", "LITE", "GLW")


def build_snapshot(
    database: Database,
    run_date: date,
    as_of: datetime,
    config_hash: str,
    provider_status: dict,
) -> dict:
    macro_history = {key: database.macro_history(key, run_date) for key in RATE_IDS}
    market_history = {key: database.market_history(key, run_date) for key in MARKET_IDS}
    nasdaq = market_history["NASDAQ"]

    rates = {key: summarize_rate(value) for key, value in macro_history.items()}
    market = {
        key: summarize_market(value, nasdaq if key in ("SOXX",) + COMPANY_IDS else None)
        for key, value in market_history.items()
    }
    correlations = _correlations(macro_history, market_history)
    missing = [
        key
        for key in RATE_IDS + MARKET_IDS
        if (rates.get(key) or market.get(key, {})).get("status") != "OK"
    ]
    stale = _stale_items(run_date, rates, market)
    status = "COMPLETE" if not missing else "DEGRADED"
    snapshot = {
        "schema_version": "1.0",
        "run": {
            "run_date": run_date.isoformat(),
            "as_of": as_of.isoformat(),
            "status": status,
            "config_hash": config_hash,
            "provider_status": provider_status,
        },
        "macro": {"fed_rate": rates["FED_FUNDS_EFFECTIVE"]},
        "rates": {key: rates[key] for key in RATE_IDS if key != "FED_FUNDS_EFFECTIVE"},
        "fx": {"DXY": market["DXY"]},
        "commodities": {"GOLD": market["GOLD"], "BRENT": market["BRENT"]},
        "equity": {key: market[key] for key in ("SP500", "NASDAQ", "SOXX")},
        "companies": {key: market[key] for key in COMPANY_IDS},
        "correlations": correlations,
        "regimes": [],
        "quality": {
            "warnings": [
                "FRED CSV MVP uses latest available vintage; true historical vintage replay is deferred.",
                "yfinance is an unofficial convenience feed without an SLA.",
                "DXY, gold, and Brent may be provider futures/index proxies; see assets.yaml.",
                "Correlation is validation evidence, not proof of causation.",
            ],
            "missing_series": missing,
            "stale_series": stale,
        },
    }
    snapshot["regimes"] = classify(snapshot)
    return snapshot


def _correlations(macro: dict, market: dict) -> dict:
    pairs = {
        "GOLD_vs_REAL_YIELD": (market["GOLD"], macro["US_REAL_YIELD_10Y"]),
        "GOLD_vs_DXY": (market["GOLD"], market["DXY"]),
        "NASDAQ_vs_US10Y": (market["NASDAQ"], macro["US10Y"]),
        "SOXX_vs_US10Y": (market["SOXX"], macro["US10Y"]),
        "BRENT_vs_BREAKEVEN": (market["BRENT"], macro["US_BREAKEVEN_10Y"]),
        "LITE_vs_SOXX": (market["LITE"], market["SOXX"]),
    }
    return {
        name: {
            f"{window}d": aligned_correlation(left, right, window) for window in (5, 20, 60, 120)
        }
        for name, (left, right) in pairs.items()
    }


def _stale_items(run_date: date, rates: dict, market: dict) -> list[str]:
    stale: list[str] = []
    for key, item in {**rates, **market}.items():
        observed = item.get("as_of_session") or item.get("as_of_observation")
        if observed and (run_date - date.fromisoformat(observed)).days > 4:
            stale.append(key)
    return stale
