from pathlib import Path
from typing import Any

import yaml
from fastapi import FastAPI

CONTRACT_PATH = Path(__file__).resolve().parents[1] / "shared" / "openapi.yaml"


def load_openapi_contract() -> dict[str, Any]:
    document = yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise RuntimeError("OpenAPI contract must contain an object")
    return document


def install_canonical_openapi(app: FastAPI) -> None:
    contract = load_openapi_contract()

    def canonical_openapi() -> dict[str, Any]:
        return contract

    app.openapi = canonical_openapi  # type: ignore[method-assign]
