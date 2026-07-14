from pathlib import Path

import yaml
from fastapi.routing import APIRoute
from starlette.testclient import TestClient

from app.main import create_app

HTTP_METHODS = {"get", "post", "put", "patch", "delete"}


def load_contract() -> dict:
    return yaml.safe_load(Path("shared/openapi.yaml").read_text(encoding="utf-8"))


def contract_operations(document: dict) -> set[tuple[str, str]]:
    return {
        (path, method)
        for path, path_item in document["paths"].items()
        for method in path_item
        if method in HTTP_METHODS
    }


def collect_api_routes(routes) -> list[APIRoute]:
    collected = []
    for route in routes:
        if isinstance(route, APIRoute):
            collected.append(route)
        elif hasattr(route, "original_router"):
            collected.extend(collect_api_routes(route.original_router.routes))
    return collected


def runtime_operations(app) -> set[tuple[str, str]]:
    return {
        (route.path, method.lower())
        for route in collect_api_routes(app.routes)
        for method in route.methods
        if method.lower() in HTTP_METHODS
    }


def test_runtime_routes_implement_every_contract_operation():
    app = create_app()

    assert runtime_operations(app) == contract_operations(load_contract())


def test_runtime_openapi_is_the_canonical_contract():
    app = create_app()

    response = TestClient(app).get("/openapi.json")

    assert response.status_code == 200
    assert response.json() == load_contract()
