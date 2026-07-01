from __future__ import annotations

import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from project_env import load_project_env

from scripts.bootstrap_supabase import (  # noqa: E402
    _management_request,
    _management_session,
    _project_ref_from_supabase_url,
)

SQL = PROJECT_ROOT / "supabase" / "20260701_dedupe_event_tables.sql"


def main() -> int:
    load_project_env(PROJECT_ROOT)
    supabase_url = os.getenv("SUPABASE_URL", "").strip()
    access_token = os.getenv("SUPABASE_ACCESS_TOKEN", "").strip()
    if not supabase_url:
        print("Missing SUPABASE_URL", file=sys.stderr)
        return 1
    if not access_token:
        print("Missing SUPABASE_ACCESS_TOKEN", file=sys.stderr)
        return 1

    project_ref = _project_ref_from_supabase_url(supabase_url)
    session = _management_session()
    before = {}
    for table in ["public.events", "public.staging_events"]:
        query = f"select count(*)::int as count from {table};"
        before[table] = _management_request(session, project_ref, query, access_token)[0]["count"]

    payload = _management_request(session, project_ref, SQL.read_text(encoding="utf-8"), access_token)

    after = {}
    for table in ["public.events", "public.staging_events"]:
        query = f"select count(*)::int as count from {table};"
        after[table] = _management_request(session, project_ref, query, access_token)[0]["count"]

    print(json.dumps({"status": "success", "before": before, "after": after, "sql_file": str(SQL), "response": payload}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
