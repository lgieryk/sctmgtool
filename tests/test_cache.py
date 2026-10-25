# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Łukasz Gieryk

import pickle

from sctmgtool.cache import Cache
from sctmgtool.tools import ClashType


class _LegacyCharge:
    def __reduce__(self):
        return ClashType, ("Charge",)


class _Manager:
    @staticmethod
    def dict(value=None):
        return dict(value or {})


def test_cache_ignores_pickle_with_legacy_enum_value(tmp_path, monkeypatch):
    with open(tmp_path / Cache.FILENAME, "wb") as file:
        pickle.dump(((Cache.MAJOR_REVISION, "revision"), {_LegacyCharge(): "histogram"}), file)

    monkeypatch.setattr("sctmgtool.cache.Manager", _Manager)

    cache = Cache("revision", tmp_path)

    assert cache.data == {}
