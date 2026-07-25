# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Łukasz Gieryk

from copy import deepcopy

from sctmgtool.tools import MusteredUnit, Tag, Weapon
from sctmgtool.units import ALL_UNITS
from sctmgtool.units.terran import apply_jim_raynors_orders


def muster(name: str, config=None):
    prototype = next(unit for unit in ALL_UNITS if unit.name == name)
    return MusteredUnit.make(prototype, config or {})


def clone(name: str):
    prototype = next(unit for unit in ALL_UNITS if unit.name == name)
    return deepcopy(prototype)


def test_jim_raynor_orders_upgrade():
    marauder = muster("Marauder", {"! Orders / Jim Raynor": True})
    assert all(Tag.CriticalHit2 in weapon.tags for weapon in marauder.weapons)

    marine_prototype = next(unit for unit in ALL_UNITS if unit.name == "Marine")
    order_names = {upgrade.name for upgrade in marine_prototype.upgrades if upgrade.name.startswith("! Orders / Jim Raynor")}
    assert order_names == {
        "! Orders / Jim Raynor / C-14 rifle",
        "! Orders / Jim Raynor / AGG-12",
        "! Orders / Jim Raynor / Rocket Launcher",
        "! Orders / Jim Raynor / Strike/Bayonet",
    }

    marine = muster("Marine", {"! Orders / Jim Raynor / AGG-12": True})
    assert Tag.CriticalHit2 in next(weapon for weapon in marine.weapons if weapon.name == "AGG-12").tags
    assert all(Tag.CriticalHit2 not in weapon.tags for weapon in marine.weapons if weapon.name != "AGG-12")

    marine = muster("Marine", {"! Orders / Jim Raynor / Strike/Bayonet": True})
    assert all(Tag.CriticalHit2 in weapon.tags for weapon in marine.weapons if weapon.name in ("Strike", "Bayonet"))
    assert all(Tag.CriticalHit2 not in weapon.tags for weapon in marine.weapons if weapon.name not in ("Strike", "Bayonet"))

    marauder = clone("Marauder")
    marauder.weapons = (*marauder.weapons, Weapon("Charge", "C", Tag.Ground, 2, 4, None, None, 1))
    non_order_upgrades = tuple(upgrade for upgrade in marauder.upgrades if not upgrade.name.startswith("! Orders / Jim Raynor"))
    marauder.upgrades = (*non_order_upgrades, *apply_jim_raynors_orders(marauder))
    marauder = MusteredUnit.make(marauder, {"! Orders / Jim Raynor": True})
    assert all(Tag.CriticalHit2 in weapon.tags for weapon in marauder.weapons if weapon.type_letter != "C")
    assert all(Tag.CriticalHit2 not in weapon.tags for weapon in marauder.weapons if weapon.type_letter == "C")
