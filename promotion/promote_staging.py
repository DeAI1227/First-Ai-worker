from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from promotion.packet_promoter import promote_packets


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Promotion for Investment Research Collector")
    parser.add_argument("--input", required=True)
    parser.add_argument("--packet-type", default="all", choices=["event", "daily_digest", "report", "crawl_run", "rejected_source", "all"])
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = promote_packets(input_path=args.input, packet_type_filter=args.packet_type, dry_run=args.dry_run)
    print("Promotion Dry Run Summary" if args.dry_run else "Promotion Write Summary")
    print(f"Batch Report: {report.get('batch_report_path', '')}")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report.get("status") == "failed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
