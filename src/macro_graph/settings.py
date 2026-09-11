"""Configuration loading with deterministic project-relative defaults."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = yaml.safe_load(handle) or {}
    if not isinstance(value, dict):
        raise TypeError(f"Expected mapping in {path}")
    return value


@dataclass(frozen=True)
class Settings:
    project_root: Path
    database_path: Path
    output_dir: Path
    assets_path: Path
    relationships_path: Path
    report_timezone: str = "America/New_York"
    local_timezone: str = "Asia/Shanghai"
    provider_timeout_seconds: float = 20.0
    provider_max_retries: int = 3

    @classmethod
    def load(cls, project_root: Path | None = None) -> Settings:
        root = (project_root or PROJECT_ROOT).resolve()
        config_path = root / "config" / "settings.local.yaml"
        if not config_path.exists():
            config_path = root / "config" / "settings.example.yaml"
        raw = load_yaml(config_path)
        database_url = str(raw.get("database_url", "sqlite:///data/macro_graph.sqlite3"))
        prefix = "sqlite:///"
        if not database_url.startswith(prefix):
            raise ValueError("MVP supports only sqlite:/// database URLs")
        db_value = Path(database_url[len(prefix) :])
        output_value = Path(str(raw.get("output_dir", "output")))
        return cls(
            project_root=root,
            database_path=db_value if db_value.is_absolute() else root / db_value,
            output_dir=output_value if output_value.is_absolute() else root / output_value,
            assets_path=root / "config" / "assets.yaml",
            relationships_path=root / "config" / "relationships.yaml",
            report_timezone=str(raw.get("report_timezone", "America/New_York")),
            local_timezone=str(raw.get("local_timezone", "Asia/Shanghai")),
            provider_timeout_seconds=float(raw.get("provider_timeout_seconds", 20)),
            provider_max_retries=int(raw.get("provider_max_retries", 3)),
        )
