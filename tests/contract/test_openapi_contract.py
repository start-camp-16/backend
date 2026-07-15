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


def test_post_contract_uses_district_and_prefix_and_removes_tag():
    document = load_contract()
    schemas = document["components"]["schemas"]
    list_parameters = document["paths"]["/api/posts"]["get"]["parameters"]

    assert schemas["PostDistrict"]["enum"] == [
        "강남구", "강동구", "강북구", "강서구", "관악구", "광진구", "구로구",
        "금천구", "노원구", "도봉구", "동대문구", "동작구", "마포구", "서대문구",
        "서초구", "성동구", "성북구", "송파구", "양천구", "영등포구", "용산구",
        "은평구", "종로구", "중구", "중랑구",
    ]
    assert schemas["PostPrefix"]["enum"] == [
        "관광", "맛집", "문화", "행사", "숙박", "쇼핑", "자유"
    ]
    assert "PostTag" not in schemas
    parameter_names = {
        parameter["name"] for parameter in list_parameters if "name" in parameter
    }
    assert parameter_names >= {"district", "prefix"}
    assert "tag" not in parameter_names
    assert set(schemas["PostCreateRequest"]["required"]) >= {"district", "prefix"}
    assert "tag" not in schemas["PostCreateRequest"]["properties"]
    assert set(schemas["PostSource"]["required"]) >= {"district", "prefix"}
