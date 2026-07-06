# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Łukasz Gieryk

from sctmgtool.base import Tag, Weapon, SurgeDie, Speed, Cost, Upgrade, Unit, Faction


def test_tag():
    all_getters = (Tag.anti_evade, Tag.precision, Tag.pierce_armoured, Tag.pierce_light, Tag.tough)

    def validate(tag: Tag, expected: map):
        for getter in all_getters:
            assert getter(tag) == expected.get(getter, 0)

    validate(Tag.Tough1, {Tag.tough: 1})
    validate(Tag.AntiEvade1, {Tag.anti_evade: 1})
    validate(Tag.AntiEvade3, {Tag.anti_evade: 3})
    validate(Tag.PierceArmoured2, {Tag.pierce_armoured: 2})
    validate(Tag.PierceLight2, {Tag.pierce_light: 2})
    validate(Tag.CriticalHit2, {Tag.critical_hit: 2})

    tag = Tag.Tough1 | Tag.PierceArmoured2
    expected = {Tag.tough: 1, Tag.pierce_armoured: 2}
    validate(tag, expected)

    s = str(tag)
    s = s.replace("Tough1", "")
    s = s.replace("PierceArmoured2", "")
    assert s == "|"


def test_tag_sibling_bits():
    bits = Tag.AntiEvade1.sibling_bits()
    combined = Tag.AntiEvade1 | Tag.AntiEvade2 | Tag.AntiEvade3
    assert bits == combined.value


def test_weapon():
    w = Weapon("Dummy", 0, Tag.Flying | Tag.Ground, 7, 3, None, None, 1, tags=Tag.AntiEvade1)

    assert w.tags.anti_evade() == 1
    w.add_tag(Tag.AntiEvade3)
    assert w.tags.anti_evade() == 3

    assert w.rate_of_attack == 7
    w.buff_roa(4)
    assert w.rate_of_attack == 11

    assert w.surge_die is None
    w.set_surge_die(SurgeDie.D6)
    assert w.surge_die == SurgeDie.D6

    assert w.surge is None
    w.add_surge_tag(Tag.Precision1)
    assert w.surge == Tag.Precision1
    w.add_surge_tag(Tag.Precision2)
    # TODO: this is not necessarily an intuitive outcome...
    assert w.surge == Tag.Precision2 | Tag.Precision1

    assert w.damage == 1
    w.set_damage(5)
    assert w.damage == 5

    assert w.hit == 3
    w.buff_hit(1)
    assert w.hit == 2
    w.buff_hit(1)
    assert w.hit == 2  # Cannot get below 2


def test_str():
    weapon = Weapon("name", "range", Tag.Ground, 11, 22, Tag.Light, SurgeDie.D3, 33, "for", Tag.AntiEvade1)
    assert str(weapon) == "name                           range G  11D6 22+  Light            D3   DMG:33 AntiEvade1           FOR:for"

    s_die = SurgeDie.D3P1
    assert str(s_die) == "D3P1"

    speed = Speed(5, 6)
    assert str(speed) == "5/6"

    cost = Cost(11, 22, points=33)
    assert str(cost) == "11/22/33P"

    assert str(Upgrade("upgrade", {}, message="message", cost=cost)) == "upgrade 11/22/33P message"

    unit = Unit(Faction.Terran, "name", 1, speed, 2, 3, 4, (weapon,), (), Tag.Unique, ())
    assert str(unit) == "name SHLD:1 EVA:2+ ARM:3+ HP:4 Unique"
