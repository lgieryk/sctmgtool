# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Łukasz Gieryk

from copy import deepcopy
from typing import NamedTuple

import pytest

from sctmgtool.base import Cost, Range, Squad
from sctmgtool.tools import ClashType, MusteredUnit, Tag, Upgrade, Weapon, process_unit_list, select_weapons
from sctmgtool.units import ALL_UNITS


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
    Case(ClashType.Charge, Tag.Ground, ("ChargeAbility", "MovementAbility")),
    Case(ClashType.CloseCombat, Tag.Ground, ("CloseCombat",)),
    Case(ClashType.Ranged, Tag.Ground, ("GroundRanged", "ComboRanged", "Ability")),
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
        Weapon("Ability", "A", Tag.Ground, 0, 0, None, None, 1, tags=Tag.Sidearm, flags=Weapon.Flags.SimulationProfile),
        Weapon(
            "ChargeAbility",
            "A",
            Tag.Ground,
            0,
            0,
            None,
            None,
            1,
            tags=Tag.Sidearm,
            flags=Weapon.Flags.SimulationProfile | Weapon.Flags.TriggeredByCharge,
        ),
        Weapon(
            "MovementAbility",
            "A",
            Tag.Ground,
            0,
            0,
            None,
            None,
            1,
            tags=Tag.Sidearm,
            flags=Weapon.Flags.SimulationProfile | Weapon.Flags.ResolvedInMovement,
        ),
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
        Weapon("Other Alternative", 10, Tag.Ground, 0, 0, None, None, 1, exchange_for="Default"),
        Weapon("Unselected", 10, Tag.Ground, 0, 0, None, None, 1),  # exchange_for intentionally omitted
        Weapon("Melee", "E", Tag.Ground, 0, 0, None, None, 1),
    )
    proto_marine.upgrades = (
        Upgrade("Alternative", Upgrade.activate_weapon),
        Upgrade("Other Alternative", Upgrade.activate_weapon),
    )

    def is_selected(unit: MusteredUnit, name: str):
        return any(batch.weapon.name == name for batch in unit.weapon_batches)

    marine = MusteredUnit.make(proto_marine, {"Alternative": True})
    assert is_selected(marine, "Melee")
    assert not is_selected(marine, "Default")
    assert is_selected(marine, "Alternative")
    assert not is_selected(marine, "AlternativeBad")

    marine = MusteredUnit.make(proto_marine, {"Alternative": True, "Other Alternative": True})
    assert is_selected(marine, "Alternative")
    assert not is_selected(marine, "Other Alternative")

    marine = MusteredUnit.make(proto_marine, {})
    assert is_selected(marine, "Melee")
    assert is_selected(marine, "Default")
    assert not is_selected(marine, "Alternative")
    assert not is_selected(marine, "AlternativeBad")


def test_simulated_ability_profile_can_use_official_upgrade_name():
    prototype = clone("Marine")
    prototype.weapons = (
        Weapon(
            "! Ability",
            "A",
            Tag.Ground,
            1,
            None,
            None,
            None,
            1,
            tags=Tag.Sidearm | Tag.Hits,
            flags=Weapon.Flags.SimulationProfile,
        ),
    )
    prototype.upgrades = (Upgrade("Ability", apply=lambda unit: unit.activate_weapon("! Ability")),)

    assert MusteredUnit.make(prototype, {}).batch("! Ability") is None
    assert MusteredUnit.make(prototype, {"Ability": True}).batch("! Ability") is not None


def test_mustered_unit_str_includes_squad_and_role_upgrade_points():
    prototype = clone("Marine")
    prototype.squad = (
        Squad(Range(4, 6), 1, 100),
        Squad(Range(7, 9), 2, 200),
    )
    prototype.upgrades = (
        Upgrade("Attack", {}, cost=Cost(20, 30, points=2), flags=Upgrade.Flags.TypeOffensive),
        Upgrade("Defense", {}, cost=Cost(40, 60, points=3), flags=Upgrade.Flags.TypeDefensive),
        Upgrade("Same cost", {}, cost=Cost(10), flags=Upgrade.Flags.TypeOffensive),
    )

    attacker_without_upgrades = MusteredUnit.make(prototype, {}, is_attacker=True)
    attacker = MusteredUnit.make(prototype, {"Attack": True, "Defense": True, "Same cost": True}, is_attacker=True)
    defender = MusteredUnit.make(prototype, {"_squad_size_def": 9, "Attack": True, "Defense": True}, is_attacker=False)

    assert str(attacker_without_upgrades) == "Marine SHLD:None EVA:5+ ARM:5+ HP:2 SIZ:2 Biological|Ground|Light (100 PTS)"
    assert str(attacker) == "Marine SHLD:None EVA:5+ ARM:5+ HP:2 SIZ:2 Biological|Ground|Light (130 PTS)"
    assert str(defender) == "Marine SHLD:None EVA:5+ ARM:5+ HP:2 SIZ:2 Biological|Ground|Light (260 PTS)"


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
    marine.upgrades = (
        *marine.upgrades,
        Upgrade("Useless", apply=lambda x: True),
        Upgrade("Workaround", apply=lambda x: True, flags=Upgrade.Flags.Workaround),
        Upgrade("Replaced", flags=Upgrade.Flags.TypeOther | Upgrade.Flags.ReplacedByWorkaround),
    )
    units = (clone("Zergling"), marine)

    def upgrade(unit, name: str):
        return next(upgrade for upgrade in unit.upgrades if upgrade.name == name)

    assert upgrade(marine, "Combat Shield").flags is Upgrade.Flags.TypeUnset

    processed_units = process_unit_list(units)
    processed_marine = next(unit for unit in processed_units if unit.name == "Marine")

    assert processed_units is not units
    assert processed_marine is not marine
    assert upgrade(marine, "Combat Shield").flags is Upgrade.Flags.TypeUnset
    assert Upgrade.Flags.ReplacedByWorkaround in upgrade(marine, "Replaced").flags
    assert not marine.has_upgrade("! Generic Evade-All")

    assert upgrade(processed_marine, "Combat Shield").flags == Upgrade.Flags.TypeDefensive
    assert upgrade(processed_marine, "Bayonet").flags == Upgrade.Flags.TypeOffensive
    assert upgrade(processed_marine, "Useless").flags == Upgrade.Flags.TypeOther
    assert upgrade(processed_marine, "Workaround").flags == Upgrade.Flags.TypeOther | Upgrade.Flags.Workaround
    assert not processed_marine.has_upgrade("Replaced")
    assert processed_marine.has_upgrade("! Generic Evade-All")
    assert upgrade(processed_marine, "! Generic Evade-All").flags == Upgrade.Flags.TypeDefensive | Upgrade.Flags.Workaround


def test_special_weapons_are_consistent():
    for unit in process_unit_list(ALL_UNITS):
        for weapon in unit.weapons:
            special_tags = (Tag.Hits, Tag.Impact, Tag.DirectDamage)
            active_special_tags = {tag for tag in special_tags if tag in weapon.tags}
            assert len(active_special_tags) <= 1 or active_special_tags == {Tag.Hits, Tag.DirectDamage}, (
                f"{unit.name}/{weapon.name}: only HITS and direct damage may be combined"
            )

            if Tag.Hits in weapon.tags:
                assert weapon.hit is None, f"{unit.name}/{weapon.name}: HITS must not have a Hit characteristic"
                assert weapon.surge is None and weapon.surge_die is None, f"{unit.name}/{weapon.name}: HITS cannot generate Surge"
            else:
                assert weapon.hit is not None, f"{unit.name}/{weapon.name}: missing Hit characteristic requires HITS"

            if Tag.Impact in weapon.tags:
                assert weapon.hit is not None, f"{unit.name}/{weapon.name}: IMPACT requires a Hit characteristic"
                assert weapon.damage == 1, f"{unit.name}/{weapon.name}: IMPACT must have Damage 1"
                assert weapon.surge is None and weapon.surge_die is None, f"{unit.name}/{weapon.name}: IMPACT cannot generate Surge"
            if Tag.DirectDamage in weapon.tags:
                assert weapon.surge is None and weapon.surge_die is None, f"{unit.name}/{weapon.name}: direct damage cannot generate Surge"
                assert weapon.tags.precision() == 0, f"{unit.name}/{weapon.name}: direct damage cannot have Precision"
                assert weapon.tags.critical_hit() == 0, f"{unit.name}/{weapon.name}: direct damage cannot have Critical Hit"
                assert weapon.tags.pierce_armoured() == 0 and weapon.tags.pierce_light() == 0, f"{unit.name}/{weapon.name}: direct damage cannot have Pierce"


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

    marine.debuff_armour(2)
    assert marine.armour == 4
    marine.debuff_armour(20)
    assert marine.armour == 6  # Cannot get above 6

    assert marine.evade == 5
    marine.buff_evade(1)
    assert marine.evade == 4
    marine.buff_evade(20)
    assert marine.evade == 2  # Cannot get below 2

    assert marine.hit_points == 2
    marine.buff_hit_points(4)
    assert marine.hit_points == 6
