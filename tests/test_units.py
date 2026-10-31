# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Łukasz Gieryk

from copy import deepcopy
from unittest.mock import patch

from sctmgtool import hooks
from sctmgtool.base import Hook, Tag, Upgrade, Weapon
from sctmgtool.histogram import simulate_clash
from sctmgtool.tools import ClashType, DicePool, HookContext, MusteredUnit, WeaponBatch, process_unit_list
from sctmgtool.units import ALL_UNITS
from sctmgtool.units.terran import TERRAN_UNITS
from sctmgtool.units.zerg import ZERG_UNITS


def muster(name: str, config=None):
    prototype = next(unit for unit in ALL_UNITS if unit.name == name)
    return MusteredUnit.make(prototype, config or {})


def clone(name: str):
    prototype = next(unit for unit in ALL_UNITS if unit.name == name)
    return deepcopy(prototype)


def test_debilitating_saliva_ignores_units_without_ranged_weapons():
    vile = next(unit for unit in ZERG_UNITS if unit.name == "Vile (Roach)")
    defender = MusteredUnit.make(vile, {"Debilitating Saliva": True}, is_attacker=False)

    medic = MusteredUnit.make(next(unit for unit in TERRAN_UNITS if unit.name == "Medic"), {})
    HookContext(medic, defender).apply_opponent_hooks(medic, defender)
    assert medic.batch("Strike").weapon.hit == 5

    marine = MusteredUnit.make(next(unit for unit in TERRAN_UNITS if unit.name == "Marine"), {})
    HookContext(marine, defender).apply_opponent_hooks(marine, defender)
    assert marine.batch("C-14 rifle").weapon.hit == 4
    assert marine.batch("Strike").weapon.hit == 5


def test_point_defense_laser_applies_to_first_non_instant_ranged_weapon():
    upgrade_name = "! Point Defense Laser / Point Defense Drone"
    marine = next(unit for unit in TERRAN_UNITS if unit.name == "Marine")
    drone = next(unit for unit in TERRAN_UNITS if unit.name == "Point Defense Drone")
    assert marine.has_upgrade(upgrade_name)
    assert not drone.has_upgrade(upgrade_name)

    attacker = MusteredUnit.make(marine, {})
    defender = MusteredUnit.make(marine, {upgrade_name: True}, is_attacker=False)
    context = HookContext(attacker, defender)

    instant_weapon = Weapon("Instant", 12, Tag.Ground, 4, 3, None, None, 1, tags=Tag.Instant)
    ranged_weapon = Weapon("Ranged", 12, Tag.Ground, 4, 3, None, None, 1)
    melee_weapon = Weapon("Melee", "E", Tag.Ground, 4, 3, None, None, 1)

    def apply_hook(weapon):
        attack_pool = DicePool.n_dice(4)
        discard_pool = DicePool.empty()
        pools = hooks.PoolHookArgs(attack_pool, DicePool.empty(), DicePool.empty(), discard_pool)
        context.call_hooks(Hook.RollPoolsInitiated, hooks.RollHookArgs(attacker, WeaponBatch(1, weapon), defender), pools)
        return attack_pool.size(), discard_pool.size()

    assert apply_hook(instant_weapon) == (4, 0)
    assert apply_hook(melee_weapon) == (4, 0)
    assert apply_hook(ranged_weapon) == (2, 2)
    assert apply_hook(ranged_weapon) == (4, 0)

    context.reset_hook_state()
    assert apply_hook(ranged_weapon) == (2, 2)


def test_ancillary_carapace_applies_tough_only_to_first_weapon_of_each_clash():
    attacker = MusteredUnit.make(clone("Marine"), {})
    weapons = (
        Weapon("First", 12, Tag.Ground, 1, None, None, None, 1, tags=Tag.Hits),
        Weapon("Second", 12, Tag.Ground, 1, None, None, None, 1, tags=Tag.Hits),
    )
    attacker.weapon_batches = [WeaponBatch(1, weapon) for weapon in weapons]

    defender = MusteredUnit.make(clone("Hydralisk"), {"Ancillary Carapace": True}, is_attacker=False)
    defender.armour = 7
    defender.shield = 0

    with patch("sctmgtool.tools.random.choices", side_effect=lambda _, k: [1] * k):
        histogram = simulate_clash(attacker, defender, roll_count=2)[ClashType.Ranged]

    assert histogram.damage[1] == 100


def test_ravager_corrosive_bile_weapon_combinations():
    cases = (
        ({}, ("Plasma Discharge",)),
        ({"! Corrosive Bile": True}, ("Plasma Discharge", "! Corrosive Bile")),
        ({"! Corrosive Bile (2)": True}, ("! Corrosive Bile",)),
        ({"! Corrosive Bile": True, "! Corrosive Bile (2)": True}, ("! Corrosive Bile",)),
    )

    for config, expected in cases:
        ravager = muster("Ravager", config)
        active = tuple(batch.weapon.name for batch in ravager.weapon_batches if batch.weapon.name in ("Plasma Discharge", "! Corrosive Bile"))
        assert active == expected


def test_zerg_ground_and_flying_weapon_combinations():
    cases = (
        ("Queen", "Talons (Assault)", "Acid spines", "! Acid spines"),
        ("Zagara", "Zagara's Talons", "Zagara's Acid Spines", "! Zagara's Acid Spines"),
    )

    for unit_name, ground_weapon, flying_weapon, upgrade in cases:
        unit = muster(unit_name)
        assert unit.batch(ground_weapon) is not None
        assert unit.batch(flying_weapon) is None

        unit = muster(unit_name, {upgrade: True})
        assert unit.batch(ground_weapon) is None
        assert unit.batch(flying_weapon) is not None


def test_zeratul_shadow_strike_weapon_combinations():
    cases = (
        ({}, ("Master Warp Blade",)),
        ({"! Shadow Strike": True}, ("Master Warp Blade", "! Shadow Strike")),
        ({"! Shadow Strike (2)": True}, ("! Shadow Strike",)),
        ({"! Shadow Strike": True, "! Shadow Strike (2)": True}, ("! Shadow Strike",)),
    )

    for config, expected in cases:
        zeratul = muster("Zeratul", config)
        active = tuple(batch.weapon.name for batch in zeratul.weapon_batches if batch.weapon.name in ("Master Warp Blade", "! Shadow Strike"))
        assert active == expected


def test_psionic_presence_does_not_affect_shadow_strike():
    zeratul = muster("Zeratul", {"! Shadow Strike": True, "! Psionic Presence / Adept": True})

    assert Tag.Precision1 in zeratul.batch("Master Warp Blade").weapon.tags
    assert Tag.Precision1 not in zeratul.batch("! Shadow Strike").weapon.tags


def test_our_minds_as_one_buffs_psionic_storm_at_supply_two():
    upgrade = "! Our Minds as One"
    storm = "! Psionic Storm / Assault phase"

    processed_templar = process_unit_list((clone("High Templar"),))[0]
    processed_upgrade = next(item for item in processed_templar.upgrades if item.name == upgrade)
    assert Upgrade.Flags.TypeOffensive in processed_upgrade.flags

    small_unit = muster("High Templar", {upgrade: True, storm: True})
    large_unit = muster("High Templar", {"_squad_size": 3, upgrade: True, storm: True})

    assert small_unit.batch(storm).weapon.hit == 5
    assert large_unit.batch(storm).weapon.hit == 4


def test_direct_damage_ability_profile():
    profile_name = "! Psi Lightning"
    assert muster("Tassadar").batch(profile_name) is None

    batch = muster("Tassadar", {"Psi Lightning": True}).batch(profile_name)
    weapon = batch.weapon
    assert batch.model_num == 1
    assert weapon.range == "A"
    assert weapon.target == Tag.Flying | Tag.Ground
    assert weapon.rate_of_attack == 1
    assert weapon.hit is None
    assert weapon.damage == 1
    assert weapon.tags == Tag.Sidearm | Tag.Specialist | Tag.Hits | Tag.DirectDamage


def test_siege_tank_shock_cannon_automatically_applies_aftershock_rounds():
    prototype = next(unit for unit in ALL_UNITS if unit.name == "Siege Tank")
    upgrades = {upgrade.name: upgrade for upgrade in prototype.upgrades}
    assert "! Shock Cannon / Aftershock Rounds" in upgrades
    assert Upgrade.Flags.ReplacedByWorkaround in upgrades["Aftershock Rounds"].flags

    processed_tank = process_unit_list((prototype,))[0]
    assert not processed_tank.has_upgrade("Aftershock Rounds")
    assert processed_tank.has_upgrade("! Shock Cannon / Aftershock Rounds")

    tank_without_upgrade = muster("Siege Tank")
    assert tank_without_upgrade.batch("Twin Cannon") is not None
    assert tank_without_upgrade.batch("Shock Cannon") is None

    tank = muster("Siege Tank", {"! Shock Cannon / Aftershock Rounds": True})
    shock_cannon = tank.batch("Shock Cannon")
    assert shock_cannon is not None
    assert shock_cannon.weapon.rate_of_attack == "BT:Shock Cannon+4"
    assert tank.batch("Twin Cannon") is None

    defender = muster("Marine")
    damage = hooks.DamageHookArgs(shock_cannon.weapon.damage)
    HookContext(tank).call_hooks(Hook.ModifyDamage, hooks.RollHookArgs(tank, shock_cannon, defender), damage)
    assert damage.value == defender.size


def test_biological_structure_negates_impact_attacks():
    attacker = muster("Zergling")
    attacker.weapon_batches = [WeaponBatch(1, Weapon("Impact", "A", Tag.Ground, 1, 2, None, None, 1, tags=Tag.Impact))]
    defender = MusteredUnit.make(clone("Bile Launcher"), {"Biological Structure": True}, is_attacker=False)

    with patch("sctmgtool.tools.random.choices", side_effect=lambda _, k: [2] * k):
        histogram = simulate_clash(attacker, defender, roll_count=1)[ClashType.Charge]

    assert histogram.damage[0] == 100


def test_dark_swarm_and_broodmother_workarounds_apply_size_dependent_effects():
    vileling = MusteredUnit.make(
        clone("Vileling (Zergling)"),
        {"! Dark Swarm / Defiler": True},
        is_attacker=False,
    )
    assert vileling.evade_reroll == "REA"
    assert vileling.evade == 4

    vileling = muster("Vileling (Zergling)", {"! Broodmother / Zagara": True})
    assert vileling.batch("! Devastating Charge").weapon.hit == 4
    assert vileling.batch("Claws").weapon.hit == 5

    defiler = clone("Defiler")
    defiler.weapons = (*defiler.weapons, Weapon("Other Ability", "A", Tag.Ground, 1, 3, None, None, 1))
    defiler = MusteredUnit.make(defiler, {"! Broodmother / Zagara": True})
    assert all(Tag.CriticalHit1 in weapon.tags for weapon in defiler.weapons if Tag.Impact not in weapon.tags)
    assert Tag.CriticalHit1 not in next(weapon for weapon in defiler.weapons if Tag.Impact in weapon.tags).tags

    zagara = MusteredUnit.make(clone("Zagara"), {"! Broodmother / Zagara": True}, is_attacker=False)
    assert Tag.Tough1 in zagara.tags


def test_simulated_ability_profiles_are_marked_in_their_names():
    profiles = [weapon for unit in ALL_UNITS for weapon in unit.weapons if Weapon.Flags.SimulationProfile in weapon.flags]

    assert profiles
    assert all(weapon.name.startswith("! ") for weapon in profiles)


def test_ability_profile_chart_flags_are_consistent():
    weapons = [weapon for unit in ALL_UNITS for weapon in unit.weapons]
    profiles = [weapon for weapon in weapons if Weapon.Flags.TriggeredByCharge in weapon.flags]
    movement_profiles = [weapon for weapon in weapons if Weapon.Flags.ResolvedInMovement in weapon.flags]
    devastating_charge_profiles = [weapon for weapon in weapons if weapon.name == "! Devastating Charge"]

    assert profiles
    assert movement_profiles
    assert all(Weapon.Flags.SimulationProfile in weapon.flags for weapon in profiles)
    assert all(Weapon.Flags.SimulationProfile in weapon.flags for weapon in movement_profiles)
    assert all(weapon.type_letter == "A" for weapon in profiles)
    assert all(weapon.type_letter == "A" for weapon in movement_profiles)
    assert all(Weapon.Flags.TriggeredByCharge not in weapon.flags for weapon in movement_profiles)
    assert all(Weapon.Flags.TriggeredByCharge in weapon.flags for weapon in devastating_charge_profiles)


def test_my_life_for_aiur_only_buffs_impact_rate_of_attack():
    zealot = clone("Zealot")
    zealot.weapons = (*zealot.weapons, Weapon("Other Ability", "A", Tag.Ground, 2, 3, None, None, 1))

    zealot = MusteredUnit.make(zealot, {"My Life for Aiur": True})

    assert next(weapon for weapon in zealot.weapons if Tag.Impact in weapon.tags).rate_of_attack == 4
    assert next(weapon for weapon in zealot.weapons if weapon.name == "Other Ability").rate_of_attack == 2


def test_transfusion_reduces_total_damage_not_below_zero():
    attacker = MusteredUnit.make(next(unit for unit in TERRAN_UNITS if unit.name == "Marine"), {})
    bile_launcher = next(unit for unit in ZERG_UNITS if unit.name == "Bile Launcher")
    defender = MusteredUnit.make(bile_launcher, {"! Transfusion / Queen/Zagara": True}, is_attacker=False)
    context = HookContext(attacker, defender)

    for initial, expected in ((5, 3), (1, 0)):
        total_damage = hooks.TotalDamageHookArgs(attacker, defender, ClashType.Ranged, initial)
        context.call_hooks(Hook.ModifyTotalDamage, total_damage)
        assert total_damage.value == expected


def test_plague_biomass_upgrades_stack_on_one_profile():
    plague = "! Plague"
    second_bm = "! Plague / Second BM"
    third_bm = "! Plague / Third BM"
    cases = (
        ({plague: True}, 5),
        ({plague: True, second_bm: True}, 4),
        ({plague: True, second_bm: True, third_bm: True}, 3),
    )

    assert muster("Defiler").batch(plague) is None

    for config, hit in cases:
        defiler = muster("Defiler", config)
        batches = [batch for batch in defiler.weapon_batches if batch.weapon.name == plague]

        assert len(batches) == 1
        assert batches[0].weapon.rate_of_attack == "BT:Plague+2"
        assert batches[0].weapon.hit == hit
        assert batches[0].weapon.tags == Tag.Sidearm | Tag.DirectDamage
