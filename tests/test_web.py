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
