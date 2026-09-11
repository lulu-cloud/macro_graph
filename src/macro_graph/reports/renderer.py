"""Strict evidence-labelled Markdown daily report renderer."""

from __future__ import annotations

from pathlib import Path


def render_report(snapshot: dict, output_path: Path) -> None:
    sections: list[str] = ["# Global Market Daily / 全球市场日报", ""]
    sections += _macro(snapshot)
    sections += _rates(snapshot)
    sections += _single_market("3 美元", snapshot["fx"], ("DXY",))
    sections += _single_market("4 商品", snapshot["commodities"], ("GOLD", "BRENT"))
    sections += _single_market("5 美股", snapshot["equity"], ("SP500", "NASDAQ", "SOXX"))
    sections += _single_market("6 AI Hardware", snapshot["companies"], tuple(snapshot["companies"]))
    sections += _relative_strength(snapshot)
    sections += _capital_rotation(snapshot)
    sections += [
        "## 9 重要事件",
        "",
        "- [UNKNOWN] 经济日历属于下一阶段，当前无法提供未来七天事件清单。",
        "",
    ]
    sections += _causal_map(snapshot)
    sections += ["## 数据质量", ""]
    sections += [f"- [FACT] {warning}" for warning in snapshot["quality"]["warnings"]]
    if snapshot["quality"]["missing_series"]:
        sections.append("- [UNKNOWN] 缺失序列：" + ", ".join(snapshot["quality"]["missing_series"]))
    if snapshot["quality"]["stale_series"]:
        sections.append(
            "- [OBSERVATION] 过期序列：" + ", ".join(snapshot["quality"]["stale_series"])
        )
    sections += ["", f"_As of {snapshot['run']['as_of']}; status {snapshot['run']['status']}._", ""]
    _atomic_text(output_path, "\n".join(sections))


def _macro(snapshot: dict) -> list[str]:
    fed = snapshot["macro"]["fed_rate"]
    return ["## 1 宏观状态", "", _rate_line("Effective Fed Funds", fed), ""]


def _rates(snapshot: dict) -> list[str]:
    lines = ["## 2 利率", ""]
    for key in ("US02Y", "US10Y", "US_REAL_YIELD_10Y", "US_BREAKEVEN_10Y"):
        lines.append(_rate_line(key, snapshot["rates"][key]))
    lines.append("- [HYPOTHESIS] 在接入事件和新闻证据前，不能为当日收益率变化指定单一原因。")
    lines.append("")
    return lines


def _rate_line(label: str, item: dict) -> str:
    if item.get("status") != "OK":
        return f"- [UNKNOWN] {label}：数据不可用。"
    change = _fmt(item.get("daily_change_bp"), "bp")
    return (
        f"- [FACT] {label}：{item['value_pct']:.3f}%（{change}）；"
        f"观测日期 {item['as_of_observation']}，来源 {item['provider']}。"
    )


def _single_market(title: str, container: dict, keys: tuple[str, ...]) -> list[str]:
    lines = [f"## {title}", ""]
    for key in keys:
        item = container[key]
        if item.get("status") != "OK":
            lines.append(f"- [UNKNOWN] {key}：数据不可用。")
            continue
        lines.append(
            f"- [FACT] {key}：{item['price']:.3f}，1D {_fmt(item.get('daily_return'), '%')}，"
            f"20D {_fmt(item.get('20d_return'), '%')}；交易日 {item['as_of_session']}。"
        )
    lines.append("")
    return lines


def _relative_strength(snapshot: dict) -> list[str]:
    available: list[tuple[str, float]] = []
    for key, item in {**snapshot["equity"], **snapshot["companies"]}.items():
        relative = item.get("relative_strength_vs_nasdaq_pct_points", {}).get("5d")
        if relative is not None:
            available.append((key, relative))
    available.sort(key=lambda item: item[1], reverse=True)
    lines = ["## 7 相对强弱", ""]
    if not available:
        lines.append("- [UNKNOWN] 对齐后的历史数据不足，无法计算相对强弱排名。")
    else:
        strongest = ", ".join(f"{key} {value:+.2f}pp" for key, value in available[:3])
        weakest = ", ".join(f"{key} {value:+.2f}pp" for key, value in available[-3:])
        lines.append(f"- [OBSERVATION] 近 5 个交易日相对 Nasdaq 最强：{strongest}。")
        lines.append(f"- [OBSERVATION] 近 5 个交易日相对 Nasdaq 最弱：{weakest}。")
    lines.append("")
    return lines


def _capital_rotation(snapshot: dict) -> list[str]:
    regimes = snapshot["regimes"]
    lines = ["## 8 资金轮动", ""]
    for regime in regimes:
        if regime["regime"] == "AI_HARDWARE_RELATIVE_STRENGTH":
            lines.append(
                "- [HYPOTHESIS] SOXX 相对强势与硬件轮动假设一致，"
                "但缺少软件板块广度和真实资金流数据确认。"
            )
    lines.append("- [UNKNOWN] 无法确认资金流向，目前只能观察价格相对强弱和成交量代理指标。")
    lines.append("")
    return lines


def _causal_map(snapshot: dict) -> list[str]:
    lines = ["## 10 今日因果路径", ""]
    for regime in snapshot["regimes"]:
        if regime["regime"] == "HAWKISH_TIGHTENING":
            lines += [
                "- [INFERENCE, medium confidence] 已观察到的价格路径与下列机制一致：",
                "",
                "  `Real Yield ↑ -> DXY ↑ -> long-duration equity valuation pressure`",
                "",
                "  这只是路径一致性检验，不能证明这些变化由某一个宏观事件导致。",
            ]
        elif regime["regime"] == "AI_HARDWARE_RELATIVE_STRENGTH":
            lines.append(
                "- [HYPOTHESIS, low confidence] `AI 需求预期 -> 半导体相对强势`；"
                "当前尚未接入基本面事件证据。"
            )
    if snapshot["regimes"][0]["regime"] == "UNKNOWN":
        lines.append("- [UNKNOWN] 当前没有因果或 regime 路径获得足够证据支持。")
    lines.append("")
    return lines


def _fmt(value: float | None, suffix: str) -> str:
    return "UNKNOWN" if value is None else f"{value:+.2f}{suffix}"


def _atomic_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(content, encoding="utf-8")
    temporary.replace(path)
