import logging
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.locations.importer import ImportReport, import_manifest
from app.models import Location

logger = logging.getLogger(__name__)

DEFAULT_LOCATION_MANIFEST = Path(__file__).resolve().parents[2] / "data" / "manifest.json"


def ensure_location_data(
    session_factory: sessionmaker[Session],
    manifest_path: str | Path = DEFAULT_LOCATION_MANIFEST,
) -> ImportReport | None:
    with session_factory() as session:
        if session.scalar(select(Location.id).limit(1)) is not None:
            logger.info("Location bootstrap skipped because data already exists")
            return None

    with session_factory() as session:
        report = import_manifest(session, manifest_path)

    logger.info(
        "Location bootstrap completed",
        extra={"inserted": report.inserted, "total": report.total},
    )
    return report
