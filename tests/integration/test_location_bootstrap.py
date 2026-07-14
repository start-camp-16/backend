import json
from pathlib import Path

import pytest
from sqlalchemy import func, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from starlette.testclient import TestClient

from app.locations.importer import ImportValidationError
from app.main import create_app
from app.models import Location


def write_manifest(directory: Path) -> Path:
    source_path = directory / "12.json"
    source_path.write_text(
        json.dumps(
            {
                "contentType": "관광지",
                "contentTypeId": "12",
                "total": 1,
                "items": [
                    {
                        "contentid": "bootstrap-100",
                        "title": "초기 적재 장소",
                        "addr1": "서울특별시 강남구 테헤란로",
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    manifest_path = directory / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "expectedTotal": 1,
                "sources": [
                    {
                        "category": "관광지",
                        "contentTypeId": "12",
                        "path": source_path.name,
                        "expectedCount": 1,
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return manifest_path


def test_startup_imports_locations_when_database_is_empty(
    db_engine: Engine,
    tmp_path: Path,
) -> None:
    session_factory = sessionmaker(bind=db_engine, expire_on_commit=False)
    app = create_app(
        bootstrap_locations=True,
        session_factory=session_factory,
        location_manifest=write_manifest(tmp_path),
    )

    with TestClient(app):
        pass

    with session_factory() as session:
        assert session.scalar(select(func.count(Location.id))) == 1


def test_startup_skips_import_when_locations_already_exist(
    db_engine: Engine,
    tmp_path: Path,
) -> None:
    session_factory = sessionmaker(bind=db_engine, expire_on_commit=False)
    with session_factory.begin() as session:
        session.add(
            Location(
                content_id="existing-100",
                category="관광지",
                title="기존 장소",
                address1=None,
                address2=None,
                district="기타",
                longitude=None,
                latitude=None,
                image_url=None,
                thumbnail_url=None,
                phone=None,
                source_order=1,
            )
        )
    app = create_app(
        bootstrap_locations=True,
        session_factory=session_factory,
        location_manifest=tmp_path / "missing-manifest.json",
    )

    with TestClient(app):
        pass

    with session_factory() as session:
        assert session.scalar(select(func.count(Location.id))) == 1
        assert session.scalar(select(Location.content_id)) == "existing-100"


def test_startup_fails_when_initial_import_fails(
    db_engine: Engine,
    tmp_path: Path,
) -> None:
    session_factory = sessionmaker(bind=db_engine, expire_on_commit=False)
    app = create_app(
        bootstrap_locations=True,
        session_factory=session_factory,
        location_manifest=tmp_path / "missing-manifest.json",
    )

    with pytest.raises(ImportValidationError, match="cannot read JSON source"):
        with TestClient(app):
            pass
