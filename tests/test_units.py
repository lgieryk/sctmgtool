# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Łukasz Gieryk

from sctmgtool.tools import MusteredUnit
from sctmgtool.units import ALL_UNITS


def muster(name: str, config=None):
    prototype = next(unit for unit in ALL_UNITS if unit.name == name)
    return MusteredUnit.make(prototype, config or {})


def test_ravager_corrosive_bile_weapon_combinations():
    cases = (
        ({}, ("Plasma Discharge",)),
        ({"! Corrosive Bile": True}, ("Plasma Discharge", "! Corrosive Bile")),
        ({"! Corrosive Bile (2)": True}, ("! Corrosive Bile",)),
        ({"! Corrosive Bile": True, "! Corrosive Bile (2)": True}, ("! Corrosive Bile",)),
    )

    for config, expected in cases:
        ravager = muster("Ravager", config)
        active = tuple(batch.weapon.name for batch in ravager.weapon_batches if batch.weapon.name in ("Plasma Discharge", "! Corrosive Bile"))
        assert active == expected


def test_zeratul_shadow_strike_weapon_combinations():
    cases = (
        ({}, ("Master Warp Blade",)),
        ({"! Shadow Strike": True}, ("Master Warp Blade", "! Shadow Strike")),
        ({"! Shadow Strike (2)": True}, ("! Shadow Strike",)),
        ({"! Shadow Strike": True, "! Shadow Strike (2)": True}, ("! Shadow Strike",)),
    )

    for config, expected in cases:
        zeratul = muster("Zeratul", config)
        active = tuple(batch.weapon.name for batch in zeratul.weapon_batches if batch.weapon.name in ("Master Warp Blade", "! Shadow Strike"))
        assert active == expected
