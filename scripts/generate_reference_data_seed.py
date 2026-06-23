from __future__ import annotations

import argparse
import json
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "supabase" / "seed_reference_data.sql"


def _ensure_project_root_on_path() -> None:
    root = str(PROJECT_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)


def _sql_text(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _sql_jsonb(value: Any) -> str:
    return "'{}'::jsonb".format(json.dumps(value, ensure_ascii=False).replace("'", "''"))


def _render_values(rows: list[list[str]]) -> str:
    return ",\n".join("  (" + ", ".join(row) + ")" for row in rows)


def _unique_by_key(items: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    unique: OrderedDict[str, dict[str, Any]] = OrderedDict()
    for item in items:
        unique[str(item[key])] = item
    return list(unique.values())


def build_seed_sql() -> str:
    _ensure_project_root_on_path()

    from collector.config.tracking_universe import (
        INSTITUTION_WATCH_STOCKS,
        MACRO_TOPICS,
        STOCK_INDUSTRY_RELATIONS,
        TRACKED_STOCKS,
        TRACKING_INDUSTRIES,
    )

    all_stocks = _unique_by_key([*TRACKED_STOCKS, *INSTITUTION_WATCH_STOCKS], "stock_code")

    industries_rows = []
    for industry in TRACKING_INDUSTRIES:
        industries_rows.append(
            [
                _sql_text(industry["industry_id"]),
                _sql_text(industry["industry_name"]),
                "true" if industry.get("enabled", True) else "false",
                _sql_jsonb(industry.get("keywords_zh", [])),
                _sql_jsonb(industry.get("keywords_en", [])),
            ]
        )

    stocks_rows = []
    for stock in all_stocks:
        stocks_rows.append(
            [
                _sql_text(stock["stock_code"]),
                _sql_text(stock["stock_name"]),
                "true" if stock.get("enabled", True) else "false",
                _sql_jsonb([stock["stock_name"], stock["stock_code"]]),
                _sql_jsonb([]),
            ]
        )

    relation_rows = []
    for relation in STOCK_INDUSTRY_RELATIONS:
        relation_rows.append(
            [
                _sql_text(relation["stock_code"]),
                _sql_text(relation["industry_name"]),
            ]
        )

    macro_rows = []
    for topic in MACRO_TOPICS:
        macro_rows.append(
            [
                _sql_text(topic["topic_id"]),
                _sql_text(topic["topic_name"]),
                "true" if topic.get("enabled", True) else "false",
                _sql_jsonb(topic.get("keywords_zh", [])),
                _sql_jsonb(topic.get("keywords_en", [])),
            ]
        )

    institution_rows = []
    for item in INSTITUTION_WATCH_STOCKS:
        institution_rows.append(
            [
                _sql_text(item["stock_code"]),
                _sql_text(item["stock_name"]),
                "true" if item.get("enabled", True) else "false",
                _sql_text("institution_watch"),
            ]
        )

    sql = f"""-- Production reference data seed for Investment Research Collector
--
-- Generated from collector/config/tracking_universe.py.
-- Re-run scripts/generate_reference_data_seed.py whenever the tracking universe changes.
-- This file seeds reference entities only. It does not create events.

-- SECTION: industries
insert into industries (
  industry_id,
  industry_name,
  enabled,
  keywords_zh,
  keywords_en
) values
{_render_values(industries_rows)}
on conflict (industry_id) do update set
  industry_name = excluded.industry_name,
  enabled = excluded.enabled,
  keywords_zh = excluded.keywords_zh,
  keywords_en = excluded.keywords_en,
  updated_at = now();

-- SECTION: stocks
insert into stocks (
  stock_code,
  stock_name,
  enabled,
  keywords_zh,
  keywords_en
) values
{_render_values(stocks_rows)}
on conflict (stock_code) do update set
  stock_name = excluded.stock_name,
  enabled = excluded.enabled,
  keywords_zh = excluded.keywords_zh,
  keywords_en = excluded.keywords_en,
  updated_at = now();

-- SECTION: stock_industries
insert into stock_industries (
  stock_code,
  industry_name
) values
{_render_values(relation_rows)}
on conflict (stock_code, industry_name) do update set
  stock_code = excluded.stock_code,
  industry_name = excluded.industry_name;

-- SECTION: macro_topics
insert into macro_topics (
  topic_id,
  topic_name,
  enabled,
  keywords_zh,
  keywords_en
) values
{_render_values(macro_rows)}
on conflict (topic_id) do update set
  topic_name = excluded.topic_name,
  enabled = excluded.enabled,
  keywords_zh = excluded.keywords_zh,
  keywords_en = excluded.keywords_en,
  updated_at = now();

-- SECTION: institution_watch_stocks
insert into institution_watch_stocks (
  stock_code,
  stock_name,
  enabled,
  watch_reason
) values
{_render_values(institution_rows)}
on conflict (stock_code) do update set
  stock_name = excluded.stock_name,
  enabled = excluded.enabled,
  watch_reason = excluded.watch_reason,
  updated_at = now();
"""
    return sql


def write_seed_sql(output_path: Path = DEFAULT_OUTPUT_PATH) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_seed_sql(), encoding="utf-8")
    return output_path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate the production reference data seed SQL.")
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="Output path for the seed SQL file.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    output_path = write_seed_sql(args.output)
    print(f"Wrote reference data seed to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
