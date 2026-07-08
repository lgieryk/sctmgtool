# Files in this package (stcmgtool.units) are distributed under separate terms —
# see NOTICE.txt in this directory. They are NOT covered by the project's MIT
# License.

from sctmgtool.base import Unit, Faction, Speed, Tag, Weapon, Squad, Range, Upgrade, SurgeDie, Cost, Hook

_PROTOSS_UNITS: tuple[Unit] = (
    Unit(
        faction=Faction.Protoss,
        name="Zealot",
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
                cost=Cost(10),
                message="When this Unit makes a Close Combat Attack, if the target is Engaged with at least 1 other Friendly Unit, this Unit's Close Combat Weapon gains PRECISION (2).",
                apply=lambda unit: unit.weapon("@range==E").add_tag(Tag.Precision2),
            ),
            Upgrade(
                "My Life for Aiur",
                cost=Cost(10),
                message="When this Unit resolves IMPACT, each eligible model generates 1 additional IMPACT die.",
                apply=lambda unit: unit.weapon("@range==C").buff_roa(1),
            ),
        ),
    ),
)


def _guardian_shield_effect(_, roll, pools):
    if roll.weapon_batch.weapon.type_letter() == "R":
        pools.attack_pool.transfer_dice_to(pools.discard_pool, up_to=1)


def _apply_common_skills(units):
    guardian_shield = Upgrade(
        "! Guardian Shield / Sentry",
        message='Apply active GS of a friendly Sentry unit within 4" - All Ranged Attacks are made with 1 fewer die in the Attack Pool.',
        upgrade_type=Upgrade.Type.Defensive,
        apply={Hook.RollPoolsInitiated: _guardian_shield_effect},
    )

    psionic_presence = Upgrade(
        "! Psionic Presence / Adept",
        message="Apply PP of a friendly Adept's Shade token within 4\" - All weapons gain PRECISION (1)",
        apply=lambda unit: unit.weapon("*").add_tag(Tag.Precision1),
    )

    for unit in units:
        unit.upgrades = (*unit.upgrades, guardian_shield, psionic_presence)

    return units


PROTOSS_UNITS = _apply_common_skills(_PROTOSS_UNITS)
