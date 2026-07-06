# Files in this package (stcmgtool.units) are distributed under separate terms —
# see NOTICE.txt in this directory. They are NOT covered by the project's MIT
# License.

from sctmgtool.base import Unit, Faction, Speed, Tag, Weapon, Squad, Range, Upgrade, SurgeDie, Cost

ZERG_UNITS: tuple[Unit] = (
    Unit(
        faction=Faction.Zerg,
        name="Zergling",
        shield=None,
        speed=Speed(4, 8),
        evade=4,
        armour=6,
        hit_points=1,
        weapons=(
            Weapon("Claws", "E", Tag.Ground, 2, 4, Tag.Light, SurgeDie.D3, 1),
            Weapon("Shredding Claws", "E", Tag.Ground, 2, 4, Tag.Light | Tag.Armoured, SurgeDie.D3, 1, exchange_for="Claws"),
            Weapon("Devastating Charge", "C", Tag.Ground, 1, 5, None, None, 1),
        ),
        squad=(
            Squad(Range(7, 12), 1, 180),
            Squad(Range(13, 18), 2, 220),
        ),
        tags=Tag.Biological | Tag.Light | Tag.Ground,
        upgrades=(
            Upgrade(
                "Adrenal Glands",
                cost=Cost(10),
                message="This Unit’s Claws and Shredding Claws weapons gain PRECISION (2).",
                apply=lambda unit: unit.weapon(["Claws", "Shredding Claws"]).add_tag(Tag.Precision2),
            ),
            Upgrade("Shredding Claws", Upgrade.activate_weapon),
        ),
    ),
)
