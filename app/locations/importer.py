import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.models import LOCATION_CATEGORIES, Location

logger = logging.getLogger(__name__)

DISTRICT_PATTERN = re.compile(r"(?:서울특별시|서울)\s+([가-힣]+구)(?:\s|$)")


class ImportValidationError(ValueError):
    pass


@dataclass(frozen=True)
class SourceSpec:
    category: str
    content_type_id: str
    path: Path
    expected_count: int


@dataclass(frozen=True)
class Manifest:
    expected_total: int
    sources: tuple[SourceSpec, ...]


@dataclass(frozen=True)
class ImportReport:
    inserted: int
    updated: int
    total: int
    category_counts: dict[str, int]


def parse_float(value: object) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def extract_district(address: str | None) -> str:
    match = DISTRICT_PATTERN.search(address or "")
    return match.group(1) if match else "기타"


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ImportValidationError(f"cannot read JSON source: {path}") from exc
    if not isinstance(payload, dict):
        raise ImportValidationError(f"JSON root must be an object: {path}")
    return payload


def _required_string(item: dict[str, Any], field: str, source_path: Path) -> str:
    value = item.get(field)
    if not isinstance(value, str) or not value:
        raise ImportValidationError(f"{source_path}: field {field} must be a non-empty string")
    return value


def _optional_string(value: object) -> str | None:
    return value if isinstance(value, str) and value else None


def load_manifest(manifest_path: str | Path) -> Manifest:
    path = Path(manifest_path).resolve()
    payload = _read_json(path)
    expected_total = payload.get("expectedTotal")
    raw_sources = payload.get("sources")
    if not isinstance(expected_total, int) or expected_total < 0:
        raise ImportValidationError("manifest expectedTotal must be a non-negative integer")
    if not isinstance(raw_sources, list) or not raw_sources:
        raise ImportValidationError("manifest sources must be a non-empty array")

    sources: list[SourceSpec] = []
    for raw_source in raw_sources:
        if not isinstance(raw_source, dict):
            raise ImportValidationError("manifest source entries must be objects")
        category = raw_source.get("category")
        content_type_id = raw_source.get("contentTypeId")
        source_path = raw_source.get("path")
        expected_count = raw_source.get("expectedCount")
        if category not in LOCATION_CATEGORIES:
            raise ImportValidationError(f"unsupported location category: {category}")
        if not isinstance(content_type_id, str) or not content_type_id:
            raise ImportValidationError("manifest contentTypeId must be a non-empty string")
        if not isinstance(source_path, str) or not source_path:
            raise ImportValidationError("manifest path must be a non-empty string")
        if not isinstance(expected_count, int) or expected_count < 0:
            raise ImportValidationError("manifest expectedCount must be a non-negative integer")
        resolved_path = Path(source_path)
        if not resolved_path.is_absolute():
            resolved_path = path.parent / resolved_path
        sources.append(
            SourceSpec(
                category=category,
                content_type_id=content_type_id,
                path=resolved_path.resolve(),
                expected_count=expected_count,
            )
        )

    if sum(source.expected_count for source in sources) != expected_total:
        raise ImportValidationError("manifest category counts do not equal expectedTotal")
    return Manifest(expected_total=expected_total, sources=tuple(sources))


def _load_records(manifest: Manifest) -> tuple[list[dict[str, Any]], dict[str, int]]:
    records: list[dict[str, Any]] = []
    category_counts: dict[str, int] = {}
    content_ids: set[str] = set()

    for source in manifest.sources:
        payload = _read_json(source.path)
        items = payload.get("items")
        if payload.get("contentType") != source.category:
            raise ImportValidationError(f"{source.path}: contentType does not match manifest")
        if str(payload.get("contentTypeId")) != source.content_type_id:
            raise ImportValidationError(f"{source.path}: contentTypeId does not match manifest")
        if not isinstance(items, list):
            raise ImportValidationError(f"{source.path}: items must be an array")
        if payload.get("total") != len(items):
            raise ImportValidationError(f"{source.path}: total does not match items length")
        if len(items) != source.expected_count:
            raise ImportValidationError(
                f"{source.path}: expected {source.expected_count} items, found {len(items)}"
            )

        category_counts[source.category] = len(items)
        for source_order, raw_item in enumerate(items, start=1):
            if not isinstance(raw_item, dict):
                raise ImportValidationError(f"{source.path}: item {source_order} must be an object")
            content_id = _required_string(raw_item, "contentid", source.path)
            if content_id in content_ids:
                raise ImportValidationError(f"duplicate contentid: {content_id}")
            content_ids.add(content_id)
            address1 = _optional_string(raw_item.get("addr1"))
            records.append(
                {
                    "content_id": content_id,
                    "category": source.category,
                    "title": _required_string(raw_item, "title", source.path),
                    "address1": address1,
                    "address2": _optional_string(raw_item.get("addr2")),
                    "district": extract_district(address1),
                    "longitude": parse_float(raw_item.get("mapx")),
                    "latitude": parse_float(raw_item.get("mapy")),
                    "image_url": _optional_string(raw_item.get("firstimage")),
                    "thumbnail_url": _optional_string(raw_item.get("firstimage2")),
                    "phone": _optional_string(raw_item.get("tel")),
                    "source_order": source_order,
                }
            )

    if len(records) != manifest.expected_total:
        raise ImportValidationError(
            f"expected {manifest.expected_total} total items, found {len(records)}"
        )
    return records, category_counts


def import_manifest(session: Session, manifest_path: str | Path) -> ImportReport:
    manifest = load_manifest(manifest_path)
    records, category_counts = _load_records(manifest)

    with session.begin():
        existing_ids = set(session.scalars(select(Location.content_id)))
        for record in records:
            statement = sqlite_insert(Location).values(**record)
            update_fields = {
                key: getattr(statement.excluded, key) for key in record if key != "content_id"
            }
            session.execute(
                statement.on_conflict_do_update(
                    index_elements=[Location.content_id],
                    set_=update_fields,
                )
            )

    inserted = sum(record["content_id"] not in existing_ids for record in records)
    report = ImportReport(
        inserted=inserted,
        updated=len(records) - inserted,
        total=len(records),
        category_counts=category_counts,
    )
    logger.info(
        "Location import completed",
        extra={
            "inserted": report.inserted,
            "updated": report.updated,
            "total": report.total,
            "category_counts": report.category_counts,
        },
    )
    return report
