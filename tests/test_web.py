import base64
import gc
import json
import weakref
from unittest.mock import Mock
from urllib.parse import urlsplit

import pytest
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

from sctmgtool.web import app as web_app
from sctmgtool.web.cache import APP_REVISION, CHARTS_REVISION


def encode_result_key(attacker, defender):
    payload = json.dumps([attacker, defender], separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")


def encode_json(payload):
    return base64.urlsafe_b64encode(payload.encode("utf-8")).decode("ascii").rstrip("=")


def test_frontend_includes_shareable_configuration_support(tmp_path):
    application = web_app.create_flask_app(cache_dir=tmp_path)
    client = application.test_client()

    index = client.get("/")
    script = client.get("/app.js")

    assert index.status_code == 200
    assert b'id="link-version-warning"' in index.data
    assert script.status_code == 200
    assert b"history.replaceState" in script.data
    assert b"readLinkedConfiguration" in script.data
    assert b"MAX_SHARE_FRAGMENT_LENGTH" in script.data
    assert b"allowedConfigurationMask" in script.data


def test_frontend_loads_configured_unit_display_from_backend(tmp_path):
    application = web_app.create_flask_app(cache_dir=tmp_path)

    script = application.test_client().get("/app.js")

    assert script.status_code == 200
    assert b"/api/configurations/" in script.data
    assert b"AbortController" in script.data
    assert b"getAttackerWeaponBatches" not in script.data
    assert b"activatesWeapon" not in script.data


@pytest.mark.parametrize(
    "result_key",
    [
        encode_json("1"),
        encode_result_key(["Marine", True, 0], ["Zealot", 3, 0]),
        encode_result_key(["Marine", 6, True], ["Zealot", 3, 0]),
        encode_result_key(["Marine", 6, -1], ["Zealot", 3, 0]),
        "not!base64",
        "A" * (web_app.MAX_RESULT_KEY_LENGTH + 1),
    ],
)
def test_result_image_rejects_malformed_key_before_cache(tmp_path, monkeypatch, result_key):
    generate_image = Mock()
    monkeypatch.setattr(web_app, "make_results_webp", generate_image)
    application = web_app.create_flask_app(cache_dir=tmp_path)

    response = application.test_client().get(f"/api/results/{APP_REVISION}/{CHARTS_REVISION}/{result_key}")

    assert response.status_code == 400
    assert generate_image.call_count == 0
    assert list(application.extensions["cache"].image_dir.iterdir()) == []


@pytest.mark.parametrize(
    "result_key",
    [
        encode_result_key(["Marine", 6, 1], ["Zealot", 3, 0]),
        encode_result_key(["Marine", 6, 1 << 30], ["Zealot", 3, 0]),
        encode_json(json.dumps([["Marine", 6, 0], ["Zealot", 3, 0]])),
    ],
)
def test_result_image_rejects_noncanonical_key_before_cache(tmp_path, monkeypatch, result_key):
    generate_image = Mock()
    monkeypatch.setattr(web_app, "make_results_webp", generate_image)
    application = web_app.create_flask_app(cache_dir=tmp_path)

    response = application.test_client().get(f"/api/results/{APP_REVISION}/{CHARTS_REVISION}/{result_key}")

    assert response.status_code == 400
    assert generate_image.call_count == 0
    assert list(application.extensions["cache"].image_dir.iterdir()) == []


def test_result_image_with_relative_cache_dir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    image = b"RIFF\x10\x00\x00\x00WEBPVP8 regression-test"
    generate_image = Mock(return_value=image)
    monkeypatch.setattr(web_app, "make_results_webp", generate_image)

    application = web_app.create_flask_app(cache_dir="web-cache")
    client = application.test_client()
    result_key = encode_result_key(["Marine", 6, 0], ["Zealot", 3, 0])
    response = client.get(f"/api/results/{APP_REVISION}/{CHARTS_REVISION}/{result_key}")
    cached_response = client.get(f"/api/results/{APP_REVISION}/{CHARTS_REVISION}/{result_key}")
    generated_response = client.get(response.headers["Location"])
    image_files = list(application.extensions["cache"].image_dir.iterdir())
    location = urlsplit(response.headers["Location"])

    assert application.extensions["cache"].cache_dir == tmp_path / "web-cache"
    assert response.status_code == 302
    assert not location.scheme
    assert not location.netloc
    assert location.path == f"/generated/{APP_REVISION}/{CHARTS_REVISION}/{image_files[0].name}"
    assert cached_response.status_code == 302
    assert cached_response.headers["Location"] == response.headers["Location"]
    assert generated_response.status_code == 200
    assert generated_response.mimetype == "image/webp"
    assert generated_response.data == image
    assert generated_response.headers["Cache-Control"] == "public, max-age=31536000, immutable"
    assert generate_image.call_count == 1
    assert len(image_files) == 1
    assert image_files[0].suffix == ".webp"


@pytest.mark.parametrize(
    "path",
    [
        f"/generated/{APP_REVISION}/{CHARTS_REVISION}/results.sqlite3",
        f"/generated/{APP_REVISION}/{CHARTS_REVISION}/{'0' * 64}.webp",
        f"/generated/{APP_REVISION}/{CHARTS_REVISION - 1}/{'0' * 64}.webp",
        f"/generated/unknown/{CHARTS_REVISION}/{'0' * 64}.webp",
    ],
)
def test_generated_image_rejects_invalid_or_missing_file(tmp_path, path):
    application = web_app.create_flask_app(cache_dir=tmp_path)

    response = application.test_client().get(path)

    assert response.status_code == 404


def test_result_redirect_keeps_api_cors_headers(tmp_path, monkeypatch):
    monkeypatch.setattr(web_app, "make_results_webp", lambda *_: b"RIFF\x10\x00\x00\x00WEBPVP8 regression-test")
    application = web_app.create_flask_app(cache_dir=tmp_path, allowed_origins="https://lgieryk.github.io")
    result_key = encode_result_key(["Marine", 6, 0], ["Zealot", 3, 0])

    response = application.test_client().get(
        f"/api/results/{APP_REVISION}/{CHARTS_REVISION}/{result_key}",
        headers={"Origin": "https://lgieryk.github.io"},
    )

    assert response.status_code == 302
    assert response.headers["Access-Control-Allow-Origin"] == "https://lgieryk.github.io"


@pytest.mark.parametrize(
    ("app_revision", "charts_revision"),
    [
        (APP_REVISION, CHARTS_REVISION - 1),
        (APP_REVISION, CHARTS_REVISION + 1),
        ("unknown", CHARTS_REVISION),
    ],
)
def test_result_image_rejects_old_or_unknown_revision(tmp_path, app_revision, charts_revision):
    application = web_app.create_flask_app(cache_dir=tmp_path)
    result_key = encode_result_key(["Marine", 6, 0], ["Zealot", 3, 0])

    response = application.test_client().get(f"/api/results/{app_revision}/{charts_revision}/{result_key}")

    assert response.status_code == 404


def test_cors_allows_configured_origin_from_environment(tmp_path, monkeypatch):
    monkeypatch.setenv("SCTMGTOOL_WEB_ALLOWED_ORIGINS", "https://lgieryk.github.io")
    application = web_app.create_flask_app(cache_dir=tmp_path)

    response = application.test_client().get("/api/units", headers={"Origin": "https://lgieryk.github.io"})

    assert response.status_code == 200
    assert response.headers["Access-Control-Allow-Origin"] == "https://lgieryk.github.io"
    assert "Origin" in response.vary


def test_cors_rejects_unconfigured_origin(tmp_path):
    application = web_app.create_flask_app(cache_dir=tmp_path, allowed_origins="https://lgieryk.github.io")

    response = application.test_client().get("/api/units", headers={"Origin": "https://example.com"})

    assert response.status_code == 200
    assert "Access-Control-Allow-Origin" not in response.headers
    assert "Origin" in response.vary


def test_cors_does_not_affect_request_without_origin(tmp_path):
    application = web_app.create_flask_app(cache_dir=tmp_path, allowed_origins="https://lgieryk.github.io")

    response = application.test_client().get("/api/units")

    assert response.status_code == 200
    assert "Access-Control-Allow-Origin" not in response.headers


def test_units_api_serializes_upgrade_point_costs(tmp_path):
    application = web_app.create_flask_app(cache_dir=tmp_path)

    response = application.test_client().get("/api/units")
    marine = next(unit for unit in response.json["units"] if unit["name"] == "Marine")
    combat_shield = next(upgrade for upgrade in marine["upgrades"] if upgrade["summary"].startswith("Combat Shield "))
    agg_12 = next(upgrade for upgrade in marine["upgrades"] if upgrade["summary"].startswith("AGG-12 "))

    assert combat_shield["pointCost"] == {"small": 20, "large": 30}
    assert agg_12["pointCost"] == {"small": 10, "large": 10}


def test_configured_units_api_returns_backend_weapon_loadout(tmp_path):
    application = web_app.create_flask_app(cache_dir=tmp_path)
    ravager = next(unit for unit in web_app.get_units() if unit.name == "Ravager")
    corrosive_bile_index = next(index for index, upgrade in enumerate(ravager.upgrades) if upgrade.name == "! Corrosive Bile (2)")
    result_key = encode_result_key(["Ravager", 1, 1 << corrosive_bile_index], ["Zealot", 3, 0])

    response = application.test_client().get(f"/api/configurations/{APP_REVISION}/{result_key}")
    plasma_discharge = next(weapon for weapon in response.json["attacker"]["weapons"] if "Plasma Discharge" in weapon["text"])
    corrosive_bile = next(weapon for weapon in response.json["attacker"]["weapons"] if "! Corrosive Bile" in weapon["text"])

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "public, max-age=31536000, immutable"
    assert response.json["attacker"]["summary"].startswith("Ravager SHLD:None EVA:5+ ARM:5+ HP:9 SIZ:3 ")
    assert plasma_discharge["active"] is False
    assert corrosive_bile["active"] is True
    assert response.json["defender"]["summary"].startswith("Zealot SHLD:3 EVA:5+ ARM:5+ HP:4 SIZ:2 ")


@pytest.mark.parametrize(
    ("app_revision", "result_key", "expected_status"),
    [
        (APP_REVISION, "invalid", 400),
        (APP_REVISION, encode_result_key(["Marine", 6, 1], ["Zealot", 3, 0]), 400),
        ("unknown", encode_result_key(["Marine", 6, 0], ["Zealot", 3, 0]), 404),
    ],
)
def test_configured_units_api_rejects_invalid_key_or_revision(tmp_path, app_revision, result_key, expected_status):
    application = web_app.create_flask_app(cache_dir=tmp_path)

    response = application.test_client().get(f"/api/configurations/{app_revision}/{result_key}")

    assert response.status_code == expected_status


def test_cors_is_added_to_api_error(tmp_path):
    application = web_app.create_flask_app(cache_dir=tmp_path, allowed_origins="https://lgieryk.github.io")

    response = application.test_client().get(
        f"/api/results/{APP_REVISION}/{CHARTS_REVISION}/invalid",
        headers={"Origin": "https://lgieryk.github.io"},
    )

    assert response.status_code == 400
    assert response.headers["Access-Control-Allow-Origin"] == "https://lgieryk.github.io"


def test_cors_preflight_for_get_endpoint(tmp_path):
    application = web_app.create_flask_app(cache_dir=tmp_path, allowed_origins="https://lgieryk.github.io")

    response = application.test_client().options(
        "/api/units",
        headers={
            "Origin": "https://lgieryk.github.io",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["Access-Control-Allow-Origin"] == "https://lgieryk.github.io"
    assert response.headers["Access-Control-Allow-Methods"] == "GET, OPTIONS"


def test_invalid_cors_origin_is_rejected(tmp_path):
    try:
        web_app.create_flask_app(cache_dir=tmp_path, allowed_origins="https://lgieryk.github.io/project")
    except ValueError as error:
        assert str(error) == "Invalid CORS origin: 'https://lgieryk.github.io/project'"
    else:
        raise AssertionError("Invalid CORS origin was accepted.")


def test_make_results_webp_uses_quality_85_and_releases_figure_without_garbage_collection(monkeypatch):
    figure_references = []
    webp_options = []
    original_print_webp = FigureCanvasAgg.print_webp

    def draw_test_figure(*_):
        figure = Figure()
        figure.add_subplot().plot([0, 1], [0, 1])
        figure_references.append(weakref.ref(figure))
        return figure

    def capture_print_webp(canvas, output, *, pil_kwargs):
        webp_options.append(pil_kwargs)
        return original_print_webp(canvas, output, pil_kwargs=pil_kwargs)

    monkeypatch.setattr(web_app, "make_unit_from_fingerprint", lambda *_: object())
    monkeypatch.setattr(web_app, "simulate_clash", lambda *_: {})
    monkeypatch.setattr(web_app, "draw_histograms", draw_test_figure)
    monkeypatch.setattr(FigureCanvasAgg, "print_webp", capture_print_webp)

    gc.collect()
    gc.disable()
    try:
        image = web_app.make_results_webp(["attacker"], ["defender"])
        assert image.startswith(b"RIFF")
        assert image[8:12] == b"WEBP"
        assert webp_options == [{"quality": 85}]
        assert figure_references[0]() is None
    finally:
        gc.enable()
        gc.collect()
