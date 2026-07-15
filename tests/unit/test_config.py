from app.config import Settings


def test_settings_allow_startup_without_openai_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    settings = Settings(_env_file=None)

    assert settings.openai_api_key is None


def test_cors_origins_are_trimmed_and_empty_values_removed():
    settings = Settings(
        _env_file=None,
        cors_origins="http://localhost:5173, https://example.com, ",
    )

    assert settings.cors_origin_list == [
        "http://localhost:5173",
        "https://example.com",
    ]


def test_admin_password_is_optional_by_default(monkeypatch):
    monkeypatch.delenv("ADMIN_PASSWORD", raising=False)

    settings = Settings(_env_file=None)

    assert settings.admin_password is None


def test_admin_password_loads_as_secret(monkeypatch):
    monkeypatch.setenv("ADMIN_PASSWORD", "operator-pass")

    settings = Settings(_env_file=None)

    assert settings.admin_password is not None
    assert settings.admin_password.get_secret_value() == "operator-pass"
