from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

import requests
from requests.exceptions import SSLError

from collector.utils.ssl_utils import allow_insecure_ssl, resolve_ssl_verify_setting, supabase_ssl_error_message


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from project_env import load_project_env

load_project_env(PROJECT_ROOT)

SQL_FILES = [
    PROJECT_ROOT / "supabase" / "production_schema.sql",
    PROJECT_ROOT / "supabase" / "staging_schema.sql",
    PROJECT_ROOT / "supabase" / "seed_reference_data.sql",
    PROJECT_ROOT / "supabase" / "20260622_align_summarizer_mode.sql",
    PROJECT_ROOT / "supabase" / "20260701_allow_agnes_llm_provider.sql",
    PROJECT_ROOT / "supabase" / "20260701_allow_firecrawl_search_provider.sql",
    PROJECT_ROOT / "supabase" / "20260701_dedupe_event_tables.sql",
]

VIEW_NAMES = [
    "view_dashboard_events",
    "view_industry_cards",
    "view_stock_cards",
    "view_stock_detail_events",
    "view_macro_events",
    "view_institution_watch_events",
    "view_recent_reports",
    "view_unread_counts",
]


def _project_ref_from_supabase_url(url: str) -> str:
    match = re.search(r"https?://([^.]+)\.supabase\.co", url)
    if not match:
        raise ValueError("Could not determine Supabase project ref from SUPABASE_URL.")
    return match.group(1)


def _management_session() -> requests.Session:
    session = requests.Session()
    session.verify = resolve_ssl_verify_setting()
    return session


def _management_request(session: requests.Session, project_ref: str, query: str, token: str) -> list[dict[str, Any]]:
    response = _request_with_ssl_policy(
        session,
        "POST",
        f"https://api.supabase.com/v1/projects/{project_ref}/database/query",
        token,
        json={"query": query},
    )
    if not response.ok:
        raise RuntimeError(f"Supabase query failed: {response.status_code} {response.text}")
    payload = response.json()
    if not isinstance(payload, list):
        raise RuntimeError(f"Unexpected Supabase response: {json.dumps(payload, ensure_ascii=False)}")
    return payload


def _load_sql(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _print_step(message: str) -> None:
    print(message, flush=True)


def _request_with_ssl_policy(
    session: requests.Session,
    method: str,
    url: str,
    token: str,
    *,
    json: dict[str, Any],
) -> requests.Response:
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    try:
        return session.request(method, url, headers=headers, json=json, timeout=60)
    except SSLError as exc:
        if not _allow_insecure_ssl():
            raise RuntimeError(supabase_ssl_error_message("Supabase management API")) from exc
        print(
            "WARNING: insecure SSL fallback enabled by ALLOW_INSECURE_SSL=true",
            flush=True,
        )
        session.verify = False
        try:
            return session.request(method, url, headers=headers, json=json, timeout=60)
        except SSLError as retry_exc:
            raise RuntimeError(supabase_ssl_error_message("Supabase management API")) from retry_exc


def _allow_insecure_ssl() -> bool:
    return allow_insecure_ssl()


def bootstrap_supabase(*, verify: bool = True) -> dict[str, Any]:
    supabase_url = os.getenv("SUPABASE_URL", "").strip()
    access_token = os.getenv("SUPABASE_ACCESS_TOKEN", "").strip()
    if not supabase_url:
        raise RuntimeError("Missing SUPABASE_URL in .env.")
    if not access_token:
        raise RuntimeError("Missing SUPABASE_ACCESS_TOKEN in .env.")

    project_ref = _project_ref_from_supabase_url(supabase_url)
    session = _management_session()
    if verify:
        session.verify = True

    results: list[dict[str, Any]] = []
    drop_views_sql = "\n".join(f"drop view if exists public.{name} cascade;" for name in VIEW_NAMES)
    _print_step("Resetting existing views ...")
    _management_request(session, project_ref, drop_views_sql, access_token)
    _print_step("Reset existing views")

    for sql_file in SQL_FILES:
        if not sql_file.exists():
            raise FileNotFoundError(f"Missing SQL file: {sql_file}")
        _print_step(f"Applying {sql_file.name} ...")
        payload = _management_request(session, project_ref, _load_sql(sql_file), access_token)
        results.append({"file": str(sql_file), "response": payload})
        _print_step(f"Applied {sql_file.name}")

    checks = {
        "industries": "select count(*)::int as count from public.industries;",
        "stocks": "select count(*)::int as count from public.stocks;",
        "stock_industries": "select count(*)::int as count from public.stock_industries;",
        "macro_topics": "select count(*)::int as count from public.macro_topics;",
        "institution_watch_stocks": "select count(*)::int as count from public.institution_watch_stocks;",
        "staging_events": "select to_regclass('public.staging_events') is not null as exists;",
        "staging_daily_digests": "select to_regclass('public.staging_daily_digests') is not null as exists;",
        "staging_reports": "select to_regclass('public.staging_reports') is not null as exists;",
        "staging_crawl_runs": "select to_regclass('public.staging_crawl_runs') is not null as exists;",
        "staging_rejected_sources": "select to_regclass('public.staging_rejected_sources') is not null as exists;",
        "production_views": (
            "select "
            "to_regclass('public.view_dashboard_events') is not null as view_dashboard_events, "
            "to_regclass('public.view_industry_cards') is not null as view_industry_cards, "
            "to_regclass('public.view_stock_cards') is not null as view_stock_cards, "
            "to_regclass('public.view_stock_detail_events') is not null as view_stock_detail_events, "
            "to_regclass('public.view_macro_events') is not null as view_macro_events, "
            "to_regclass('public.view_institution_watch_events') is not null as view_institution_watch_events, "
            "to_regclass('public.view_recent_reports') is not null as view_recent_reports, "
            "to_regclass('public.view_unread_counts') is not null as view_unread_counts;"
        ),
    }

    verification: dict[str, Any] = {}
    for name, query in checks.items():
        payload = _management_request(session, project_ref, query, access_token)
        verification[name] = payload

    return {
        "project_ref": project_ref,
        "applied_files": [str(path) for path in SQL_FILES],
        "verification": verification,
        "results": results,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bootstrap Supabase schema, views, and reference data.")
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Use strict SSL verification for Management API calls.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        result = bootstrap_supabase(verify=args.verify)
    except Exception as exc:  # pragma: no cover - manual bootstrap helper
        print(json.dumps({"status": "failed", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1

    print(
        json.dumps(
            {
                "status": "success",
                "project_ref": result["project_ref"],
                "applied_files": [Path(path).name for path in result["applied_files"]],
                "verification": result["verification"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
