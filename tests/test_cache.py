# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Łukasz Gieryk

import pickle

from sctmgtool.cache import Cache
from sctmgtool.tools import ClashType


class _Manager:
    @staticmethod
    def dict(value=None):
        return dict(value or {})


def test_cache_loads_pickle_with_charge_clash_type(tmp_path, monkeypatch):
    with open(tmp_path / Cache.FILENAME, "wb") as file:
        pickle.dump(((Cache.MAJOR_REVISION, "revision"), {ClashType.Charge: "histogram"}), file)

    monkeypatch.setattr("sctmgtool.cache.Manager", _Manager)

    cache = Cache("revision", tmp_path)

    assert cache.data == {ClashType.Charge: "histogram"}
