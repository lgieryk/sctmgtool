# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Łukasz Gieryk

import argparse
import base64
import gc
import io
import json
import os
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlsplit

from flask import Flask, Response, abort, request, send_file
from matplotlib.backends.backend_agg import FigureCanvasAgg

import sctmgtool
from sctmgtool.base import Upgrade
from sctmgtool.histogram import draw_histograms, simulate_clash
from sctmgtool.tools import MusteredUnit, process_unit_list
from sctmgtool.units import ALL_UNITS
from sctmgtool.web.cache import APP_REVISION, CHARTS_REVISION, ImageCache


@lru_cache(maxsize=1)
def get_units():
    process_unit_list(ALL_UNITS)
    return tuple(ALL_UNITS)


@lru_cache(maxsize=1)
def get_units_json() -> str:
    units = sorted(get_units(), key=lambda unit: (unit.faction.value, unit.name))
    return json.dumps(
        {
            "cacheRevision": {"app": APP_REVISION, "charts": CHARTS_REVISION},
            "units": [serialize_unit(unit) for unit in units],
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )


def serialize_upgrade(upgrade, index):
    upgrade_types = []
    if Upgrade.Type.Offensive in upgrade.upgrade_type:
        upgrade_types.append("offensive")
    if Upgrade.Type.Defensive in upgrade.upgrade_type:
        upgrade_types.append("defensive")

    return {
        "summary": str(upgrade),
        "activatesWeapon": upgrade.name if upgrade.message == "Upgrade weapon" else None,
        "fingerprintIndex": index,
        "type": upgrade_types,
    }


def serialize_unit(unit):
    return {
        "name": unit.name,
        "faction": unit.faction.name,
        "summary": str(unit),
        "squads": [
            {
                "models": {"min": squad.models.start, "max": squad.models.stop},
                "supply": squad.supply,
                "points": squad.points,
            }
            for squad in unit.squad
        ],
        "weapons": [
            {
                "name": weapon.name,
                "summary": str(weapon),
                "range": weapon.range,
                "exchangeFor": weapon.exchange_for,
                "tags": str(weapon.tags).split("|") if weapon.tags else [],
            }
            for weapon in unit.weapons
        ],
        "upgrades": [serialize_upgrade(upgrade, index) for index, upgrade in enumerate(unit.upgrades) if upgrade.upgrade_type != Upgrade.Type.Other],
    }


def parse_result_key(result_key: str):
    try:
        padding = "=" * (-len(result_key) % 4)
        attacker, defender = json.loads(base64.urlsafe_b64decode(result_key + padding).decode("utf-8"))
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
        return None

    if not all(
        isinstance(fingerprint, list)
        and len(fingerprint) == 3
        and isinstance(fingerprint[0], str)
        and isinstance(fingerprint[1], int)
        and isinstance(fingerprint[2], int)
        for fingerprint in (attacker, defender)
    ):
        return None

    return attacker, defender


def make_unit_from_fingerprint(fingerprint: list, is_attacker: bool) -> MusteredUnit:
    name, squad_size, configuration = fingerprint
    prototype = next((unit for unit in get_units() if unit.name == name), None)
    if prototype is None or squad_size not in [squad.models.stop for squad in prototype.squad]:
        raise ValueError("Unknown unit or invalid squad size.")

    config = {"_squad_size" if is_attacker else "_squad_size_def": squad_size}
    config.update({upgrade.name: bool(configuration & (1 << index)) for index, upgrade in enumerate(prototype.upgrades)})
    return MusteredUnit.make(prototype, config, is_attacker)


def render_results_png(histograms) -> bytes:
    figure = draw_histograms(histograms, {"figsize": (15, 3), "dpi": 72})

    output = io.BytesIO()
    canvas = FigureCanvasAgg(figure)
    try:
        canvas.print_png(output)
        return output.getvalue()
    finally:
        figure.clear()
        figure.set_canvas(None)
        canvas.figure = None


def make_results_png(attacker_fingerprint: list, defender_fingerprint: list) -> bytes:
    attacker = make_unit_from_fingerprint(attacker_fingerprint, True)
    defender = make_unit_from_fingerprint(defender_fingerprint, False)
    histograms = simulate_clash(attacker, defender)
    try:
        return render_results_png(histograms)
    finally:
        gc.collect()


def parse_allowed_origins(value: str) -> frozenset[str]:
    origins = set()
    for configured_origin in value.split(","):
        origin = configured_origin.strip()
        if not origin:
            continue

        parsed = urlsplit(origin)
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.netloc
            or parsed.username is not None
            or parsed.password is not None
            or parsed.path not in {"", "/"}
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError(f"Invalid CORS origin: {origin!r}")

        origins.add(origin.rstrip("/"))

    return frozenset(origins)


def create_flask_app(
    *,
    cache_dir: str | Path | None = None,
    database_url: str | None = None,
    allowed_origins: str | None = None,
) -> Flask:
    app = Flask(__name__, static_url_path="")
    cache_path = Path(cache_dir or os.environ.get("SCTMGTOOL_WEB_CACHE_DIR", "web-cache")).expanduser().resolve()
    database_url = database_url or os.environ.get("SCTMGTOOL_WEB_DATABASE_URL")
    configured_origins = parse_allowed_origins(allowed_origins if allowed_origins is not None else os.environ.get("SCTMGTOOL_WEB_ALLOWED_ORIGINS", ""))
    if database_url is None:
        database_url = f"sqlite:///{(cache_path / 'results.sqlite3').resolve()}"

    app.extensions["cache"] = ImageCache(cache_path, database_url)

    @app.after_request
    def add_cors_headers(response):
        if not configured_origins or not request.path.startswith("/api/"):
            return response

        response.vary.add("Origin")
        if request.headers.get("Origin") not in configured_origins:
            return response

        response.headers["Access-Control-Allow-Origin"] = request.headers["Origin"]
        if request.method == "OPTIONS":
            response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        return response

    @app.get("/")
    def index():
        return app.send_static_file("index.html")

    @app.get("/health")
    def health():
        return {"status": "ok", "version": sctmgtool.__version__}

    @app.get("/api/units")
    def list_units():
        """Return all unit data needed by the frontend.

        Upgrades classified as ``Other`` cannot affect a combat configuration,
        so they are intentionally omitted from the response.
        """
        return Response(get_units_json(), mimetype="application/json")

    @app.get("/api/results/<app_revision>/<int:charts_revision>/<result_key>")
    def result_image(app_revision: str, charts_revision: int, result_key: str):
        if app_revision != APP_REVISION or charts_revision != CHARTS_REVISION:
            abort(404, description="Unknown chart revision.")

        fingerprints = parse_result_key(result_key)
        if fingerprints is None:
            abort(400, description="Invalid combat result key.")

        try:
            image_path = app.extensions["cache"].get_or_create(result_key, lambda: make_results_png(*fingerprints))
        except ValueError:
            abort(400, description="Unknown unit or invalid squad size.")
        response = send_file(image_path, mimetype="image/png", conditional=True)
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        return response

    return app


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the SC:TMG Tool web application.")
    parser.add_argument("--cache-dir", help="Directory used to store generated result images.")
    parser.add_argument("--database-url", help="SQLAlchemy database URL for the result cache index.")
    arguments = parser.parse_args()

    application = create_flask_app(cache_dir=arguments.cache_dir, database_url=arguments.database_url)
    application.run(
        host=os.environ.get("FLASK_HOST", "127.0.0.1"),
        port=int(os.environ.get("FLASK_PORT", "5000")),
        debug=os.environ.get("FLASK_DEBUG", "false").lower() == "true",
    )


if __name__ == "__main__":
    main()
