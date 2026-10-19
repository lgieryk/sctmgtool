# Files in this package (stcmgtool.units) are distributed under separate terms —
# see NOTICE.txt in this directory. They are NOT covered by the project's MIT
# License.

from sctmgtool.base import Cost, Faction, Hook, Range, Speed, Squad, SurgeDie, Tag, Unit, UnitType, Upgrade, Weapon


def _activate_psionic_ability_only(unit, ability):
    if unit.batch(ability) is None:
        unit.activate_weapon(ability)

    psi_blast = unit.batch("Psi Blast")
    if psi_blast is not None:
        unit.weapon_batches.remove(psi_blast)


def _activate_shadow_strike_only(unit):
    if unit.batch("! Shadow Strike") is None:
        unit.activate_weapon("! Shadow Strike")

    master_warp_blade = unit.batch("Master Warp Blade")
    if master_warp_blade is not None:
        unit.weapon_batches.remove(master_warp_blade)


def _improved_barrier(_, __, damage):
    damage.value = min(damage.value, 1)


def _buff_roa_for_impact_weapons(unit):
    for weapon in unit.weapons:
        if Tag.Impact in weapon.tags:
            weapon.buff_roa(1)


def _our_minds_as_one(unit):
    has_supply_two = any(squad.models.start <= unit.models <= squad.models.stop and squad.supply == 2 for squad in unit.squad)
    if has_supply_two:
        unit.weapon(["! Psionic Storm / Movement phase", "! Psionic Storm / Assault phase"]).buff_hit(1)


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
            Upgrade(
                "Psionic Presence",
                message='All Weapons of Friendly Units targeting an Enemy Unit Within 4" of this Unit’s Shade token gain PRECISION (1).',
                cost=Cost(),
                flags=Upgrade.Flags.TypeOther | Upgrade.Flags.ReplacedByWorkaround,
            ),
            Upgrade("Psionic Transfer", flags=Upgrade.Flags.TypeOther),
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
            Weapon(
                "! Devastating Charge",
                "A",
                Tag.Ground,
                6,
                4,
                None,
                None,
                1,
                tags=Tag.Impact,
                flags=Weapon.Flags.SimulationProfile | Weapon.Flags.TriggeredByCharge,
            ),
        ),
        squad=(Squad(Range(1, 1), 1, 250),),
        tags=Tag.Biological | Tag.Psionic | Tag.Ground | Tag.Unique,
        upgrades=(
            Upgrade("Twilight Blades Sweep", Upgrade.activate_weapon),
            Upgrade("Commander", flags=Upgrade.Flags.TypeOther),
            Upgrade("Phase Prism", flags=Upgrade.Flags.TypeOther),
            Upgrade("Hierarch’s Stand", flags=Upgrade.Flags.TypeOther),
            Upgrade("Lightning Dash", flags=Upgrade.Flags.TypeOther),
        ),
    ),
    Unit(
        faction=Faction.Protoss,
        name="High Templar",
        unit_type=UnitType.Support,
        size=2,
        keywords=(),
        shield=3,
        speed=Speed(4, 7),
        evade=6,
        armour=5,
        hit_points=3,
        weapons=(
            Weapon("Psi Blast", 8, Tag.Flying | Tag.Ground, 1, 3, Tag.Light, SurgeDie.D3, 2, tags=Tag.Instant),
            Weapon("Strike", "E", Tag.Ground, 1, 4, None, None, 1),
            Weapon(
                "! Psionic Storm / Movement phase",
                "A",
                Tag.Flying | Tag.Ground,
                "BT:Psionic Storm+3",
                5,
                None,
                None,
                1,
                tags=Tag.Sidearm | Tag.Specialist | Tag.DirectDamage,
                flags=Weapon.Flags.SimulationProfile | Weapon.Flags.ResolvedInMovement,
            ),
            Weapon(
                "! Psionic Storm / Assault phase",
                "A",
                Tag.Flying | Tag.Ground,
                "BT:Psionic Storm+3",
                5,
                None,
                None,
                1,
                tags=Tag.Sidearm | Tag.Specialist | Tag.DirectDamage,
                flags=Weapon.Flags.SimulationProfile,
            ),
        ),
        squad=(
            Squad(Range(2, 2), 1, 130),
            Squad(Range(3, 4), 2, 200),
        ),
        tags=Tag.Biological | Tag.Ground | Tag.Light | Tag.Psionic,
        upgrades=(
            Upgrade(
                "Our Minds as One",
                message=(
                    "While this Unit's Current Supply Value is 2, it gains the following effects:\n"
                    "The first Special Ability resolved by this Unit each Round has its PE cost reduced by 1 (to a minimum of 0).\n"
                    "Apply a +1 Modifier to the dice rolled for its Psionic Storm Special Ability."
                ),
                cost=Cost(),
                flags=Upgrade.Flags.TypeOther | Upgrade.Flags.ReplacedByWorkaround,
            ),
            Upgrade(
                "! Our Minds as One",
                apply=_our_minds_as_one,
                message="While this Unit's Current Supply Value is 2, apply a +1 Modifier to its Psionic Storm rolls.",
                flags=Upgrade.Flags.TypeOffensive | Upgrade.Flags.Workaround,
            ),
            Upgrade(
                "Psionic Storm",
                message=(
                    'Set a Psionic Storm token Within 10" and Line of Sight of this Unit. This token is not removed if this Unit is Destroyed. At the '
                    "End of each Phase, set a Psionic Storm Blast Template on the centre of this token. For each Unit that has at least one model whose "
                    "base is partially covered by the template, roll 3 dice, plus 1 additional die for each model in that Unit whose base is partially "
                    "covered. For each result of 5+, that Unit suffers an effect depending on the current Phase:\nMovement Phase: NON-LETHAL DAMAGE "
                    "(1).\nAssault Phase: 1 Damage. \nIf multiple effects trigger at the End of the Assault Phase, resolve them in the order specified "
                    "in Part 8.9.4."
                ),
                cost=Cost(20, 30, points=2),
                flags=Upgrade.Flags.TypeOther | Upgrade.Flags.ReplacedByWorkaround,
            ),
            Upgrade(
                "! Psionic Storm / Assault phase",
                Upgrade.activate_weapon,
                message="Resolved on the Assault chart.",
                cost=Cost(20, 30, points=2),
                flags=Upgrade.Flags.Workaround,
            ),
            Upgrade(
                "! Psionic Storm / Assault phase (2)",
                lambda unit: _activate_psionic_ability_only(unit, "! Psionic Storm / Assault phase"),
                message="Resolve only Psionic Storm instead of the Psi Blast.",
                cost=Cost(20, 30, points=2),
                flags=Upgrade.Flags.Workaround,
            ),
            Upgrade(
                "! Psionic Storm / Movement phase",
                Upgrade.activate_weapon,
                message="Resolved on the Charge chart.",
                cost=Cost(20, 30, points=2),
                flags=Upgrade.Flags.Workaround,
            ),
            Upgrade(
                "Farsight",
                message='Target one Friendly Unit Within 12". Until the End of the Round, that Unit is eligible to make an Evade Roll against any attacks targeting it.',
                cost=Cost(20, points=1),
                flags=Upgrade.Flags.TypeOther | Upgrade.Flags.ReplacedByWorkaround,
            ),
            Upgrade(
                "Feedback",
                message=(
                    'Target one Enemy Mechanical or Psionic Unit Within 8". Until the End of the Round, after that Unit resolves an Active or Reaction '
                    "Special Ability (excluding abilities granted by a Tactical Card or Faction Card), it suffers NON-LETHAL DAMAGE (3)."
                ),
                cost=Cost(points=1),
                flags=Upgrade.Flags.TypeOther,
            ),
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
            Weapon(
                "! Devastating Charge",
                "A",
                Tag.Ground,
                4,
                3,
                None,
                None,
                1,
                tags=Tag.Impact,
                flags=Weapon.Flags.SimulationProfile | Weapon.Flags.TriggeredByCharge,
            ),
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
                flags=Upgrade.Flags.TypeDefensive,
            ),
            Upgrade(
                "Improved Barrier",
                message="Use when this Unit is selected as the target of an attack. If this Unit has the Shielded Status, the Damage characteristic of the attacking weapon is treated as a maximum of 1 for this attack.",
                cost=Cost(),
                apply={Hook.ModifyDamage: _improved_barrier},
                flags=Upgrade.Flags.TypeDefensive,
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
            Upgrade("Indomitable", flags=Upgrade.Flags.TypeOther),
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
            Upgrade("Path of Shadows", flags=Upgrade.Flags.TypeOther),
            Upgrade("Nerazim Farsight", flags=Upgrade.Flags.TypeOther),
            Upgrade("Psionic Transfer", flags=Upgrade.Flags.TypeOther),
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
            Weapon(
                "! Devastating Charge",
                "A",
                Tag.Ground,
                3,
                4,
                None,
                None,
                1,
                tags=Tag.Impact,
                flags=Weapon.Flags.SimulationProfile | Weapon.Flags.TriggeredByCharge,
            ),
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
                apply=lambda unit: unit.grant_reroll("REA"),
            ),
            Upgrade("Leg Enhancements", flags=Upgrade.Flags.TypeOther),
            Upgrade("Charge", flags=Upgrade.Flags.TypeOther),
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
            Upgrade("Structure", flags=Upgrade.Flags.TypeOther),
            Upgrade("Khalai Ingenuity", flags=Upgrade.Flags.TypeOther),
            Upgrade("Warp Conduit", flags=Upgrade.Flags.TypeOther),
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
            Upgrade("Restoration", flags=Upgrade.Flags.TypeOther),
            Upgrade("Force Field", flags=Upgrade.Flags.TypeOther),
            Upgrade(
                "Guardian Shield",
                message='All Ranged Attacks targeting a Friendly Unit Within 4" (Line of Sight is not required) are made with 1 fewer die in the Attack Pool.',
                cost=Cost(points=1),
                flags=Upgrade.Flags.TypeOther | Upgrade.Flags.ReplacedByWorkaround,
            ),
            Upgrade("Solid-Field Projectors", flags=Upgrade.Flags.TypeOther),
            Upgrade("Hallucination", flags=Upgrade.Flags.TypeOther),
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
            Upgrade("Squadron", flags=Upgrade.Flags.TypeOther),
            Upgrade("Path of Shadows", flags=Upgrade.Flags.TypeOther),
            Upgrade("Blink", flags=Upgrade.Flags.TypeOther),
            Upgrade("Fury of the Nerazim", flags=Upgrade.Flags.TypeOther),
        ),
    ),
    Unit(
        faction=Faction.Protoss,
        name="Tassadar",
        unit_type=UnitType.Hero,
        size=2,
        keywords=(),
        shield=3,
        speed=Speed(7, 7),
        evade=5,
        armour=5,
        hit_points=6,
        weapons=(
            Weapon("Resonance Beam", 12, Tag.Flying | Tag.Ground, 6, 3, Tag.Armoured, SurgeDie.D3, 1, tags=Tag.Instant),
            Weapon("Strike", "E", Tag.Ground, 6, 4, None, None, 1),
            Weapon(
                "! Psi Lightning",
                "A",
                Tag.Flying | Tag.Ground,
                1,
                None,
                None,
                None,
                1,
                tags=Tag.Sidearm | Tag.Specialist | Tag.Hits | Tag.DirectDamage,
                flags=Weapon.Flags.SimulationProfile,
            ),
        ),
        squad=(Squad(Range(1, 1), 1, 230),),
        tags=Tag.Biological | Tag.Ground | Tag.Psionic | Tag.Unique,
        upgrades=(
            Upgrade(
                "Commander",
                message=(
                    "Treat this Unit’s Supply characteristic as increased by 1 for Controlling and Contesting Mission Markers, completing objectives, "
                    "and resolving Disengage checks."
                ),
                cost=Cost(),
                flags=Upgrade.Flags.TypeOther,
            ),
            Upgrade(
                "Force Wall",
                message=(
                    'Set two Force Wall tokens Wholly Within 8" in an unoccupied space. Units of Size 2 or lower cannot move across the Force Wall. '
                    "Models of Size 3 or more can move over it, and it's then removed."
                ),
                cost=Cost(points=1),
                flags=Upgrade.Flags.TypeOther,
            ),
            Upgrade(
                "Executor's Will",
                message=(
                    "Target two Enemy Units on the battlefield (Line of Sight is not required) and place a Faction Indicator next to each of them.\n"
                    "During the next Assault Phase, if either of these Units ends its Activation while its Faction Indicator remains on the battlefield, "
                    "you may Activate two Friendly Units consecutively.\nRemove both Faction Indicators after any Enemy Unit completes its Activation in "
                    "the following Assault Phase."
                ),
                cost=Cost(points=1),
                flags=Upgrade.Flags.TypeOther,
            ),
            Upgrade(
                "Khala's Gift",
                message=(
                    'Target another Friendly Biological Unit Within 12". Until the End of the Round, that Unit resolves its first Special Ability with '
                    "the cost reduced by 1 (to a minimum of 0)."
                ),
                cost=Cost(),
                flags=Upgrade.Flags.TypeOther,
            ),
            Upgrade(
                "Telekinetic Push",
                message='Set each Friendly Force Wall token Wholly Within 6" of its current position.',
                cost=Cost(points=1),
                flags=Upgrade.Flags.TypeOther,
            ),
            Upgrade(
                "Psi Lightning",
                apply=lambda unit: unit.activate_weapon("! Psi Lightning"),
                message='Each Unit Within 2" of one or more Friendly Force Wall tokens suffers 1 Damage.',
                cost=Cost(),
            ),
        ),
    ),
    Unit(
        faction=Faction.Protoss,
        name="Twilight Templar (High Templar)",
        unit_type=UnitType.Support,
        size=2,
        keywords=("Protoss", "Templar Caste"),
        shield=3,
        speed=Speed(4, 7),
        evade=6,
        armour=5,
        hit_points=3,
        weapons=(
            Weapon("Psi Blast", 8, Tag.Flying | Tag.Ground, 2, 3, Tag.Light, SurgeDie.D3, 2, tags=Tag.Instant),
            Weapon("Strike", "E", Tag.Ground, 1, 4, None, None, 1),
            Weapon(
                "! Psionic Gale / Movement phase",
                "A",
                Tag.Flying | Tag.Ground,
                "BT:Psionic Storm+3",
                4,
                None,
                None,
                1,
                tags=Tag.Sidearm | Tag.Specialist | Tag.DirectDamage,
                flags=Weapon.Flags.SimulationProfile | Weapon.Flags.ResolvedInMovement,
            ),
            Weapon(
                "! Psionic Gale / Assault phase",
                "A",
                Tag.Flying | Tag.Ground,
                "BT:Psionic Storm+3",
                4,
                None,
                None,
                1,
                tags=Tag.Sidearm | Tag.Specialist | Tag.DirectDamage,
                flags=Weapon.Flags.SimulationProfile,
            ),
        ),
        squad=(Squad(Range(2, 2), 1, 230),),
        tags=Tag.Biological | Tag.Ground | Tag.Light | Tag.Psionic | Tag.Unique,
        upgrades=(
            Upgrade(
                "Bound by the Khala",
                message=(
                    'Use when the Current Supply Value of another Friendly Unit Within 8" of this Unit is reduced. Return one Non-Unique Exhausted '
                    "Tactical Card to the Ready state."
                ),
                cost=Cost(),
                flags=Upgrade.Flags.TypeOther,
            ),
            Upgrade(
                "Warp-In",
                message="Resolve the PLACE (6) effect.",
                cost=Cost(points=1),
                flags=Upgrade.Flags.TypeOther,
            ),
            Upgrade(
                "Psionic Gale",
                message=(
                    'Set a Psionic Storm token Within 10" and Line of Sight of this Unit. This token is not removed if this Unit is Destroyed. At the '
                    "End of each Phase, set a Psionic Storm Blast Template on the centre of this token. For each Unit that has at least one model whose "
                    "base is partially covered by the template, roll 3 dice, plus 1 additional die for each model in that Unit whose base is partially "
                    "covered. For each result of 4+, that Unit suffers an effect depending on the current Phase:\nMovement Phase: NON-LETHAL DAMAGE "
                    "(1).\nAssault Phase: 1 Damage. \nIf multiple effects trigger at the End of the Assault Phase, resolve them in the order specified "
                    "in Part 8.9.4."
                ),
                cost=Cost(points=2),
                flags=Upgrade.Flags.TypeOther | Upgrade.Flags.ReplacedByWorkaround,
            ),
            Upgrade(
                "! Psionic Gale / Assault phase",
                Upgrade.activate_weapon,
                message="Resolved on the Assault chart.",
                cost=Cost(points=2),
                flags=Upgrade.Flags.Workaround,
            ),
            Upgrade(
                "! Psionic Gale / Assault phase (2)",
                lambda unit: _activate_psionic_ability_only(unit, "! Psionic Gale / Assault phase"),
                message="Resolve only Psionic Gale instead of the Psi Blast.",
                cost=Cost(points=2),
                flags=Upgrade.Flags.Workaround,
            ),
            Upgrade(
                "! Psionic Gale / Movement phase",
                Upgrade.activate_weapon,
                message="Resolved on the Charge chart.",
                cost=Cost(points=2),
                flags=Upgrade.Flags.Workaround,
            ),
            Upgrade(
                "Feedback",
                message=(
                    'Target one Enemy Mechanical or Psionic Unit Within 8". Until the End of the Round, after that Unit resolves an Active or Reaction '
                    "Special Ability (excluding abilities granted by a Tactical Card or Faction Card), it suffers NON-LETHAL DAMAGE (3)."
                ),
                cost=Cost(points=1),
                flags=Upgrade.Flags.TypeOther,
            ),
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
            Weapon(
                "! Devastating Charge",
                "A",
                Tag.Ground,
                3,
                4,
                None,
                None,
                1,
                tags=Tag.Impact,
                flags=Weapon.Flags.SimulationProfile | Weapon.Flags.TriggeredByCharge,
            ),
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
                apply=_buff_roa_for_impact_weapons,
            ),
            Upgrade("Leg Enhancements", flags=Upgrade.Flags.TypeOther),
            Upgrade("Charge", flags=Upgrade.Flags.TypeOther),
            Upgrade("Zealous Round", flags=Upgrade.Flags.TypeOther),
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
            Weapon(
                "! Shadow Strike",
                "E",
                Tag.Ground,
                4,
                None,
                None,
                None,
                1,
                tags=Tag.Sidearm | Tag.Hits,
                flags=Weapon.Flags.SimulationProfile,
            ),
            Weapon(
                "! Devastating Charge",
                "A",
                Tag.Ground,
                4,
                4,
                None,
                None,
                1,
                tags=Tag.Impact,
                flags=Weapon.Flags.SimulationProfile | Weapon.Flags.TriggeredByCharge,
            ),
        ),
        squad=(Squad(Range(1, 1), 1, 230),),
        tags=Tag.Biological | Tag.Ground | Tag.Psionic | Tag.Unique,
        upgrades=(
            Upgrade("One With the Shadows", flags=Upgrade.Flags.TypeOther),
            Upgrade(
                "Prophetic Vision",
                message="REPEATABLE. Use when this Unit is selected as the target of an attack. This Unit's Evade characteristic is treated as 4+ against this attack and cannot be modified.",
                cost=Cost(points=1),
                apply=lambda unit: unit.grant_reroll("REA") or unit.buff_evade(1),
                flags=Upgrade.Flags.TypeDefensive,
            ),
            Upgrade(
                "Sentenced to Death",
                message="Target Enemy Unit on the battlefield. Whenever Zeratul makes a Close Combat Attack targeting the selected Unit, its weapon gains CRITICAL HIT (2).",
                cost=Cost(points=1),
                apply=lambda unit: unit.weapon("Master Warp Blade").add_tag(Tag.CriticalHit2),
                flags=Upgrade.Flags.TypeOffensive,
            ),
            Upgrade("Void Prison", flags=Upgrade.Flags.TypeOther),
            Upgrade("Void Blink", flags=Upgrade.Flags.TypeOther),
            Upgrade(
                "Shadow Strike",
                message="All Enemy Units Engaged with this Unit suffer HITS 4 (1).",
                cost=Cost(points=1),
                flags=Upgrade.Flags.TypeOther | Upgrade.Flags.ReplacedByWorkaround,
            ),
            Upgrade(
                "! Shadow Strike",
                message="All Enemy Units Engaged with this Unit suffer HITS 4 (1).",
                cost=Cost(points=1),
                apply=Upgrade.activate_weapon,
                flags=Upgrade.Flags.Workaround,
            ),
            Upgrade(
                "! Shadow Strike (2)",
                _activate_shadow_strike_only,
                message="Resolve Shadow Strike instead of using Master Warp Blade: all Enemy Units Engaged with this Unit suffer HITS 4 (1).",
                cost=Cost(points=1),
                flags=Upgrade.Flags.Workaround,
            ),
        ),
    ),
)


def _guardian_shield_effect(_, roll, pools):
    if roll.weapon_batch.weapon.type_letter == "R":
        pools.attack_pool.transfer_dice_to(pools.discard_pool, up_to=1)


def _psionic_presence_effect(unit):
    for weapon in unit.weapons:
        if weapon.type_letter != "A" and weapon.hit is not None:
            weapon.add_tag(Tag.Precision1)


def _apply_common_skills(units):
    guardian_shield = Upgrade(
        "! Guardian Shield / Sentry",
        message='Apply active GS of a friendly Sentry unit within 4" - All Ranged Attacks are made with 1 fewer die in the Attack Pool.',
        flags=Upgrade.Flags.TypeDefensive | Upgrade.Flags.Workaround,
        apply={Hook.RollPoolsInitiated: _guardian_shield_effect},
    )

    psionic_presence = Upgrade(
        "! Psionic Presence / Adept",
        message="Apply PP of a friendly Adept's Shade token within 4\" - All Ranged and Close Combat weapons gain PRECISION (1)",
        apply=_psionic_presence_effect,
        flags=Upgrade.Flags.Workaround,
    )

    farsight = Upgrade(
        "! Farsight / High Templar",
        message=(
            'Apply Farsight from a friendly High Templar Within 12". Until the End of the Round, this Unit is eligible to make an Evade Roll against '
            "any attacks targeting it."
        ),
        apply=lambda unit: unit.grant_reroll("REA"),
        flags=Upgrade.Flags.TypeDefensive | Upgrade.Flags.Workaround,
    )

    for unit in units:
        if unit.is_structure:
            continue

        unit.upgrades = (*unit.upgrades, guardian_shield, psionic_presence)
        if unit.evade is not None:
            unit.upgrades = (*unit.upgrades, farsight)

    return units


PROTOSS_UNITS = _apply_common_skills(_PROTOSS_UNITS)
