# Files in this package (stcmgtool.units) are distributed under separate terms —
# see NOTICE.txt in this directory. They are NOT covered by the project's MIT
# License.

from sctmgtool.base import Unit, Faction, Speed, Tag, Weapon, Squad, Range, Upgrade, SurgeDie, Cost

TERRAN_UNITS: tuple[Unit] = (
    Unit(
        faction=Faction.Terran,
        name="Marine",
        shield=None,
        speed=Speed(4, 7),
        evade=5,
        armour=5,
        hit_points=2,
        weapons=(
            Weapon("C-14 Rifle", 12, Tag.Ground | Tag.Flying, 2, 3, Tag.Light, SurgeDie.D3, 1),
            Weapon("AGG-12", 12, Tag.Ground, 2, 3, Tag.Armoured, SurgeDie.D3, 1, tags=Tag.Specialist, exchange_for="C-14 Rifle"),
            Weapon("Rocket Launcher", 12, Tag.Ground, 4, 3, None, None, 1, tags=Tag.Sidearm | Tag.Specialist),
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
                apply=lambda unit: unit.grant_reroll("EC"),
            ),  # Naively assumed it's only the Charge that generates damage from ability
            Upgrade("AGG-12", cost=Cost(10), apply=Upgrade.activate_weapon),
            Upgrade("Rocket Launcher", cost=Cost(40), apply=Upgrade.activate_weapon),
            Upgrade(
                "Slugthrower",
                cost=Cost(10, 20),
                message='When this Unit makes a Ranged Attack with a C-14 Rifle and the target is Within 8", that weapon gains ANTI-EVADE (1).',
                apply=lambda unit: unit.weapon("C-14 Rifle").add_tag(Tag.AntiEvade1),
            ),
            Upgrade(
                "Grenades - Frag",
                cost=Cost(10),
                message='When this Unit makes a Ranged Attack with a C-14 Rifle and the target is Within 8", that weapon’s S Dice is replaced by D6.',
                apply=lambda unit: unit.weapon("C-14 Rifle").set_surge_die(SurgeDie.D6),
            ),
            Upgrade("Bayonet", cost=Cost(20, 30), apply=Upgrade.activate_weapon),
            Upgrade(
                "Stimpack",
                cost=Cost(points=1),
                message="This Unit suffers NON-LETHAL DAMAGE (2). This Unit gains BUFF Speed (3). Additionally, its C-14 Rifle and all Close Combat Weapons gain PRECISION (3).",
                apply=lambda unit: unit.weapon(["C-14 Rifle", "@range==E"]).add_tag(Tag.Precision3),
            ),
        ),
    ),
)
