# SC:TMG Tool Web Interface

## Local setup

Install the optional web dependencies:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[web]'
```

Run the Flask application:

```sh
python -m sctmgtool.web.app --cache-dir ./web-cache
```

The development server listens on `127.0.0.1:5000` by default. The host, port,
and debug mode can be configured with `FLASK_HOST`, `FLASK_PORT`, and
`FLASK_DEBUG`.

Do not expose the Flask development server directly to the Internet. Use a
production WSGI server and a TLS reverse proxy for public deployments.

## Cache database

By default, the web cache uses a SQLite database named `results.sqlite3` in the
cache directory. This is suitable for local development.

To use MySQL or MariaDB, supply a SQLAlchemy URL. The `web` extra includes the
PyMySQL driver:

```sh
python -m sctmgtool.web.app \
  --cache-dir /tmp/sctmgtool-cache/ \
  --database-url 'mysql+pymysql://USER:PASSWORD@HOST:3306/DATABASE'
```

The same values can be provided through environment variables:

- `SCTMGTOOL_WEB_CACHE_DIR`;
- `SCTMGTOOL_WEB_DATABASE_URL`.

## Cross-origin access

The static frontend can be hosted on a different origin, such as GitHub Pages.
Set `SCTMGTOOL_WEB_ALLOWED_ORIGINS` to a comma-separated list of origins that
may access the API:

```sh
SCTMGTOOL_WEB_ALLOWED_ORIGINS=https://lgieryk.github.io \
  python -m sctmgtool.web.app --cache-dir ./web-cache
```

An origin consists only of the scheme, host, and optional port. Do not include
the GitHub Pages project path or a trailing path:

```text
https://lgieryk.github.io
```

Requests without an `Origin` header continue to work normally. Requests from
origins outside the configured allowlist receive the API response without CORS
permission, so browsers cannot expose it to the calling page.
