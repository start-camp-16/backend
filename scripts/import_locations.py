import argparse
import logging
from pathlib import Path

from app.db import SessionLocal
from app.locations.importer import ImportValidationError, import_manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import TourAPI location JSON into SQLite")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--verify-total", type=int)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        with SessionLocal() as session:
            report = import_manifest(session, args.manifest)
    except ImportValidationError as exc:
        logging.error("Location import validation failed: %s", exc)
        return 1

    if args.verify_total is not None and report.total != args.verify_total:
        logging.error("Imported total %d does not match %d", report.total, args.verify_total)
        return 1

    for category, count in report.category_counts.items():
        print(f"category={category} count={count}")
    print(f"inserted={report.inserted} updated={report.updated} total={report.total} verified=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
