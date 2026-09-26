# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Łukasz Gieryk

from copy import deepcopy
from unittest.mock import patch

from sctmgtool import hooks
from sctmgtool.base import Hook, Tag, Weapon
from sctmgtool.histogram import simulate_clash
from sctmgtool.tools import ClashType, HookContext, MusteredUnit, WeaponBatch
from sctmgtool.units import ALL_UNITS


def muster(name: str, config=None):
    prototype = next(unit for unit in ALL_UNITS if unit.name == name)
    return MusteredUnit.make(prototype, config or {})


def clone(name: str):
    prototype = next(unit for unit in ALL_UNITS if unit.name == name)
    return deepcopy(prototype)


def test_ancillary_carapace_applies_tough_only_to_first_weapon_of_each_clash():
    attacker = MusteredUnit.make(clone("Marine"), {})
    weapons = (
        Weapon("First", 12, Tag.Ground, 1, "!", None, None, 1),
        Weapon("Second", 12, Tag.Ground, 1, "!", None, None, 1),
    )
    attacker.weapon_batches = [WeaponBatch(1, weapon) for weapon in weapons]

    defender = MusteredUnit.make(clone("Hydralisk"), {"Ancillary Carapace": True}, is_attacker=False)
    defender.armour = 7
    defender.shield = 0

    with patch("sctmgtool.tools.random.choices", side_effect=lambda _, k: [1] * k):
        histogram = simulate_clash(attacker, defender, roll_count=2)[ClashType.Ranged]

    assert histogram.damage[1] == 100


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


def test_psionic_presence_does_not_affect_shadow_strike():
    zeratul = muster("Zeratul", {"! Shadow Strike": True, "! Psionic Presence / Adept": True})

    assert Tag.Precision1 in zeratul.batch("Master Warp Blade").weapon.tags
    assert Tag.Precision1 not in zeratul.batch("! Shadow Strike").weapon.tags


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
