# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Łukasz Gieryk

__version__ = "0.6.0"
UNIT_DATA_REVISION = "Wave 3 / 27 October 2026"


def application_revision_label() -> str:
    return f"Version {__version__} · Unit data: {UNIT_DATA_REVISION}"
