# Files in this package (stcmgtool.units) are distributed under separate terms —
# see NOTICE.txt in this directory. They are NOT covered by the project's MIT
# License.

from sctmgtool.base import Cost, Faction, Hook, Range, Speed, Squad, SurgeDie, Tag, Unit, UnitType, Upgrade, Weapon


def _activate_shadow_strike_only(unit):
    if unit.batch("! Shadow Strike") is None:
        unit.activate_weapon("! Shadow Strike")

    master_warp_blade = unit.batch("Master Warp Blade")
    if master_warp_blade is not None:
        unit.weapon_batches.remove(master_warp_blade)


def _improved_barrier(_, __, damage):
    damage.value = min(damage.value, 1)


_PROTOSS_UNITS: tuple[Unit, ...] = (
    Unit(
        faction=Faction.Protoss,
        name="Adept",
        unit_type=UnitType.Core,
        size=2,
        keywords=(),
        shield=2,
        speed=Speed(5, 8),
        evade=5,
        armour=5,
        hit_points=3,
        weapons=(
            Weapon("Glaive Cannon", 8, Tag.Ground | Tag.Flying, 2, 3, Tag.Light, SurgeDie.D3P1, 1, tags=Tag.AntiEvade1),
            Weapon("Strike", "E", Tag.Ground, 1, 4, None, None, 1),
            Weapon("Glaive Strike", "E", Tag.Ground, 1, 4, Tag.Light, SurgeDie.D3, 1, tags=Tag.PierceLight2, exchange_for="Strike"),
        ),
        squad=(Squad(Range(3, 4), 1, 150),),
        tags=Tag.Biological | Tag.Light | Tag.Ground,
        upgrades=(
            Upgrade(
                "Resonating Glaives",
                cost=Cost(20, points=1),
                message="This Unit's Glaive Cannon gains BUFF RoA (1).",
                apply=lambda unit: unit.weapon("Glaive Cannon").buff_roa(1),
            ),
            Upgrade(
                "Guidance",
                cost=Cost(10),
                message="This Unit's Glaive Cannon Ranged weapon gains ANTI-EVADE (2).",
                apply=lambda unit: unit.weapon("Glaive Cannon").add_tag(Tag.AntiEvade2),
            ),
            Upgrade("Glaive Strike", cost=Cost(20), apply=Upgrade.activate_weapon),
            Upgrade("Psionic Presence", upgrade_type=Upgrade.Type.Other),
            Upgrade("Psionic Transfer", upgrade_type=Upgrade.Type.Other),
        ),
    ),
    Unit(
        faction=Faction.Protoss,
        name="Artanis",
        unit_type=UnitType.Hero,
        size=2,
        keywords=(),
        shield=4,
        speed=Speed(7, 7),
        evade=5,
        armour=4,
        hit_points=8,
        weapons=(
            Weapon("Twilight Blades Strike", "E", Tag.Ground, 2, 2, Tag.Armoured, SurgeDie.D3, 3),
            # Note: Sweep is actually always available, it's not a "for"
            Weapon("Twilight Blades Sweep", "E", Tag.Ground, 6, 2, Tag.Light, SurgeDie.D3P1, 1, exchange_for="Twilight Blades Strike"),
            Weapon("Devastating Charge", "C", Tag.Ground, 6, 4, None, None, 1),
        ),
        squad=(Squad(Range(1, 1), 1, 250),),
        tags=Tag.Biological | Tag.Psionic | Tag.Ground | Tag.Unique,
        upgrades=(
            Upgrade("Twilight Blades Sweep", Upgrade.activate_weapon),
            Upgrade("Commander", upgrade_type=Upgrade.Type.Other),
            Upgrade("Phase Prism", upgrade_type=Upgrade.Type.Other),
            Upgrade("Hierarch’s Stand", upgrade_type=Upgrade.Type.Other),
            Upgrade("Lightning Dash", upgrade_type=Upgrade.Type.Other),
        ),
    ),
    Unit(
        faction=Faction.Protoss,
        name="Immortal",
        unit_type=UnitType.Elite,
        size=3,
        keywords=(),
        shield=6,
        speed=Speed(7, 7),
        evade=None,
        armour=4,
        hit_points=8,
        weapons=(
            Weapon("Left Photon Disruptor", 12, Tag.Ground, 4, 3, Tag.Armoured, SurgeDie.D3, 2, tags=Tag.ConcentratedFire1),
            Weapon(
                "Right Photon Disruptor",
                12,
                Tag.Ground,
                4,
                3,
                Tag.Armoured,
                SurgeDie.D3,
                2,
                tags=Tag.Sidearm | Tag.ConcentratedFire1,
            ),
            Weapon(
                "Left Phase Disruptor",
                12,
                Tag.Ground,
                4,
                3,
                Tag.Armoured,
                SurgeDie.D3,
                1,
                tags=Tag.PierceArmoured3,
                exchange_for="Left Photon Disruptor",
            ),
            Weapon(
                "Right Phase Disruptor",
                12,
                Tag.Ground,
                4,
                3,
                Tag.Armoured,
                SurgeDie.D3,
                1,
                tags=Tag.Sidearm | Tag.PierceArmoured3,
                exchange_for="Right Photon Disruptor",
            ),
            Weapon("Stomp", "E", Tag.Ground, 3, 3, None, None, 1),
            Weapon("Devastating Charge", "C", Tag.Ground, 4, 3, None, None, 1),
        ),
        squad=(Squad(Range(1, 1), 2, 280),),
        tags=Tag.Mechanical | Tag.Ground | Tag.Armoured,
        upgrades=(
            Upgrade("Left Phase Disruptor", apply=Upgrade.activate_weapon),
            Upgrade("Right Phase Disruptor", apply=Upgrade.activate_weapon),
            Upgrade(
                "Shield Overcharge",
                message="Use before this Unit makes an Armour Roll. If this Unit has the Shielded Status, It gains TOUGH (2) for this roll.",
                cost=Cost(20, points=1),
                apply=lambda unit: unit.add_tag(Tag.Tough2),
                upgrade_type=Upgrade.Type.Defensive,
            ),
            Upgrade(
                "Improved Barrier",
                message="Use when this Unit is selected as the target of an attack. If this Unit has the Shielded Status, the Damage characteristic of the attacking weapon is treated as a maximum of 1 for this attack.",
                cost=Cost(),
                apply={Hook.ModifyDamage: _improved_barrier},
                upgrade_type=Upgrade.Type.Defensive,
            ),
            Upgrade(
                "Fury Unyielding",
                message='While this Unit is Within 3" of a Mission Marker, its Ranged Weapons gain CRITICAL HIT (1) when targeting an Enemy Unit that is also Within 3" of that same Mission Marker.',
                cost=Cost(20),
                apply=lambda unit: unit.weapon("@type_letter==R").add_tag(Tag.CriticalHit1),
            ),
            Upgrade(
                "For the Ancients",
                message='When this Unit makes a Ranged Attack, if the target Unit is more than 8" away, the attacking weapons gain PRECISION (1).',
                cost=Cost(20),
                apply=lambda unit: unit.weapon("@type_letter==R").add_tag(Tag.Precision1),
            ),
            Upgrade("Indomitable", upgrade_type=Upgrade.Type.Other),
        ),
    ),
    Unit(
        faction=Faction.Protoss,
        name="Nerazim Watchers (Adept)",
        unit_type=UnitType.Core,
        size=2,
        keywords=("Protoss", "Nerazim"),
        shield=2,
        speed=Speed(5, 8),
        evade=5,
        armour=5,
        hit_points=3,
        weapons=(
            Weapon("Glaive Cannon", 8, Tag.Ground | Tag.Flying, 3, 3, Tag.Light, SurgeDie.D3P1, 1, tags=Tag.AntiEvade1 | Tag.Pinpoint),
            Weapon("Strike", "E", Tag.Ground, 1, 5, None, None, 1),
        ),
        squad=(Squad(Range(3, 4), 1, 210),),
        tags=Tag.Biological | Tag.Ground | Tag.Light,
        upgrades=(
            Upgrade("Path of Shadows", upgrade_type=Upgrade.Type.Other),
            Upgrade("Nerazim Farsight", upgrade_type=Upgrade.Type.Other),
            Upgrade("Psionic Transfer", upgrade_type=Upgrade.Type.Other),
        ),
    ),
    Unit(
        faction=Faction.Protoss,
        name="Praetor Guard (Zealot)",
        unit_type=UnitType.Elite,
        size=2,
        keywords=("Khalai",),
        shield=3,
        speed=Speed(4, 7),
        evade=5,
        armour=5,
        hit_points=4,
        weapons=(
            Weapon("Psi Blades", "E", Tag.Ground, 4, 3, Tag.Light, SurgeDie.D3, 1),
            Weapon("Devastating Charge", "C", Tag.Ground, 3, 4, None, None, 1),
        ),
        squad=(Squad(Range(2, 3), 2, 280),),
        tags=Tag.Biological | Tag.Light | Tag.Ground | Tag.Unique,
        upgrades=(
            Upgrade(
                "Shield Overcharge",
                cost=Cost(0),
                message="This Unit gains TOUGH (2) on the first Armour Roll each Round.",
                apply=lambda unit: unit.add_tag(Tag.Tough2),
            ),
            Upgrade(
                "Titan Killers",
                cost=Cost(0),
                message="When this Unit makes a Close Combat Attack, and the target is Size 3 or larger, the weapon’s Damage characteristic is treated as 2.",
                apply=lambda unit: unit.weapon("@range==E").set_damage(2),
            ),
            Upgrade(
                "Precognition",
                cost=Cost(0),
                message="This Unit is eligible to make an Evade roll against all attacks targeting it.",
                apply=lambda unit: unit.grant_reroll("REC"),
            ),
            Upgrade("Leg Enhancements", upgrade_type=Upgrade.Type.Other),
            Upgrade("Charge", upgrade_type=Upgrade.Type.Other),
        ),
    ),
    Unit(
        faction=Faction.Protoss,
        name="Pylon",
        unit_type=UnitType.Other,
        size=3,
        keywords=("Khalai",),
        shield=2,
        speed=Speed(0, 0),
        evade=None,
        armour=5,
        hit_points=8,
        weapons=(),
        squad=(Squad(Range(1, 1), 0, 0),),
        tags=Tag.Armoured | Tag.Ground,
        upgrades=(
            Upgrade("Structure", upgrade_type=Upgrade.Type.Other),
            Upgrade("Khalai Ingenuity", upgrade_type=Upgrade.Type.Other),
            Upgrade("Warp Conduit", upgrade_type=Upgrade.Type.Other),
        ),
    ),
    Unit(
        faction=Faction.Protoss,
        name="Sentry",
        unit_type=UnitType.Support,
        size=1,
        keywords=(),
        shield=2,
        speed=Speed(4, 7),
        evade=6,
        armour=5,
        hit_points=4,
        weapons=(
            Weapon("Disruption Beam", 8, Tag.Ground | Tag.Flying, 2, 2, None, None, 1, tags=Tag.Instant),
            Weapon("Beam", "E", Tag.Ground, 2, 3, None, None, 1),
        ),
        squad=(Squad(Range(2, 2), 1, 130),),
        tags=Tag.Light | Tag.Mechanical | Tag.Psionic | Tag.Ground,
        upgrades=(
            Upgrade("Restoration", upgrade_type=Upgrade.Type.Other),
            Upgrade("Force Field", upgrade_type=Upgrade.Type.Other),
            Upgrade("Guardian Shield", upgrade_type=Upgrade.Type.Other),
            Upgrade("Solid-Field Projectors", upgrade_type=Upgrade.Type.Other),
            Upgrade("Hallucination", upgrade_type=Upgrade.Type.Other),
        ),
    ),
    Unit(
        faction=Faction.Protoss,
        name="Stalker",
        unit_type=UnitType.Elite,
        size=3,
        keywords=(),
        shield=3,
        speed=Speed(4, 8),
        evade=6,
        armour=4,
        hit_points=6,
        weapons=(
            Weapon("Particle Disruptors", 12, Tag.Ground | Tag.Flying, 4, 3, Tag.Armoured, SurgeDie.D3, 2),
            Weapon("Stomp", "E", Tag.Ground, 2, 5, None, None, 1),
        ),
        squad=(
            Squad(Range(1, 1), 1, 170),
            Squad(Range(2, 2), 2, 270),
        ),
        tags=Tag.Armoured | Tag.Mechanical | Tag.Ground,
        upgrades=(
            Upgrade("Squadron", upgrade_type=Upgrade.Type.Other),
            Upgrade("Path of Shadows", upgrade_type=Upgrade.Type.Other),
            Upgrade("Blink", upgrade_type=Upgrade.Type.Other),
            Upgrade("Fury of the Nerazim", upgrade_type=Upgrade.Type.Other),
        ),
    ),
    Unit(
        faction=Faction.Protoss,
        name="Zealot",
        unit_type=UnitType.Core,
        size=2,
        keywords=(),
        shield=3,
        speed=Speed(4, 7),
        evade=5,
        armour=5,
        hit_points=4,
        weapons=(
            Weapon("Psi Blades", "E", Tag.Ground, 4, 3, Tag.Light, SurgeDie.D3, 1),
            Weapon("Devastating Charge", "C", Tag.Ground, 3, 4, None, None, 1),
        ),
        squad=(Squad(Range(2, 3), 2, 160),),
        tags=Tag.Biological | Tag.Light | Tag.Ground,
        upgrades=(
            Upgrade(
                "We Stand as One",
                cost=Cost(20),
                message="When this Unit makes a Close Combat Attack, if the target is Engaged with at least 1 other Friendly Unit, this Unit's Close Combat Weapon gains PRECISION (2).",
                apply=lambda unit: unit.weapon("@range==E").add_tag(Tag.Precision2),
            ),
            Upgrade(
                "My Life for Aiur",
                cost=Cost(10),
                message="When this Unit resolves IMPACT, each eligible model generates 1 additional IMPACT die.",
                apply=lambda unit: unit.weapon("@range==C").buff_roa(1),
            ),
            Upgrade("Leg Enhancements", upgrade_type=Upgrade.Type.Other),
            Upgrade("Charge", upgrade_type=Upgrade.Type.Other),
            Upgrade("Zealous Round", upgrade_type=Upgrade.Type.Other),
        ),
    ),
    Unit(
        faction=Faction.Protoss,
        name="Zeratul",
        unit_type=UnitType.Hero,
        size=2,
        keywords=(),
        shield=3,
        speed=Speed(7, 7),
        evade=5,
        armour=5,
        hit_points=5,
        weapons=(
            Weapon("Master Warp Blade", "E", Tag.Ground, 4, 3, Tag.Light | Tag.Armoured, SurgeDie.D3, 2, tags=Tag.Instant),
            Weapon("! Shadow Strike", "E", Tag.Ground, 4, "!", None, None, 1, tags=Tag.Sidearm),
            Weapon("Devastating Charge", "C", Tag.Ground, 4, 4, None, None, 1),
        ),
        squad=(Squad(Range(1, 1), 1, 230),),
        tags=Tag.Biological | Tag.Ground | Tag.Psionic | Tag.Unique,
        upgrades=(
            Upgrade("One With the Shadows", upgrade_type=Upgrade.Type.Other),
            Upgrade(
                "Prophetic Vision",
                message="REPEATABLE. Use when this Unit is selected as the target of an attack. This Unit's Evade characteristic is treated as 4+ against this attack and cannot be modified.",
                cost=Cost(points=1),
                apply=lambda unit: unit.grant_reroll("REC") or unit.buff_evade(1),
                upgrade_type=Upgrade.Type.Defensive,
            ),
            Upgrade(
                "Sentenced to Death",
                message="Target Enemy Unit on the battlefield. Whenever Zeratul makes a Close Combat Attack targeting the selected Unit, its weapon gains CRITICAL HIT (2).",
                cost=Cost(points=1),
                apply=lambda unit: unit.weapon("Master Warp Blade").add_tag(Tag.CriticalHit2),
                upgrade_type=Upgrade.Type.Offensive,
            ),
            Upgrade("Void Prison", upgrade_type=Upgrade.Type.Other),
            Upgrade("Void Blink", upgrade_type=Upgrade.Type.Other),
            Upgrade(
                "! Shadow Strike",
                message="All Enemy Units Engaged with this Unit suffer HITS 4 (1).",
                cost=Cost(points=1),
                apply=Upgrade.activate_weapon,
            ),
            Upgrade("! Shadow Strike (2)", _activate_shadow_strike_only, message="Use instead of Master Warp Blade.", cost=Cost(points=1)),
        ),
    ),
)


def _guardian_shield_effect(_, roll, pools):
    if roll.weapon_batch.weapon.type_letter == "R":
        pools.attack_pool.transfer_dice_to(pools.discard_pool, up_to=1)


def _psionic_presence_effect(unit):
    for weapon in unit.weapons:
        if weapon.type_letter != "C" and weapon.hit != "!":
            weapon.add_tag(Tag.Precision1)


def _apply_common_skills(units):
    guardian_shield = Upgrade(
        "! Guardian Shield / Sentry",
        message='Apply active GS of a friendly Sentry unit within 4" - All Ranged Attacks are made with 1 fewer die in the Attack Pool.',
        upgrade_type=Upgrade.Type.Defensive,
        apply={Hook.RollPoolsInitiated: _guardian_shield_effect},
    )

    psionic_presence = Upgrade(
        "! Psionic Presence / Adept",
        message="Apply PP of a friendly Adept's Shade token within 4\" - All Ranged and Close Combat weapons gain PRECISION (1)",
        apply=_psionic_presence_effect,
    )

    for unit in units:
        if unit.is_structure:
            continue

        unit.upgrades = (*unit.upgrades, guardian_shield, psionic_presence)

    return units


PROTOSS_UNITS = _apply_common_skills(_PROTOSS_UNITS)
