"""Transparent, multi-label regime rules."""

from __future__ import annotations


def classify(snapshot: dict) -> list[dict]:
    rates = snapshot["rates"]
    fx = snapshot["fx"].get("DXY", {})
    equity = snapshot["equity"]
    real_yield = rates.get("US_REAL_YIELD_10Y", {}).get("daily_change_bp")
    dxy_return = fx.get("daily_return")
    nasdaq_return = equity.get("NASDAQ", {}).get("daily_return")
    soxx_relative = (
        equity.get("SOXX", {}).get("relative_strength_vs_nasdaq_pct_points", {}).get("1d")
    )
    results: list[dict] = []

    hawkish_inputs = [real_yield, dxy_return, nasdaq_return]
    if all(value is not None for value in hawkish_inputs):
        matches = [real_yield > 3, dxy_return > 0.2, nasdaq_return < -0.3]
        if sum(matches) >= 2:
            results.append(
                {
                    "regime": "HAWKISH_TIGHTENING",
                    "score": round(sum(matches) / 3, 2),
                    "confidence": "medium" if sum(matches) == 2 else "high",
                    "evidence": {
                        "real_yield_change_bp": real_yield,
                        "dxy_return_pct": dxy_return,
                        "nasdaq_return_pct": nasdaq_return,
                    },
                    "rule_id": "regime.hawkish.v1",
                }
            )

    if soxx_relative is not None and soxx_relative > 0.75:
        results.append(
            {
                "regime": "AI_HARDWARE_RELATIVE_STRENGTH",
                "score": min(1.0, round(soxx_relative / 2.0, 2)),
                "confidence": "low",
                "evidence": {"soxx_vs_nasdaq_1d_pct_points": soxx_relative},
                "counterevidence": "MVP has no software ETF, breadth, or fund-flow confirmation.",
                "rule_id": "regime.hardware_relative.v1",
            }
        )

    if not results:
        results.append(
            {
                "regime": "UNKNOWN",
                "score": 0.0,
                "confidence": "insufficient",
                "evidence": {},
                "reason": "No rule met its threshold or required inputs were unavailable.",
                "rule_id": "regime.unknown.v1",
            }
        )
    return results
