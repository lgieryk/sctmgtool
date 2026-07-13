# Files in this package (stcmgtool.units) are distributed under separate terms —
# see NOTICE.txt in this directory. They are NOT covered by the project's MIT
# License.

from sctmgtool.base import Unit, Faction, Speed, Tag, Weapon, Squad, Range, Upgrade, SurgeDie, Cost

_TERRAN_UNITS: tuple[Unit] = (
    Unit(
        faction=Faction.Terran,
        name="Marine",
        shield=None,
        speed=Speed(4, 7),
        evade=5,
        armour=5,
        hit_points=2,
        weapons=(
            Weapon("C-14 rifle", 12, Tag.Ground | Tag.Flying, 2, 3, Tag.Light, SurgeDie.D3, 1),
            Weapon("AGG-12", 12, Tag.Ground, 2, 3, Tag.Armoured, SurgeDie.D3, 1, tags=Tag.Specialist, exchange_for="C-14 rifle"),
            Weapon("Rocket Launcher", 12, Tag.Ground, 4, 3, None, None, 1, tags=Tag.Sidearm | Tag.Specialist | Tag.IndirectFire),
            Weapon("Strike", "E", Tag.Ground, 1, 5, None, None, 1),
            Weapon("Bayonet", "E", Tag.Ground, 2, 5, None, None, 1, exchange_for="Strike"),
        ),
        squad=(
            Squad(Range(4, 6), 1, 160),
            Squad(Range(7, 9), 2, 210),
        ),
        tags=Tag.Biological | Tag.Light | Tag.Ground,
        upgrades=(
            Upgrade(
                "Combat Shield",
                cost=Cost(20, 30, points=1),
                message="This Unit is always eligible to make an Evade Roll against any Close Combat Attack targeting it and any Damage from an Enemy Special Ability.",
                # Naively assumed it's only the Charge that generates damage from ability
                apply=lambda unit: unit.grant_reroll("EC"),
            ),
            Upgrade("AGG-12", cost=Cost(10), apply=Upgrade.activate_weapon),
            Upgrade("Rocket Launcher", cost=Cost(40), apply=Upgrade.activate_weapon),
            Upgrade(
                "Slugthrower",
                cost=Cost(10, 20),
                message='When this Unit makes a Ranged Attack with a C-14 Rifle and the target is Within 8", that weapon gains ANTI-EVADE (1).',
                apply=lambda unit: unit.weapon("C-14 rifle").add_tag(Tag.AntiEvade1),
            ),
            Upgrade(
                "Grenades - Frag",
                cost=Cost(10),
                message='When this Unit makes a Ranged Attack with a C-14 Rifle and the target is Within 8", that weapon’s S Dice is replaced by D6.',
                apply=lambda unit: unit.weapon("C-14 rifle").set_surge_die(SurgeDie.D6),
            ),
            Upgrade("Bayonet", cost=Cost(20, 30), apply=Upgrade.activate_weapon),
            Upgrade(
                "Stimpack",
                cost=Cost(points=1),
                message="This Unit suffers NON-LETHAL DAMAGE (2). This Unit gains BUFF Speed (3). Additionally, its C-14 Rifle and all Close Combat Weapons gain PRECISION (3).",
                apply=lambda unit: unit.weapon(["C-14 rifle", "@range==E"]).add_tag(Tag.Precision3),
            ),
        ),
    ),
    Unit(
        faction=Faction.Terran,
        name="Goliath",
        shield=None,
        speed=Speed(7, 7),
        evade=None,
        armour=4,
        hit_points=10,
        weapons=(
            Weapon("Autocannon", 12, Tag.Ground, 9, 4, None, None, 1),
            Weapon("Underbelly Machine Gun", 8, Tag.Ground, 6, 3, Tag.Light, SurgeDie.D3, 1, tags=Tag.Pinpoint | Tag.Sidearm),
            Weapon("Hellfire Missiles", 16, Tag.Flying, 6, 3, Tag.Light, SurgeDie.D3, 1, tags=Tag.AntiEvade1 | Tag.Sidearm),
            Weapon(
                "Scatter Missiles",
                18,
                Tag.Ground,
                6,
                5,
                Tag.Light,
                SurgeDie.D3,
                1,
                tags=Tag.Sidearm | Tag.LockedIn6 | Tag.IndirectFire,
                exchange_for="Hellfire Missiles",
            ),
            Weapon(
                "Haywire Missiles", 12, Tag.Ground, 3, 3, Tag.Armoured, SurgeDie.D3, 1, tags=Tag.Sidearm | Tag.PierceArmoured3, exchange_for="Hellfire Missiles"
            ),
            Weapon("Stomp", "E", Tag.Ground, 4, 5, None, None, 1),
            Weapon("Devastating Charge", "C", Tag.Ground, 4, 3, None, None, 1),
        ),
        squad=(Squad(Range(1, 1), 2, 190),),
        tags=Tag.Armoured | Tag.Mechanical | Tag.Ground,
        upgrades=(
            Upgrade(
                "Ares-Class Targeting System",
                cost=Cost(20),
                message="This Unit’s Autocannon and Underbelly Machine Gun weapons gain PRECISION (1).",
                apply=lambda unit: unit.weapon(["Autocannon", "Underbelly Machine Gun"]).add_tag(Tag.Precision1),
            ),
            Upgrade("Scatter Missiles", cost=Cost(30), apply=Upgrade.activate_weapon),
            Upgrade("Haywire Missiles", cost=Cost(40), apply=Upgrade.activate_weapon),
            Upgrade(
                "Target Lock",
                cost=Cost(points=1),
                message='Select one Enemy Unit Within 12". Whenever a Friendly Goliath Unit targets that enemy with an Autocannon, that weapon gains Surge Type: Light, Armoured, and S Dice: D3+1.',
                apply=lambda unit: unit.weapon("Autocannon").add_surge_tag(Tag.Light | Tag.Armoured) or unit.weapon("Autocannon").set_surge_die(SurgeDie.D3P1),
            ),
            Upgrade("! Activate LockedIn6", lambda unit: unit.weapon("Scatter Missiles").buff_roa(6)),
            Upgrade("Indomitable", upgrade_type=Upgrade.Type.Other),
        ),
    ),
    Unit(
        faction=Faction.Terran,
        name="Marauder",
        shield=None,
        speed=Speed(4, 7),
        evade=6,
        armour=4,
        hit_points=5,
        weapons=(
            Weapon("Quad K12", 12, Tag.Ground, 3, 3, Tag.Armoured, SurgeDie.D3, 1, tags=Tag.PierceArmoured2),
            Weapon("Strike", "E", Tag.Ground, 2, 4, None, None, 1),
        ),
        squad=(
            Squad(Range(2, 2), 1, 150),
            Squad(Range(3, 4), 2, 280),
        ),
        tags=Tag.Armoured | Tag.Biological | Tag.Ground,
        upgrades=(
            Upgrade(
                "Stimpack",
                cost=Cost(points=1),
                message="This Unit suffers NON-LETHAL DAMAGE (2). This Unit gains BUFF Speed (3). Additionally, its Quad K12 and all Close Combat Weapons gain PRECISION (2).",
                apply=lambda unit: unit.weapon(["Quad K12", "@range==E"]).add_tag(Tag.Precision2),
            ),
            Upgrade(
                "Veteran of Tarsonis",
                cost=Cost(20, 30),
                message='While this Unit is Within 3" of a Mission Marker, its Armour characteristic is increased by 1.',
                apply=lambda unit: unit.buff_armour(1),
            ),
            Upgrade(
                "Kinetic Foam", cost=Cost(20, 40), message="Increase this Unit's Hit Points characteristic by 1.", apply=lambda unit: unit.buff_hit_points(1)
            ),
            Upgrade("Concussive Shells", upgrade_type=Upgrade.Type.Other),
            Upgrade("Laser Targeting Systems", upgrade_type=Upgrade.Type.Other),
        ),
    ),
    Unit(
        faction=Faction.Terran,
        name="Jim Raynor",
        shield=None,
        speed=Speed(7, 7),
        evade=5,
        armour=4,
        hit_points=8,
        weapons=(
            Weapon("Commando Rifle", 18, Tag.Ground | Tag.Flying, 3, 3, Tag.Armoured, SurgeDie.D3, 1, tags=Tag.Bulky | Tag.PierceArmoured3),
            Weapon("“Justice” Revolver", 6, Tag.Ground, 2, 3, None, None, 2, tags=Tag.AntiEvade2 | Tag.Sidearm | Tag.Pinpoint),
            Weapon("Bayonet", "E", Tag.Ground, 2, 4, Tag.Light, SurgeDie.D3, 1),
            Weapon("C-14 rifle", 12, Tag.Ground | Tag.Flying, 6, 3, Tag.Light, SurgeDie.D3P1, 1, tags=Tag.BurstFire, exchange_for="Commando Rifle"),
        ),
        squad=(Squad(Range(1, 1), 1, 250),),
        tags=Tag.Unique | Tag.Biological | Tag.Ground,
        upgrades=(
            Upgrade("C-14 rifle", Upgrade.activate_weapon),
            Upgrade('! Activate BURST FIRE (3) on C-14 Rifle - target within 8"', lambda unit: unit.weapon("C-14 rifle").buff_roa(3)),
            Upgrade("Commander", upgrade_type=Upgrade.Type.Other),
            Upgrade("Freedom Fighters", upgrade_type=Upgrade.Type.Other),
            Upgrade("Orders", upgrade_type=Upgrade.Type.Other),
        ),
    ),
    Unit(
        faction=Faction.Terran,
        name="Medic",
        shield=None,
        speed=Speed(4, 7),
        evade=5,
        armour=5,
        hit_points=2,
        weapons=(Weapon("Strike", "E", Tag.Ground, 1, 5, None, None, 1),),
        squad=(Squad(Range(2, 3), 1, 110),),
        tags=Tag.Biological | Tag.Light | Tag.Ground,
        upgrades=(
            Upgrade("Life Support", upgrade_type=Upgrade.Type.Other),
            Upgrade("Advanced Medic Facilities", upgrade_type=Upgrade.Type.Other),
            Upgrade("Restoration", upgrade_type=Upgrade.Type.Other),
            Upgrade("A-13 Flash Grenade Launcher", upgrade_type=Upgrade.Type.Other),
            Upgrade("Stabilizer Medpacks", upgrade_type=Upgrade.Type.Other),
            Upgrade("Medpack", upgrade_type=Upgrade.Type.Other),
            Upgrade("Optical Flare", upgrade_type=Upgrade.Type.Other),
        ),
    ),
    Unit(
        faction=Faction.Terran,
        name="Point Defense Drone",
        shield=None,
        speed=Speed(0, 0),
        evade=6,
        armour=6,
        hit_points=3,
        weapons=(),
        squad=(Squad(Range(1, 1), 0, 0),),
        tags=Tag.Armoured | Tag.Flying | Tag.Mechanical,
        upgrades=(
            Upgrade("Point Defense Laser", upgrade_type=Upgrade.Type.Other),
            Upgrade("Gliding", upgrade_type=Upgrade.Type.Other),
            Upgrade("Structure", upgrade_type=Upgrade.Type.Other),
        ),
    ),
    Unit(
        faction=Faction.Terran,
        name="Raynor's Raider (Marine)",
        shield=None,
        speed=Speed(unit=4, model=7),
        evade=5,
        armour=5,
        hit_points=2,
        weapons=(
            Weapon("C-14 rifle", 12, Tag.Flying | Tag.Ground, 2, 3, Tag.Light, SurgeDie.D3, 1),
            Weapon("Bayonet", "E", Tag.Ground, 2, 5, None, None, 1),
        ),
        squad=(Squad(Range(1, 6), 1, 230),),
        tags=Tag.Biological | Tag.Ground | Tag.Light,
        upgrades=(
            Upgrade(
                "Stimpack",
                message="This Unit suffers NON-LETHAL DAMAGE (2). This Unit gains BUFF Speed (3). Additionally, its C-14 Rifle and all Close Combat Weapons gain PRECISION (3).",
                cost=Cost(points=1),
                apply=lambda unit: unit.weapon(["C-14 rifle", "@range==E"]).add_tag(Tag.Precision3),
            ),
            Upgrade("Raiders Roll!", upgrade_type=Upgrade.Type.Other),
            Upgrade("Rapid Reinforcements", upgrade_type=Upgrade.Type.Other),
            Upgrade(
                "Slugthrower",
                message='When this Unit makes a Ranged Attack with a C-14 Rifle and the target is Within 8", that weapon gains ANTI-EVADE (1).',
                cost=Cost(0),
                apply=lambda unit: unit.weapon("C-14 rifle").add_tag(Tag.AntiEvade1),
            ),
            Upgrade(
                "Grenades - Frag",
                message='When this Unit makes a Ranged Attack with a C-14 Rifle and the target is Within 8", that weapon’s S Dice is replaced by D6.',
                cost=Cost(0),
                apply=lambda unit: unit.weapon("C-14 rifle").set_surge_die(SurgeDie.D6),
            ),
        ),
    ),
)


def _apply_common_skills(units):
    orders = Upgrade(
        "! Orders / Jim Raynor",
        message='Apply active Orders of a friendly Jim Raynor within 8" - Unit’s first used weapon gains the CRITICAL HIT (2)',
        apply=lambda unit: unit.weapon("*").add_tag(Tag.CriticalHit2),
    )

    for unit in units:
        unit.upgrades = (*unit.upgrades, orders)

    return units


TERRAN_UNITS = _apply_common_skills(_TERRAN_UNITS)
