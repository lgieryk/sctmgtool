# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Łukasz Gieryk

from sctmgtool import hooks
from sctmgtool.base import Hook
from sctmgtool.tools import HookContext, MusteredUnit
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


def test_siege_tank_shock_cannon_automatically_applies_aftershock_rounds():
    prototype = next(unit for unit in ALL_UNITS if unit.name == "Siege Tank")
    upgrade_names = {upgrade.name for upgrade in prototype.upgrades}
    assert "! Shock Cannon / Aftershock Rounds" in upgrade_names
    assert "Aftershock Rounds" not in upgrade_names

    tank_without_upgrade = muster("Siege Tank")
    assert tank_without_upgrade.batch("Twin Cannon") is not None
    assert tank_without_upgrade.batch("Shock Cannon") is None

    tank = muster("Siege Tank", {"! Shock Cannon / Aftershock Rounds": True})
    shock_cannon = tank.batch("Shock Cannon")
    assert shock_cannon is not None
    assert tank.batch("Twin Cannon") is None

    defender = muster("Marine")
    damage = hooks.DamageHookArgs(shock_cannon.weapon.damage)
    HookContext(tank).call_hooks(Hook.ModifyDamage, hooks.RollHookArgs(tank, shock_cannon, defender), damage)
    assert damage.value == defender.size
