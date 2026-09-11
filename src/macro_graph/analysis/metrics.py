"""Deterministic metrics for daily snapshots."""

from __future__ import annotations

import math
import statistics

WINDOWS = (1, 5, 20, 60, 120)


def pct_change(current: float, previous: float) -> float | None:
    if previous == 0:
        return None
    return (current / previous - 1.0) * 100.0


def summarize_market(rows: list[dict], benchmark_rows: list[dict] | None = None) -> dict:
    if not rows:
        return {"status": "UNKNOWN", "reason": "no_data"}
    prices = [float(row["adj_close"] or row["close"]) for row in rows]
    latest = rows[-1]
    result: dict = {
        "status": "OK",
        "as_of_session": latest["session_date"],
        "price": prices[-1],
        "price_basis": "adjusted_close" if latest["adj_close"] else "close",
        "volume": float(latest["volume"]) if latest["volume"] is not None else None,
        "provider": latest["provider"],
        "retrieved_at": latest["retrieved_at"],
        "quality_flags": _decode_flags(latest.get("quality_flags_json")),
    }
    for window in WINDOWS:
        key = "daily_return" if window == 1 else f"{window}d_return"
        result[key] = pct_change(prices[-1], prices[-1 - window]) if len(prices) > window else None
    result["weekly_return"] = result["5d_return"]
    result["monthly_return"] = result["20d_return"]

    trailing = prices[-20:]
    if len(trailing) >= 10 and statistics.pstdev(trailing) > 0:
        result["zscore"] = (prices[-1] - statistics.mean(trailing)) / statistics.pstdev(trailing)
        result["zscore_window"] = "20_sessions_price"
    else:
        result["zscore"] = None
        result["zscore_window"] = "20_sessions_price"

    volumes = [float(row["volume"]) for row in rows[-20:] if row["volume"] is not None]
    result["volume_ratio_20d"] = (
        float(latest["volume"]) / statistics.median(volumes)
        if latest["volume"] is not None and len(volumes) >= 10 and statistics.median(volumes) > 0
        else None
    )

    if benchmark_rows:
        own = {row["session_date"]: float(row["adj_close"] or row["close"]) for row in rows}
        benchmark = {
            row["session_date"]: float(row["adj_close"] or row["close"]) for row in benchmark_rows
        }
        common = sorted(set(own) & set(benchmark))
        relative: dict[str, float | None] = {}
        for window in (1, 5, 20):
            if len(common) > window:
                end, beginning = common[-1], common[-1 - window]
                own_return = pct_change(own[end], own[beginning])
                bench_return = pct_change(benchmark[end], benchmark[beginning])
                relative[f"{window}d"] = (
                    own_return - bench_return
                    if own_return is not None and bench_return is not None
                    else None
                )
            else:
                relative[f"{window}d"] = None
        result["relative_strength_vs_nasdaq_pct_points"] = relative
        result["relative_strength"] = relative
    return _round_tree(result)


def summarize_rate(rows: list[dict]) -> dict:
    if not rows:
        return {"status": "UNKNOWN", "reason": "no_data"}
    values = [float(row["value"]) for row in rows]
    latest = rows[-1]
    result: dict = {
        "status": "OK",
        "as_of_observation": latest["period"],
        "value_pct": values[-1],
        "provider": latest["provider"],
        "retrieved_at": latest["retrieved_at"],
        "quality_flags": _decode_flags(latest.get("quality_flags_json")),
    }
    for window in WINDOWS:
        key = "daily_change_bp" if window == 1 else f"{window}d_change_bp"
        result[key] = (values[-1] - values[-1 - window]) * 100 if len(values) > window else None
    return _round_tree(result)


def aligned_correlation(left: list[dict], right: list[dict], window: int) -> dict:
    left_values = _daily_changes(left)
    right_values = _daily_changes(right)
    common = sorted(set(left_values) & set(right_values))[-window:]
    if len(common) < max(3, min(window, 5)):
        return {"value": None, "sample_size": len(common), "status": "INSUFFICIENT_DATA"}
    xs = [left_values[key] for key in common]
    ys = [right_values[key] for key in common]
    if statistics.pstdev(xs) == 0 or statistics.pstdev(ys) == 0:
        return {"value": None, "sample_size": len(common), "status": "INSUFFICIENT_VARIANCE"}
    mean_x, mean_y = statistics.mean(xs), statistics.mean(ys)
    numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    denominator = math.sqrt(sum((x - mean_x) ** 2 for x in xs) * sum((y - mean_y) ** 2 for y in ys))
    value = numerator / denominator
    return {"value": round(value, 4), "sample_size": len(common), "status": "OK"}


def _daily_changes(rows: list[dict]) -> dict[str, float]:
    date_key = "session_date" if rows and "session_date" in rows[0] else "period"
    value_key = "value" if rows and "value" in rows[0] else None
    values: list[tuple[str, float]] = []
    for row in rows:
        value = float(row[value_key]) if value_key else float(row["adj_close"] or row["close"])
        values.append((row[date_key], value))
    changes: dict[str, float] = {}
    for (current_date, current), (_, previous) in zip(values[1:], values[:-1]):
        if value_key:
            changes[current_date] = current - previous
        elif previous:
            changes[current_date] = math.log(current / previous)
    return changes


def _decode_flags(value: object) -> list[str]:
    if isinstance(value, str):
        import json

        return list(json.loads(value))
    return list(value or [])


def _round_tree(value: object) -> object:
    if isinstance(value, float):
        return round(value, 4)
    if isinstance(value, dict):
        return {key: _round_tree(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_round_tree(item) for item in value]
    return value
