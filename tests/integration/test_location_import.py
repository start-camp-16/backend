import json
from pathlib import Path

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.locations.importer import ImportValidationError, import_manifest
from app.models import Location


def write_source(
    directory: Path,
    *,
    filename: str = "12.json",
    category: str = "관광지",
    content_type_id: str | int = "12",
    items: list[dict[str, str]] | None = None,
) -> Path:
    source_items = items or [
        {
            "contentid": "100",
            "title": "첫 장소",
            "addr1": "서울특별시 강남구 테헤란로",
            "addr2": "1층",
            "mapx": "127.01",
            "mapy": "37.50",
            "firstimage": "",
            "firstimage2": "https://example.com/thumb.jpg",
            "tel": "02-000-0000",
        },
        {
            "contentid": "101",
            "title": "둘째 장소",
            "addr1": "주소 없음",
            "addr2": "",
            "mapx": "0",
            "mapy": "0",
            "firstimage": "",
            "firstimage2": "",
            "tel": "",
        },
    ]
    path = directory / filename
    path.write_text(
        json.dumps(
            {
                "region": "서울",
                "contentType": category,
                "contentTypeId": content_type_id,
                "total": len(source_items),
                "items": source_items,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return path


def write_manifest(directory: Path, sources: list[dict[str, object]], total: int) -> Path:
    path = directory / "manifest.json"
    path.write_text(
        json.dumps({"expectedTotal": total, "sources": sources}, ensure_ascii=False),
        encoding="utf-8",
    )
    return path


def source_entry(path: Path, *, count: int = 2) -> dict[str, object]:
    return {
        "category": "관광지",
        "contentTypeId": "12",
        "path": path.name,
        "expectedCount": count,
    }


def test_import_assigns_source_order_and_normalizes_values(db_session: Session, tmp_path: Path):
    source = write_source(tmp_path)
    manifest = write_manifest(tmp_path, [source_entry(source)], total=2)

    report = import_manifest(db_session, manifest)

    locations = list(db_session.scalars(select(Location).order_by(Location.source_order)))
    assert report.inserted == 2
    assert report.updated == 0
    assert report.total == 2
    assert [location.source_order for location in locations] == [1, 2]
    assert locations[0].district == "강남구"
    assert locations[0].address2 == "1층"
    assert locations[0].image_url is None
    assert locations[1].district == "기타"
    assert locations[1].longitude == 0.0
    assert locations[1].latitude == 0.0


def test_numeric_source_content_type_id_matches_string_manifest(
    db_session: Session,
    tmp_path: Path,
):
    source = write_source(tmp_path, content_type_id=12)
    manifest = write_manifest(tmp_path, [source_entry(source)], total=2)

    report = import_manifest(db_session, manifest)

    assert report.total == 2


def test_reimport_updates_source_fields_without_duplicates(db_session: Session, tmp_path: Path):
    source = write_source(tmp_path)
    manifest = write_manifest(tmp_path, [source_entry(source)], total=2)
    first = import_manifest(db_session, manifest)
    payload = json.loads(source.read_text(encoding="utf-8"))
    payload["items"][0]["title"] = "변경된 장소"
    source.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    second = import_manifest(db_session, manifest)

    assert first.inserted == 2
    assert second.updated == 2
    assert db_session.scalar(select(func.count(Location.id))) == 2
    assert (
        db_session.scalar(select(Location.title).where(Location.content_id == "100"))
        == "변경된 장소"
    )


def test_duplicate_content_id_across_sources_rolls_back(db_session: Session, tmp_path: Path):
    first = write_source(tmp_path, filename="first.json")
    second = write_source(tmp_path, filename="second.json")
    manifest = write_manifest(
        tmp_path,
        [source_entry(first), source_entry(second)],
        total=4,
    )

    with pytest.raises(ImportValidationError, match="duplicate contentid"):
        import_manifest(db_session, manifest)

    assert db_session.scalar(select(func.count(Location.id))) == 0


def test_count_mismatch_rolls_back(db_session: Session, tmp_path: Path):
    source = write_source(tmp_path)
    manifest = write_manifest(tmp_path, [source_entry(source, count=3)], total=3)

    with pytest.raises(ImportValidationError, match="expected 3 items, found 2"):
        import_manifest(db_session, manifest)

    assert db_session.scalar(select(func.count(Location.id))) == 0
