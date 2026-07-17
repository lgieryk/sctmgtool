# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Łukasz Gieryk

from unittest.mock import patch
from sctmgtool.base import SurgeDie
from sctmgtool.units import TERRAN_UNITS
from sctmgtool.tools import Weapon, WeaponBatch, Tag, MusteredUnit, DicePool, HookContext
from sctmgtool.tools import roll_damage, roll_surge
from sctmgtool.base import Unit, Range, Squad, Upgrade, Hook


def muster(name: str, config=None):
    prototype = next(u for u in TERRAN_UNITS if u.name == name)
    return MusteredUnit.make(prototype, config or {})


def loaded_die(val: int):
    def _wrap(_, k):
        return [val] * k

    return _wrap


def test_dice_pool():
    a = DicePool((1, 6))
    assert str(a) == "2D6: 1, 6"

    a.extend([5])
    assert str(a) == "3D6: 1, 6, 5"

    b = DicePool.n_dice(3)
    assert str(b) == "3D6: 0, 0, 0"

    a.transfer_dice_to(b, lambda x: x > 3)
    assert str(a) == "1D6: 1"
    assert str(b) == "5D6: 0, 0, 0, 6, 5"


def test_roll_surge():
    marine = muster("Marine")

    with patch("random.choices", side_effect=loaded_die(2)):
        anti_light = Weapon("Light", 0, Tag.Flying, 0, 0, Tag.Light, SurgeDie.D3, 1)
        assert roll_surge(anti_light, marine) == 1

    anti_armour = Weapon("Armoured", 0, Tag.Ground, 0, 0, Tag.Armoured, SurgeDie.D3, 1)
    assert roll_surge(anti_armour, marine) == 0

    anti_light2 = Weapon("Light", 0, Tag.Flying, 0, 0, Tag.Light, SurgeDie.D3P1, 1)
    for _ in range(100):
        assert roll_surge(anti_light2, marine) > 1

    with patch("random.choices", side_effect=loaded_die(6)):
        assert roll_surge(anti_light2, marine) == 4

    with patch("random.choices", side_effect=loaded_die(5)):
        assert roll_surge(anti_light2, marine) == 4

    with patch("random.choices", side_effect=loaded_die(4)):
        assert roll_surge(anti_light2, marine) == 3


def test_roll_damage():
    marine = muster("Marine")

    with patch("random.choices", side_effect=loaded_die(3)):
        # Hit on 4+ -> guaranteed 0 hits
        batch = WeaponBatch(4, Weapon("Light", 12, Tag.Ground, 4, 4, Tag.Light, SurgeDie.D3, 1))
        assert roll_damage(None, batch, marine) == 0

        # Hit on 3+ and Armour on 4+ -> all hits land
        batch = WeaponBatch(4, Weapon("Light", 12, Tag.Ground, 4, 3, Tag.Light, SurgeDie.D3, 1))
        marine.armour = 4
        assert roll_damage(None, batch, marine) == 16

        # Hit on 3+ and Armour on 4+ -> all hits land with 3 damage
        batch = WeaponBatch(4, Weapon("Light", 12, Tag.Ground, 4, 3, Tag.Light, SurgeDie.D3, 3))
        marine.armour = 4
        assert roll_damage(None, batch, marine) == 16 * 3

        # Hit on 3+ and Armour on 3+ -> all hits land and all are blocked - except for surge
        batch = WeaponBatch(4, Weapon("Light", 12, Tag.Ground, 4, 3, Tag.Light, SurgeDie.D3, 1))
        marine.armour = 3
        assert roll_damage(None, batch, marine) == 2

        # Hit on 3+ and Armour on 3+ -> all hits land and all are blocked - except for surge with multiplier
        batch = WeaponBatch(4, Weapon("Light", 12, Tag.Ground, 4, 3, Tag.Light, SurgeDie.D3P1, 2))
        marine.armour = 3
        assert roll_damage(None, batch, marine) == 3 * 2

    with patch("random.choices", side_effect=loaded_die(6)):
        # Hit on 3+ and Armour on 3+ -> all hits land and all are blocked - except for surge
        batch = WeaponBatch(4, Weapon("Light", 12, Tag.Ground, 4, 3, Tag.Light, SurgeDie.D3, 1))
        marine.armour = 3
        assert roll_damage(None, batch, marine) == 3

        # The same case, but with D6 surge
        batch = WeaponBatch(4, Weapon("Light", 12, Tag.Ground, 4, 3, Tag.Light, SurgeDie.D6, 1))
        marine.armour = 3
        assert roll_damage(None, batch, marine) == 6


def test_evade():
    marine = muster("Marine")

    with patch("random.choices", side_effect=loaded_die(3)):
        # Hit on 3+ and Armour on 4+ -> all hits land
        batch = WeaponBatch(4, Weapon("Ranged", 12, Tag.Ground, 4, 3, None, None, 1))
        marine.armour = 4
        assert roll_damage(None, batch, marine) == 16

        # Hit on 3+ and Armour on 4+ -> all hits land but are completely evaded with 3+
        batch = WeaponBatch(4, Weapon("Ranged", 12, Tag.Ground, 4, 3, None, None, 1))
        marine.armour = 4
        marine.evade = 3
        marine.evade_reroll = "REC"
        assert roll_damage(None, batch, marine) == 0

        # Defender does not have reroll against Ranged
        marine.evade_reroll = "EC"
        assert roll_damage(None, batch, marine) == 16

        # Update weapon type to see if reroll works again
        batch = WeaponBatch(4, Weapon("Charge", "C", Tag.Ground, 4, 3, None, None, 1))
        assert roll_damage(None, batch, marine) == 0

        # Failure to evade due to 4+
        batch = WeaponBatch(4, Weapon("Charge", "C", Tag.Ground, 4, 3, None, None, 1))
        marine.evade = 4
        assert roll_damage(None, batch, marine) == 16

    with patch("random.choices", side_effect=loaded_die(6)):
        # Anti-evade changes 6+ to 7+ but 6 are still successes guaranteeing 100% evades
        batch = WeaponBatch(4, Weapon("Ranged", 12, Tag.Ground, 4, 3, None, None, 1, tags=Tag.AntiEvade1))
        marine.evade = 6
        marine.evade_reroll = "REC"
        assert roll_damage(None, batch, marine) == 0

        # As above, but with 4+3
        batch = WeaponBatch(4, Weapon("Ranged", 12, Tag.Ground, 4, 3, None, None, 1, tags=Tag.AntiEvade3))
        marine.evade = 4
        assert roll_damage(None, batch, marine) == 0


def test_pierce():
    marine = muster("Marine")

    with patch("random.choices", side_effect=loaded_die(3)):
        # Incompatible pierce, expect the default damage multiplier
        batch = WeaponBatch(4, Weapon("Armoured", 12, Tag.Ground, 4, 3, None, None, 1, tags=Tag.PierceArmoured3))
        marine.armour = 4
        marine.tags = Tag.Light
        assert roll_damage(None, batch, marine) == 16

        # Pierce matches
        marine.tags = Tag.Armoured
        assert roll_damage(None, batch, marine) == 16 * 3

        # Repeat for the Light pierce
        batch = WeaponBatch(4, Weapon("Light", 12, Tag.Ground, 4, 3, None, None, 1, tags=Tag.PierceLight2))
        assert roll_damage(None, batch, marine) == 16

        marine.tags = Tag.Light
        assert roll_damage(None, batch, marine) == 16 * 2


def test_tough():
    marine = muster("Marine")

    with patch("random.choices", side_effect=loaded_die(3)):
        # Hit on 3+ and Armour on 4+ -> all hits land
        batch = WeaponBatch(4, Weapon("Light", 12, Tag.Ground, 2, 1, None, None, 2))
        marine.armour = 7
        marine.tags = Tag(0)
        assert roll_damage(None, batch, marine) == 8 * 2

        # A tough marine discards one die automatically
        marine.tags = Tag.Tough1
        assert roll_damage(None, batch, marine) == 7 * 2


def test_precision():
    marine = muster("Marine")

    with patch("random.choices", side_effect=loaded_die(3)):
        # Hit on 4+ -> nothing shall hit, even with ineffective 4+ armour
        batch = WeaponBatch(4, Weapon("Light", 12, Tag.Ground, 2, 4, None, None, 2))
        marine.armour = 4
        assert roll_damage(None, batch, marine) == 0

        # A Precise weapon always hits with N dies
        batch = WeaponBatch(4, Weapon("Light", 12, Tag.Ground, 2, 4, None, None, 2, tags=Tag.Precision1))
        assert roll_damage(None, batch, marine) == 1 * 2

        batch = WeaponBatch(4, Weapon("Light", 12, Tag.Ground, 2, 4, None, None, 2, tags=Tag.Precision3))
        assert roll_damage(None, batch, marine) == 3 * 2

        # With surge even the invincible 3+ armour gives up; precision limits the surge
        batch = WeaponBatch(4, Weapon("Light", 12, Tag.Ground, 2, 4, Tag.Light, SurgeDie.D3P1, 2, tags=Tag.Precision2))
        marine.armour = 3
        assert roll_damage(None, batch, marine) == 2 * 2


def test_critical_hit():
    marine = muster("Marine")

    with patch("random.choices", side_effect=loaded_die(3)):
        # Hit on 3+ and Armour on 3+ -> all hits land but are blocked on armour
        batch = WeaponBatch(4, Weapon("Light", 12, Tag.Ground, 2, 3, None, None, 2))
        marine.armour = 3
        marine.tags = Tag(0)
        assert roll_damage(None, batch, marine) == 0

        # A precise weapon bypasses invincible armour
        batch.weapon.tags = Tag.CriticalHit2
        assert roll_damage(None, batch, marine) == 2 * 2


def test_hooks():
    def pool_hook(_, __, pool):
        pool.attack_pool.transfer_dice_to(pool.discard_pool, up_to=6)

    weapon = Weapon("Weapon", 12, Tag.Ground, 8, 3, None, None, 1)
    prototype = Unit(
        faction=None,
        name="Unit",
        shield=None,
        speed=None,
        evade=6,
        armour=6,
        hit_points=5,
        weapons=(weapon,),
        squad=(Squad(Range(1, 1), 1, 0),),
        tags=Tag.Ground,
        upgrades=(Upgrade("Upgrade", apply={Hook.RollPoolsInitiated: pool_hook}),),
    )

    with patch("random.choices", side_effect=loaded_die(3)):
        # Hit on 3+ and Armour on 6+ -> all hits land and are not blocked
        unit = MusteredUnit.make(prototype, {})
        ctx = HookContext(unit)
        batch = WeaponBatch(1, weapon)
        assert roll_damage(None, batch, unit, ctx=ctx) == 8

        # The upgrade with a roll hook cancels 6 of the dice
        unit = MusteredUnit.make(prototype, {"Upgrade": True})
        ctx = HookContext(unit)
        batch = WeaponBatch(1, weapon)
        assert roll_damage(None, batch, unit, ctx=ctx) == 2
