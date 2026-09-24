# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Łukasz Gieryk

from copy import deepcopy
from unittest.mock import patch

from sctmgtool.base import Tag, Weapon
from sctmgtool.histogram import simulate_clash
from sctmgtool.tools import ClashType, MusteredUnit
from sctmgtool.units import ALL_UNITS


def clone(name: str):
    prototype = next(unit for unit in ALL_UNITS if unit.name == name)
    return deepcopy(prototype)


def test_concentrated_fire_batches_are_resolved_first_and_limit_casualties():
    attacker_prototype = clone("Marine")
    attacker_prototype.weapons = (
        Weapon("Regular", 12, Tag.Ground, 1, 3, None, None, 1),
        Weapon("Concentrated 1", 12, Tag.Ground, 1, 3, None, None, 1, tags=Tag.Sidearm | Tag.ConcentratedFire1),
        Weapon("Concentrated 2", 12, Tag.Ground, 1, 3, None, None, 1, tags=Tag.Sidearm | Tag.ConcentratedFire1),
    )
    attacker_prototype.upgrades = ()
    attacker = MusteredUnit.make(attacker_prototype, {})

    defender = MusteredUnit.make(clone("Marine"), {})
    defender.models = 4
    defender.hit_points = 5
    defender.shield = 0

    resolved = []

    def fixed_damage(_, batch, __, ___):
        resolved.append(batch.weapon.name)
        return 3 if batch.weapon.name == "Regular" else 10

    with patch("sctmgtool.histogram.roll_damage", side_effect=fixed_damage):
        histogram = simulate_clash(attacker, defender, roll_count=1)[ClashType.Ranged]

    assert resolved == ["Concentrated 1", "Concentrated 2", "Regular"]
    assert histogram.damage[13] == 100
    assert histogram.kills[2] == 100


def test_concentrated_fire_preserves_damage_marker_before_reaching_casualty_limit():
    attacker_prototype = clone("Marine")
    attacker_prototype.weapons = (
        Weapon("Concentrated", 12, Tag.Ground, 1, 3, None, None, 1, tags=Tag.ConcentratedFire1),
        Weapon("Regular", 12, Tag.Ground, 1, 3, None, None, 1, tags=Tag.Sidearm),
    )
    attacker_prototype.upgrades = ()
    attacker = MusteredUnit.make(attacker_prototype, {})

    defender = MusteredUnit.make(clone("Marine"), {})
    defender.models = 2
    defender.hit_points = 10
    defender.shield = 0

    with patch("sctmgtool.histogram.roll_damage", return_value=5):
        histogram = simulate_clash(attacker, defender, roll_count=1)[ClashType.Ranged]

    assert histogram.damage[10] == 100
    assert histogram.kills[1] == 100
