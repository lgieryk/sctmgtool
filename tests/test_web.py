import base64
import gc
import json
import weakref

from matplotlib.figure import Figure

from sctmgtool.web import app as web_app
from sctmgtool.web.cache import APP_REVISION, CHARTS_REVISION


def encode_result_key(attacker, defender):
    payload = json.dumps([attacker, defender], separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")


def test_result_image_with_relative_cache_dir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    image = b"\x89PNG\r\n\x1a\nregression-test"
    monkeypatch.setattr(web_app, "make_results_png", lambda *_: image)

    application = web_app.create_flask_app(cache_dir="web-cache")
    result_key = encode_result_key(["Marine", 6, 0], ["Zealot", 3, 0])
    response = application.test_client().get(f"/api/results/{APP_REVISION}/{CHARTS_REVISION}/{result_key}")

    assert application.extensions["cache"].cache_dir == tmp_path / "web-cache"
    assert response.status_code == 200
    assert response.mimetype == "image/png"
    assert response.data == image


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


def test_make_results_png_releases_figure_without_garbage_collection(monkeypatch):
    figure_references = []

    def draw_test_figure(*_):
        figure = Figure()
        figure.add_subplot().plot([0, 1], [0, 1])
        figure_references.append(weakref.ref(figure))
        return figure

    monkeypatch.setattr(web_app, "make_unit_from_fingerprint", lambda *_: object())
    monkeypatch.setattr(web_app, "simulate_clash", lambda *_: {})
    monkeypatch.setattr(web_app, "draw_histograms", draw_test_figure)

    gc.collect()
    gc.disable()
    try:
        image = web_app.make_results_png(["attacker"], ["defender"])
        assert image.startswith(b"\x89PNG\r\n\x1a\n")
        assert figure_references[0]() is None
    finally:
        gc.enable()
        gc.collect()
