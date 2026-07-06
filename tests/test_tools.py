# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Łukasz Gieryk

from typing import NamedTuple
from copy import deepcopy
import pytest
from sctmgtool.units import ALL_UNITS
from sctmgtool.tools import Weapon, Tag, MusteredUnit, ClashType, Upgrade
from sctmgtool.tools import select_weapons, process_unit_list


def muster(name: str, config=None):
    prototype = next(u for u in ALL_UNITS if u.name == name)
    return MusteredUnit.make(prototype, config or {})


def clone(name: str):
    prototype = next(u for u in ALL_UNITS if u.name == name)
    return deepcopy(prototype)


class Case(NamedTuple):
    clash_type: ClashType
    enemy_type: Tag
    expected: tuple[str]

    def __str__(self):
        return f"{self.clash_type.name}-{self.enemy_type.name}"


cases = (
    Case(ClashType.Charge, Tag.Ground, ("Charge",)),
    Case(ClashType.CloseCombat, Tag.Ground, ("CloseCombat",)),
    Case(ClashType.Ranged, Tag.Ground, ("GroundRanged", "ComboRanged")),
    Case(ClashType.Charge, Tag.Flying, ()),
    Case(ClashType.CloseCombat, Tag.Flying, ()),
    Case(ClashType.Ranged, Tag.Flying, ("FlyingRanged", "ComboRanged")),
)


@pytest.mark.parametrize("case", cases, ids=str)
def test_select_weapons(case: Case):
    proto_marine = clone("Marine")
    proto_marine.weapons = (
        Weapon("FlyingRanged", 10, Tag.Flying, 0, 0, None, None, 1),
        Weapon("GroundRanged", 10, Tag.Ground, 0, 0, None, None, 1, tags=Tag.Sidearm),
        Weapon("ComboRanged", 10, Tag.Ground | Tag.Flying, 0, 0, None, None, 1, tags=Tag.Sidearm),
        Weapon("CloseCombat", "E", Tag.Ground, 0, 0, None, None, 1),
        Weapon("Charge", "C", Tag.Ground, 0, 0, None, None, 1),
    )

    attacker = MusteredUnit.make(proto_marine, {})
    defender = muster("Zergling")
    defender.tags = case.enemy_type

    selected = select_weapons(attacker, defender, case.clash_type)
    assert len(selected) == len(case.expected)
    for e in case.expected:
        assert any(batch.weapon.name == e for batch in selected)


def test_muster_weapons():
    proto_marine = clone("Marine")
    proto_marine.weapons = (
        Weapon("Default", 10, Tag.Ground, 0, 0, None, None, 1),
        Weapon("Sidearm", 10, Tag.Ground, 0, 0, None, None, 1, tags=Tag.Sidearm),
        Weapon("Alternative", 10, Tag.Ground, 0, 0, None, None, 1, exchange_for="Default"),
        Weapon("Unselected", 10, Tag.Ground, 0, 0, None, None, 1),  # exchange_for intentionally omitted
        Weapon("Melee", "E", Tag.Ground, 0, 0, None, None, 1),
    )
    proto_marine.upgrades = (Upgrade("Alternative", Upgrade.activate_weapon),)

    def is_selected(unit: MusteredUnit, name: str):
        return any(batch.weapon.name == name for batch in unit.weapon_batches)

    marine = MusteredUnit.make(proto_marine, {"Alternative": True})
    assert is_selected(marine, "Melee")
    assert not is_selected(marine, "Default")
    assert is_selected(marine, "Alternative")
    assert not is_selected(marine, "AlternativeBad")

    marine = MusteredUnit.make(proto_marine, {})
    assert is_selected(marine, "Melee")
    assert is_selected(marine, "Default")
    assert not is_selected(marine, "Alternative")
    assert not is_selected(marine, "AlternativeBad")


def test_query():
    proto_marine = clone("Marine")
    proto_marine.weapons = (
        Weapon("Default", 10, Tag.Ground, 2, 0, None, None, 1),
        Weapon("Melee", "E", Tag.Ground, 1, 0, None, None, 1),
    )
    proto_marine.upgrades = (
        Upgrade("AddTag", apply=lambda unit: unit.weapon(["Default", "@range==E"]).add_tag(Tag.Precision3)),
        Upgrade("BuffRoa", apply=lambda unit: unit.weapon("Default").buff_roa(5)),
        Upgrade("SetDmg", apply=lambda unit: unit.weapon("*").set_damage(4)),
    )

    def weapon(unit: MusteredUnit, name: str):
        return next(batch.weapon for batch in unit.weapon_batches if batch.weapon.name == name)

    marine = MusteredUnit.make(proto_marine, {})
    assert Tag.Precision3 not in weapon(marine, "Default").tags
    assert Tag.Precision3 not in weapon(marine, "Melee").tags

    marine = MusteredUnit.make(proto_marine, {"AddTag": True})
    assert Tag.Precision3 in weapon(marine, "Default").tags
    assert Tag.Precision3 in weapon(marine, "Melee").tags

    marine = MusteredUnit.make(proto_marine, {"BuffRoa": False})
    assert weapon(marine, "Default").rate_of_attack == 2
    assert weapon(marine, "Melee").rate_of_attack == 1
    marine = MusteredUnit.make(proto_marine, {"BuffRoa": True})
    assert weapon(marine, "Default").rate_of_attack == 7
    assert weapon(marine, "Melee").rate_of_attack == 1

    marine = MusteredUnit.make(proto_marine, {"SetDmg": False})
    assert weapon(marine, "Default").damage == 1
    assert weapon(marine, "Melee").damage == 1
    marine = MusteredUnit.make(proto_marine, {"SetDmg": True})
    assert weapon(marine, "Default").damage == 4
    assert weapon(marine, "Melee").damage == 4


def test_num_killed():
    proto_marine = clone("Marine")

    proto_marine.shield = 0
    proto_marine.hit_points = 10
    marine = MusteredUnit.make(proto_marine, {})
    assert marine.num_killed(15) == 1
    assert marine.num_killed(20) == 2

    proto_marine.shield = 6
    proto_marine.hit_points = 10
    marine = MusteredUnit.make(proto_marine, {})
    assert marine.num_killed(15) == 0
    assert marine.num_killed(16) == 1
    assert marine.num_killed(25) == 1
    assert marine.num_killed(26) == 2


def test_process_units():
    marine = clone("Marine")
    marine.upgrades = (*marine.upgrades, Upgrade("Useless", apply=lambda x: True))
    units = (clone("Zergling"), marine)

    def upgrade(name: str):
        return next(upgrade for upgrade in marine.upgrades if upgrade.name == name)

    assert upgrade("Combat Shield").upgrade_type is None
    process_unit_list(units)
    assert upgrade("Combat Shield").upgrade_type == Upgrade.Type.Defensive
    assert upgrade("Bayonet").upgrade_type == Upgrade.Type.Offensive
    assert upgrade("Useless").upgrade_type == Upgrade.Type.Other


def test_unit_buff():
    marine = muster("Marine")

    marine.tags = Tag.Flying
    marine.add_tag(Tag.Unique | Tag.AntiEvade1)
    assert marine.tags == Tag.Unique | Tag.AntiEvade1 | Tag.Flying

    assert marine.armour == 5
    marine.buff_armour(2)
    assert marine.armour == 3
    marine.buff_armour(2)
    assert marine.armour == 2  # Cannot get below 2

    assert marine.evade == 5
    marine.buff_evade(1)
    assert marine.evade == 4
    marine.buff_evade(20)
    assert marine.evade == 2  # Cannot get below 2

    assert marine.hit_points == 2
    marine.buff_hit_points(4)
    assert marine.hit_points == 6
