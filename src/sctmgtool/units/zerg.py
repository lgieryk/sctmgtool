# Files in this package (stcmgtool.units) are distributed under separate terms —
# see NOTICE.txt in this directory. They are NOT covered by the project's MIT
# License.

from sctmgtool.base import Cost, Faction, Hook, Range, Speed, Squad, StatefulHook, SurgeDie, Tag, Unit, UnitType, Upgrade, Weapon


def _debuff_hit_of_ranged_weapons(unit):
    for weapon in unit.weapons:
        if weapon.type_letter == "R":
            weapon.debuff_hit(1)


def _activate_corrosive_bile_only(unit):
    if unit.batch("! Corrosive Bile") is None:
        unit.activate_weapon("! Corrosive Bile")

    plasma_discharge = unit.batch("Plasma Discharge")
    if plasma_discharge is not None:
        unit.weapon_batches.remove(plasma_discharge)


def _potent_bile(_, roll, armour):
    if roll.weapon_batch.weapon.name == "! Corrosive Bile":
        armour.value = min(6, armour.value + 1)


def _biological_structure(owner, roll, pools):
    if owner is roll.defender and Tag.Impact in roll.weapon_batch.weapon.tags:
        pools.attack_pool.transfer_dice_to(pools.discard_pool)


def _apply_dark_swarm(unit):
    unit.grant_reroll("REA")
    if unit.size == 1:
        unit.buff_evade(1)


def _transfusion(owner, total_damage):
    if owner is total_damage.defender:
        total_damage.value = max(0, total_damage.value - 2)


def _buff_impact_hit(unit):
    for weapon in unit.weapons:
        if Tag.Impact in weapon.tags:
            weapon.buff_hit(1)


def _add_critical_hit_to_non_impact_weapons(unit):
    for weapon in unit.weapons:
        if Tag.Impact not in weapon.tags:
            weapon.add_tag(Tag.CriticalHit1)


def _broodmother_upgrade(unit):
    if unit.size == 1 and any(Tag.Impact in weapon.tags for weapon in unit.weapons):
        return Upgrade(
            "! Broodmother / Zagara",
            message="Apply Broodmother of a friendly Zagara: this Size 1 Unit gains a +1 Modifier to all IMPACT Rolls.",
            cost=Cost(points=1),
            apply=_buff_impact_hit,
            flags=Upgrade.Flags.TypeOffensive | Upgrade.Flags.Workaround,
        )

    if unit.size == 2:
        return Upgrade(
            "! Broodmother / Zagara",
            message="Apply Broodmother of a friendly Zagara: all weapons of this Size 2 Unit gain CRITICAL HIT (1).",
            cost=Cost(points=1),
            apply=_add_critical_hit_to_non_impact_weapons,
            flags=Upgrade.Flags.TypeOffensive | Upgrade.Flags.Workaround,
        )

    if unit.size is not None and unit.size >= 3:
        return Upgrade(
            "! Broodmother / Zagara",
            message="Apply Broodmother of a friendly Zagara: this Size 3 or larger Unit gains TOUGH (1).",
            cost=Cost(points=1),
            apply=lambda mustered_unit: mustered_unit.add_tag(Tag.Tough1),
            flags=Upgrade.Flags.TypeDefensive | Upgrade.Flags.Workaround,
        )

    return None


class _AncillaryCarapaceHook(StatefulHook):
    def __init__(self):
        self.used = False

    def reset_state(self):
        self.used = False

    def __call__(self, owner, roll, tough):
        if owner is roll.defender and not self.used:
            tough.value = max(tough.value, 1)
            self.used = True


_ZERG_UNITS: tuple[Unit, ...] = (
    Unit(
        faction=Faction.Zerg,
        name="Corpser (Roach)",
        unit_type=UnitType.Core,
        size=2,
        keywords=(),
        shield=None,
        speed=Speed(4, 7),
        evade=5,
        armour=3,
        hit_points=4,
        weapons=(
            Weapon("Acid Saliva", 8, Tag.Ground, 2, 3, None, None, 1),
            Weapon("Claws", "E", Tag.Ground, 3, 4, Tag.Light, SurgeDie.D3P1, 1),
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
        squad=(Squad(Range(2, 3), 1, 240),),
        tags=Tag.Biological | Tag.Armoured | Tag.Ground,
        upgrades=(
            Upgrade(
                "Hydriodic Bile",
                cost=Cost(10),
                message="This Unit's Acid Saliva weapon gains Surge Type: Light, and S Dice: D3+1.",
                apply=lambda unit: unit.weapon("Acid Saliva").set_surge_die(SurgeDie.D3P1) or unit.weapon("Acid Saliva").add_surge_tag(Tag.Light),
            ),
            Upgrade("Burrow", flags=Upgrade.Flags.TypeOther),
            Upgrade("Tunneling Claws", flags=Upgrade.Flags.TypeOther),
            Upgrade("Roachling Infestation", flags=Upgrade.Flags.TypeOther),
            Upgrade("Burrow Ambush", flags=Upgrade.Flags.TypeOther),
            Upgrade("Glial Reconstitution", flags=Upgrade.Flags.TypeOther),
            Upgrade("Regeneration", flags=Upgrade.Flags.TypeOther),
        ),
    ),
    Unit(
        faction=Faction.Zerg,
        name="Hydralisk",
        unit_type=UnitType.Elite,
        size=2,
        keywords=(),
        shield=None,
        speed=Speed(4, 8),
        evade=5,
        armour=5,
        hit_points=4,
        weapons=(
            Weapon("Needle Spines", 12, Tag.Ground | Tag.Flying, 3, 3, Tag.Light | Tag.Armoured, SurgeDie.D3P1, 2),
            Weapon("Scythe", "E", Tag.Ground, 2, 4, None, None, 1),
        ),
        squad=(
            Squad(Range(2, 2), 2, 140),
            Squad(Range(3, 4), 3, 260),
        ),
        tags=Tag.Biological | Tag.Light | Tag.Ground,
        upgrades=(
            Upgrade(
                "Ancillary Carapace",
                cost=Cost(20, 40),
                message="This Unit gains TOUGH (1) on the first Armour Roll of each Activation.",
                apply={Hook.ModifyTough: _AncillaryCarapaceHook()},
                flags=Upgrade.Flags.TypeDefensive,
            ),
            Upgrade(
                "Lurking",
                cost=Cost(10, 20),
                message=(
                    "If this Unit has Stationary Status, it is eligible to make an Evade Roll against the first Ranged Attack targeting it this Round. "
                    "If this Unit is ON CREEP, it gains +1 Modifier to this Evade Roll."
                ),
                flags=Upgrade.Flags.TypeOther | Upgrade.Flags.ReplacedByWorkaround,
            ),
            Upgrade(
                "! Lurking",
                cost=Cost(10, 20),
                message="If this Unit has Stationary Status, it is eligible to make an Evade Roll against the first Ranged Attack targeting it this Round.",
                apply=lambda unit: unit.grant_reroll("R"),
                flags=Upgrade.Flags.Workaround,
            ),
            Upgrade(
                "! Lurking + ON CREEP",
                message="If this Unit is ON CREEP, it gains +1 Modifier to this Evade Roll.",
                apply=lambda unit: unit.buff_evade(1),
                flags=Upgrade.Flags.Workaround,
            ),
            Upgrade("Squadron", flags=Upgrade.Flags.TypeOther),
            Upgrade("Burrow Ambush", flags=Upgrade.Flags.TypeOther),
            Upgrade("Lunge", flags=Upgrade.Flags.TypeOther),
            Upgrade("Grooved Spines", flags=Upgrade.Flags.TypeOther),
        ),
    ),
    Unit(
        faction=Faction.Zerg,
        name="Kerrigan",
        unit_type=UnitType.Hero,
        size=2,
        keywords=(),
        shield=None,
        speed=Speed(7, 7),
        evade=6,
        armour=5,
        hit_points=9,
        weapons=(
            Weapon("Energy Blast", 8, Tag.Ground | Tag.Flying, 5, 3, Tag.Light | Tag.Armoured, SurgeDie.D3, 1),
            Weapon("Blades", "E", Tag.Ground, 6, 4, None, None, 2, tags=Tag.CriticalHit2),
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
        squad=(Squad(Range(1, 1), 1, 250),),
        tags=Tag.Biological | Tag.Psionic | Tag.Ground | Tag.Unique,
        upgrades=(
            Upgrade(
                "Mutating Carapace",
                cost=Cost(points=1),
                message='Select one Enemy Unit Within 18". This Unit is eligible to make an Evade Roll against all attacks made by the selected Enemy Unit, with a +2 Modifier applied to those Evade Rolls.',
                apply=lambda unit: unit.grant_reroll("REA") or unit.buff_evade(2),
            ),
            Upgrade("Commander", flags=Upgrade.Flags.TypeOther),
            Upgrade("Crushing Grip", flags=Upgrade.Flags.TypeOther),
            Upgrade("Leaping Strike", flags=Upgrade.Flags.TypeOther),
        ),
    ),
    Unit(
        faction=Faction.Zerg,
        name="Kerrigan Swarm Raptor (Zergling)",
        unit_type=UnitType.Elite,
        size=1,
        keywords=("Kerrigan's Swarm",),
        shield=None,
        speed=Speed(5, 9),
        evade=4,
        armour=5,
        hit_points=2,
        weapons=(
            Weapon("Claws", "E", Tag.Ground, 2, 3, Tag.Light | Tag.Armoured, SurgeDie.D6, 1, tags=Tag.Instant),
            Weapon(
                "! Devastating Charge",
                "A",
                Tag.Ground,
                2,
                5,
                None,
                None,
                1,
                tags=Tag.Impact,
                flags=Weapon.Flags.SimulationProfile | Weapon.Flags.TriggeredByCharge,
            ),
        ),
        squad=(Squad(Range(4, 6), 1, 250),),
        tags=Tag.Biological | Tag.Light | Tag.Ground | Tag.Unique,
        upgrades=(
            Upgrade(
                "Adrenal Overload",
                cost=Cost(points=1),
                message="This Unit gains a +1 Modifier to all IMPACT Hit Rolls.",
                apply=_buff_impact_hit,
            ),
            Upgrade("Squadron", flags=Upgrade.Flags.TypeOther),
            Upgrade("Raptor Strain", flags=Upgrade.Flags.TypeOther),
            Upgrade("Leap", flags=Upgrade.Flags.TypeOther),
        ),
    ),
    Unit(
        faction=Faction.Zerg,
        name="Omega Worm",
        unit_type=UnitType.Other,
        size=3,
        keywords=("Kerrigan's Swarm",),
        shield=None,
        speed=Speed(0, 0),
        evade=None,
        armour=5,
        hit_points=10,
        weapons=(),
        squad=(Squad(Range(1, 1), 0, 0),),
        tags=Tag.Biological | Tag.Armoured | Tag.Ground,
        upgrades=(
            Upgrade("Detection", flags=Upgrade.Flags.TypeOther),
            Upgrade("Source of Creep", flags=Upgrade.Flags.TypeOther),
            Upgrade("Structure", flags=Upgrade.Flags.TypeOther),
            Upgrade("Omega Network", flags=Upgrade.Flags.TypeOther),
        ),
    ),
    Unit(
        faction=Faction.Zerg,
        name="Queen",
        unit_type=UnitType.Support,
        size=3,
        keywords=(),
        shield=None,
        speed=Speed(4, 4),
        evade=None,
        armour=4,
        hit_points=9,
        weapons=(
            Weapon("Talons (Combat)", "E", Tag.Ground, 3, 4, None, None, 1),
            Weapon("Talons (Assault)", "6", Tag.Ground, 4, 4, Tag.Light, SurgeDie.D3, 2),
            # Note: Spines are not actually a "for" replacement
            Weapon("Acid spines", 12, Tag.Flying, 4, 4, Tag.Light | Tag.Armoured, SurgeDie.D3, 2, exchange_for="Talons (Assault)"),
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
        squad=(Squad(Range(1, 1), 1, 150),),
        tags=Tag.Biological | Tag.Armoured | Tag.Ground | Tag.Psionic,
        upgrades=(
            Upgrade(
                "! Acid spines",
                apply=lambda unit: unit.activate_weapon("Acid spines"),
                message="Use Acid spines instead of Talons (Assault).",
                flags=Upgrade.Flags.Workaround,
            ),
            Upgrade("Spawn Creep Tumor", flags=Upgrade.Flags.TypeOther),
            Upgrade(
                "Transfusion",
                message=(
                    'Use when another Friendly Biological Unit (including a Structure) suffers Damage Within 4". Reduce the Total Damage before '
                    "allocation by 2."
                ),
                cost=Cost(points=1),
                flags=Upgrade.Flags.TypeOther | Upgrade.Flags.ReplacedByWorkaround,
            ),
            Upgrade("Restoration", flags=Upgrade.Flags.TypeOther),
            Upgrade("Psionic Link", flags=Upgrade.Flags.TypeOther),
            Upgrade("Creep Speed", flags=Upgrade.Flags.TypeOther),
            Upgrade("Domineering Presence", flags=Upgrade.Flags.TypeOther),
        ),
    ),
    Unit(
        faction=Faction.Zerg,
        name="Raptor (Zergling)",
        unit_type=UnitType.Elite,
        size=1,
        keywords=(),
        shield=None,
        speed=Speed(5, 9),
        evade=4,
        armour=6,
        hit_points=1,
        weapons=(
            Weapon("Claws", "E", Tag.Ground, 2, 4, Tag.Light, SurgeDie.D3, 1),
            Weapon("Shredding Claws", "E", Tag.Ground, 2, 4, Tag.Light | Tag.Armoured, SurgeDie.D3, 1, exchange_for="Claws"),
            Weapon(
                "! Devastating Charge",
                "A",
                Tag.Ground,
                1,
                5,
                None,
                None,
                1,
                tags=Tag.Impact,
                flags=Weapon.Flags.SimulationProfile | Weapon.Flags.TriggeredByCharge,
            ),
        ),
        squad=(
            Squad(Range(7, 12), 1, 240),
            Squad(Range(13, 18), 2, 300),
        ),
        tags=Tag.Biological | Tag.Light | Tag.Ground,
        upgrades=(
            Upgrade(
                "Adrenal Overload",
                cost=Cost(points=1),
                message="This Unit gains a +1 Modifier to all IMPACT Hit Rolls.",
                apply=_buff_impact_hit,
            ),
            Upgrade(
                "Adrenal Glands",
                cost=Cost(20),
                message="This Unit’s Claws and Shredding Claws weapons gain PRECISION (2).",
                apply=lambda unit: unit.weapon(["Claws", "Shredding Claws"]).add_tag(Tag.Precision2),
            ),
            Upgrade("Shredding Claws", Upgrade.activate_weapon),
            Upgrade("Squadron", flags=Upgrade.Flags.TypeOther),
            Upgrade("Raptor Strain", flags=Upgrade.Flags.TypeOther),
            Upgrade("Burrow Ambush", flags=Upgrade.Flags.TypeOther),
            Upgrade("Metabolic Boost", flags=Upgrade.Flags.TypeOther),
        ),
    ),
    Unit(
        faction=Faction.Zerg,
        name="Ravager",
        unit_type=UnitType.Core,
        size=3,
        keywords=(),
        shield=None,
        speed=Speed(4, 8),
        evade=5,
        armour=5,
        hit_points=9,
        weapons=(
            Weapon("Plasma Discharge", 12, Tag.Ground, 4, 3, Tag.Light, SurgeDie.D3P1, 1),
            Weapon(
                "! Corrosive Bile",
                14,
                Tag.Ground,
                5,
                None,
                None,
                None,
                1,
                tags=Tag.Sidearm | Tag.Hits,
                flags=Weapon.Flags.SimulationProfile,
            ),
            Weapon("Claws", "E", Tag.Ground, 2, 4, None, None, 1),
            Weapon(
                "! Devastating Charge",
                "A",
                Tag.Ground,
                2,
                4,
                None,
                None,
                1,
                tags=Tag.Impact,
                flags=Weapon.Flags.SimulationProfile | Weapon.Flags.TriggeredByCharge,
            ),
        ),
        squad=(
            Squad(Range(1, 1), 1, 160),
            Squad(Range(2, 2), 2, 270),
        ),
        tags=Tag.Biological | Tag.Ground | Tag.Armoured,
        upgrades=(
            Upgrade("Squadron", flags=Upgrade.Flags.TypeOther),
            Upgrade("Bloated Bile Ducts", flags=Upgrade.Flags.TypeOther),
            Upgrade(
                "Corrosive Bile",
                message="For each model in this Unit, set one Corrosive Bile token on the battlefield Within 14\" of that model. These tokens are not removed if this Unit is Destroyed. At the End of the Assault Phase, each Unit suffers HITS 5 (1) effect for each of this Unit's Corrosive Bile tokens it is Within 1\" of. Then, remove all of this Unit's Corrosive Bile tokens from the battlefield. If multiple effects trigger at the End of the Assault Phase, resolve them in the order specified in Part 8.9.4.",
                cost=Cost(points=1),
                flags=Upgrade.Flags.TypeOther | Upgrade.Flags.ReplacedByWorkaround,
            ),
            Upgrade(
                "! Corrosive Bile",
                message="For each model in this Unit, set one Corrosive Bile token on the battlefield Within 14\" of that model. These tokens are not removed if this Unit is Destroyed. At the End of the Assault Phase, each Unit suffers HITS 5 (1) effect for each of this Unit's Corrosive Bile tokens it is Within 1\" of. Then, remove all of this Unit's Corrosive Bile tokens from the battlefield. If multiple effects trigger at the End of the Assault Phase, resolve them in the order specified in Part 8.9.4.",
                cost=Cost(points=1),
                apply=Upgrade.activate_weapon,
                flags=Upgrade.Flags.Workaround,
            ),
            Upgrade(
                "! Corrosive Bile (2)",
                _activate_corrosive_bile_only,
                message="Use instead of Plasma Discharge.",
                cost=Cost(points=1),
                flags=Upgrade.Flags.Workaround,
            ),
            Upgrade("Deep Tunnel", flags=Upgrade.Flags.TypeOther),
            Upgrade("Burrow Ambush", flags=Upgrade.Flags.TypeOther),
            Upgrade(
                "Potent Bile",
                message="Before an Enemy Unit resolves an Armour Roll against the HITS effect generated by this Unit's Corrosive Bile ability, that Unit suffers DEBUFF Armour (1).",
                cost=Cost(20, 40),
                apply={Hook.ModifyArmour: _potent_bile},
                flags=Upgrade.Flags.TypeOffensive,
            ),
        ),
    ),
    Unit(
        faction=Faction.Zerg,
        name="Roach",
        unit_type=UnitType.Core,
        size=2,
        keywords=(),
        shield=None,
        speed=Speed(4, 7),
        evade=5,
        armour=3,
        hit_points=4,
        weapons=(
            Weapon("Claws", "E", Tag.Ground, 2, 4, None, None, 1),
            Weapon("Acid Saliva", 8, Tag.Ground, 3, 3, None, None, 1),
            Weapon(
                "! Devastating Charge",
                "A",
                Tag.Ground,
                2,
                4,
                None,
                None,
                1,
                tags=Tag.Impact,
                flags=Weapon.Flags.SimulationProfile | Weapon.Flags.TriggeredByCharge,
            ),
        ),
        squad=(Squad(Range(2, 3), 1, 170),),
        tags=Tag.Biological | Tag.Armoured | Tag.Ground,
        upgrades=(
            Upgrade(
                "Hydriodic Bile",
                cost=Cost(10),
                message="This Unit's Acid Saliva weapon gains Surge Type: Light, and S Dice: D3+1.",
                apply=lambda unit: unit.weapon("Acid Saliva").set_surge_die(SurgeDie.D3P1) or unit.weapon("Acid Saliva").add_surge_tag(Tag.Light),
            ),
            Upgrade("Burrow", flags=Upgrade.Flags.TypeOther),
            Upgrade("Tunneling Claws", flags=Upgrade.Flags.TypeOther),
            Upgrade("Burrow Ambush", flags=Upgrade.Flags.TypeOther),
            Upgrade("Glial Reconstitution", flags=Upgrade.Flags.TypeOther),
            Upgrade("Regeneration", flags=Upgrade.Flags.TypeOther),
        ),
    ),
    Unit(
        faction=Faction.Zerg,
        name="Roachling",
        unit_type=UnitType.Other,
        size=1,
        keywords=(),
        shield=None,
        speed=Speed(4, 7),
        evade=6,
        armour=6,
        hit_points=1,
        weapons=(Weapon("Claws", "E", Tag.Ground, 2, 4, None, None, 1),),
        squad=(Squad(Range(1, 3), 0, 0),),
        tags=Tag.Biological | Tag.Light | Tag.Ground,
        upgrades=(Upgrade("Underdeveloped Claws", flags=Upgrade.Flags.TypeOther),),
    ),
    Unit(
        faction=Faction.Zerg,
        name="Swarmling (Zergling)",
        unit_type=UnitType.Core,
        size=1,
        keywords=(),
        shield=None,
        speed=Speed(4, 8),
        evade=5,
        armour=6,
        hit_points=1,
        weapons=(
            Weapon("Claws", "E", Tag.Ground, 2, 5, None, None, 1),
            Weapon(
                "! Devastating Charge",
                "A",
                Tag.Ground,
                1,
                5,
                None,
                None,
                1,
                tags=Tag.Impact,
                flags=Weapon.Flags.SimulationProfile | Weapon.Flags.TriggeredByCharge,
            ),
        ),
        squad=(Squad(Range(7, 18), 1, 260),),
        tags=Tag.Biological | Tag.Light | Tag.Ground,
        upgrades=(
            Upgrade("Squadron", flags=Upgrade.Flags.TypeOther),
            Upgrade("Burrow Ambush", flags=Upgrade.Flags.TypeOther),
            Upgrade("Zergling Reconstitution", flags=Upgrade.Flags.TypeOther),
            Upgrade("Metabolic Boost", flags=Upgrade.Flags.TypeOther),
        ),
    ),
    Unit(
        faction=Faction.Zerg,
        name="Vile (Roach)",
        unit_type=UnitType.Core,
        size=2,
        keywords=(),
        shield=None,
        speed=Speed(4, 7),
        evade=5,
        armour=3,
        hit_points=4,
        weapons=(
            Weapon("Vile Claws", "E", Tag.Ground, 2, 4, None, None, 1),
            Weapon("Acid Saliva", 8, Tag.Ground, 4, 3, None, None, 1),
            Weapon(
                "! Devastating Charge",
                "A",
                Tag.Ground,
                1,
                4,
                None,
                None,
                1,
                tags=Tag.Impact,
                flags=Weapon.Flags.SimulationProfile | Weapon.Flags.TriggeredByCharge,
            ),
        ),
        squad=(Squad(Range(2, 3), 1, 200),),
        tags=Tag.Biological | Tag.Armoured | Tag.Ground,
        upgrades=(
            Upgrade(
                "Hydriodic Bile",
                cost=Cost(10),
                message="This Unit's Acid Saliva weapon gains Surge Type: Light, and S Dice: D3+1.",
                apply=lambda unit: unit.weapon("Acid Saliva").set_surge_die(SurgeDie.D3P1) or unit.weapon("Acid Saliva").add_surge_tag(Tag.Light),
            ),
            Upgrade(
                "Debilitating Saliva",
                cost=Cost(points=1),
                message="Use when an Enemy Unit Within 8\" of this Unit declares a Ranged Attack. Apply DEBUFF Hit (1) to each of that Unit's Ranged Weapons.",
                apply={Hook.ModifyOpponent: _debuff_hit_of_ranged_weapons},
                flags=Upgrade.Flags.TypeDefensive,
            ),
            Upgrade("Burrow", flags=Upgrade.Flags.TypeOther),
            Upgrade("Tunneling Claws", flags=Upgrade.Flags.TypeOther),
            Upgrade("Burrow Ambush", flags=Upgrade.Flags.TypeOther),
            Upgrade("Glial Reconstitution", flags=Upgrade.Flags.TypeOther),
            Upgrade("Regeneration", flags=Upgrade.Flags.TypeOther),
        ),
    ),
    Unit(
        faction=Faction.Zerg,
        name="Zergling",
        unit_type=UnitType.Core,
        size=1,
        keywords=(),
        shield=None,
        speed=Speed(4, 8),
        evade=4,
        armour=6,
        hit_points=1,
        weapons=(
            Weapon("Claws", "E", Tag.Ground, 2, 4, Tag.Light, SurgeDie.D3, 1),
            Weapon("Shredding Claws", "E", Tag.Ground, 2, 4, Tag.Light | Tag.Armoured, SurgeDie.D3, 1, exchange_for="Claws"),
            Weapon(
                "! Devastating Charge",
                "A",
                Tag.Ground,
                1,
                5,
                None,
                None,
                1,
                tags=Tag.Impact,
                flags=Weapon.Flags.SimulationProfile | Weapon.Flags.TriggeredByCharge,
            ),
        ),
        squad=(
            Squad(Range(7, 12), 1, 180),
            Squad(Range(13, 18), 2, 220),
        ),
        tags=Tag.Biological | Tag.Light | Tag.Ground,
        upgrades=(
            Upgrade(
                "Adrenal Glands",
                cost=Cost(20),
                message="This Unit’s Claws and Shredding Claws weapons gain PRECISION (2).",
                apply=lambda unit: unit.weapon(["Claws", "Shredding Claws"]).add_tag(Tag.Precision2),
            ),
            Upgrade("Shredding Claws", Upgrade.activate_weapon),
            Upgrade("Squadron", flags=Upgrade.Flags.TypeOther),
            Upgrade("Burrow Ambush", flags=Upgrade.Flags.TypeOther),
            Upgrade("Metabolic Boost", flags=Upgrade.Flags.TypeOther),
        ),
    ),
    Unit(
        faction=Faction.Zerg,
        name="Bile Launcher",
        unit_type=UnitType.Support,
        size=3,
        keywords=(),
        shield=None,
        speed=Speed(0, 0),
        evade=None,
        armour=4,
        hit_points=10,
        weapons=(
            Weapon(
                "Bile Bomb",
                12,
                Tag.Ground,
                6,
                3,
                Tag.Light | Tag.Armoured,
                SurgeDie.D3,
                1,
                tags=Tag.Pinpoint | Tag.PierceArmoured2,
            ),
        ),
        squad=(Squad(Range(1, 1), 1, 150),),
        tags=Tag.Biological | Tag.Ground | Tag.Armoured | Tag.Unique,
        upgrades=(
            Upgrade(
                "Biological Structure",
                message="This Unit cannot gain the BURROWED Status, cannot be returned to Reserves, and is immune to the IMPACT keyword.",
                cost=Cost(),
                apply={Hook.RollPoolsInitiated: _biological_structure},
                flags=Upgrade.Flags.TypeDefensive,
            ),
            Upgrade(
                "Source of Creep",
                message='A Friendly or Enemy Ground Zerg Unit Within 6" of this Unit, counts as being ON CREEP.',
                cost=Cost(),
                flags=Upgrade.Flags.TypeOther,
            ),
            Upgrade(
                "Detection",
                message='While Enemy Units are Within 6" of this Unit, they lose the HIDDEN Status.',
                cost=Cost(),
                flags=Upgrade.Flags.TypeOther,
            ),
            Upgrade(
                "Burrow Ambush",
                message=(
                    "When this Unit is nominated to deploy from the Reserves, it may resolve the PLACE (18) effect from the controlling player's Entry "
                    "Edge. No model may be set Within 10\" of any Enemy model. This Unit's Activation ends."
                ),
                cost=Cost(),
                flags=Upgrade.Flags.TypeOther,
            ),
            Upgrade(
                "Bombard",
                message=(
                    'Set a Bile Bomb token on the battlefield Within 24" of this Unit. When this Unit resolves a Ranged Attack using the Bile Bomb '
                    "weapon profile this Round, it may choose to ignore the weapon's standard Range characteristic. If it does, it may target an Enemy "
                    'Unit that is Within 3" of that token (Line of Sight is not required), ignoring the HIDDEN Status. After the attack is fully resolved, '
                    "remove the Bile Bomb token from the battlefield. When the Bile Bomb token is about to be removed, set a Creep Tumor token in "
                    "base-to-base contact with it. The Bile Bomb token has DISPLACEMENT."
                ),
                cost=Cost(points=1),
                flags=Upgrade.Flags.TypeOther,
            ),
            Upgrade(
                "Indomitable",
                message=(
                    "While Engaged, this Unit may target and be targeted by Unengaged Enemy Units. In both cases, the defending Unit gains an Evade "
                    "Roll against those attacks."
                ),
                cost=Cost(),
                flags=Upgrade.Flags.TypeOther,
            ),
        ),
    ),
    Unit(
        faction=Faction.Zerg,
        name="Defiler",
        unit_type=UnitType.Support,
        size=2,
        keywords=(),
        shield=None,
        speed=Speed(7, 7),
        evade=5,
        armour=5,
        hit_points=8,
        weapons=(
            Weapon("Claws", "E", Tag.Ground, 4, 3, None, None, 1),
            Weapon("Cancerous Bite", "E", Tag.Ground, 2, 3, None, None, 2, tags=Tag.Sidearm | Tag.CriticalHit1),
            Weapon(
                "! Plague",
                "A",
                Tag.Ground | Tag.Flying,
                "BT:Plague+2",
                5,
                None,
                None,
                1,
                tags=Tag.Sidearm | Tag.DirectDamage,
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
        squad=(Squad(Range(1, 1), 1, 130),),
        tags=Tag.Biological | Tag.Ground | Tag.Light | Tag.Psionic,
        upgrades=(
            Upgrade(
                "Consume",
                message=(
                    'When this Unit resolves a Special Ability that costs BM, it can remove one model from a Friendly Unit Within 4" to generate 1 BM '
                    "to spend towards that ability’s cost."
                ),
                cost=Cost(),
                flags=Upgrade.Flags.TypeOther,
            ),
            Upgrade(
                "Gestate Dark Swarm",
                message='Set a Dark Swarm token in an unoccupied space Within 4" and Line of Sight of this Unit. The Dark Swarm token has DISPLACEMENT.',
                cost=Cost(),
                flags=Upgrade.Flags.TypeOther,
            ),
            Upgrade(
                "Burrow Ambush",
                message=(
                    "When this Unit is nominated to deploy from Reserves, it may resolve the PLACE (18) effect from the controlling player's Entry Edge. "
                    "No model may be placed Within 10\" of any Enemy model. This Unit's Activation ends."
                ),
                cost=Cost(20),
                flags=Upgrade.Flags.TypeOther,
            ),
            Upgrade(
                "Dark Swarm",
                message=(
                    'REPEATABLE. Use when a Friendly Unit Within 4" of a Friendly Dark Swarm token is selected as the target of an attack. If this Unit '
                    "is Within 4'' of the same token, the Targeted Friendly Unit is eligible to make an Evade Roll against that attack. If the targeted "
                    "Unit is a Size 1, it gains a +1 Modifier to this Evade Roll."
                ),
                cost=Cost(points=1),
                flags=Upgrade.Flags.TypeOther | Upgrade.Flags.ReplacedByWorkaround,
            ),
            Upgrade(
                "Plague",
                message=(
                    'You may spend 1 to 3 BM to activate this ability. Set a Plague Blast Template Wholly Within 10" and Line of Sight of this Unit. For '
                    "each Unit that has at least one model whose base is partially covered by the template, roll 2 dice, plus 1 additional die for each "
                    "model in that Unit whose base is partially covered. That Unit loses its HIDDEN Status, and, depending on the BM spent, it suffers "
                    "NON-LETHAL DAMAGE (1) for:\n1 BM: each result of 5+.\n2 BM: each result of 4+.\n3 BM: each result of 3+."
                ),
                cost=Cost(20),
                flags=Upgrade.Flags.TypeOther | Upgrade.Flags.ReplacedByWorkaround,
            ),
            Upgrade(
                "! Plague",
                Upgrade.activate_weapon,
                message=(
                    'Spend 1 BM and resolve a Plague Blast Template Wholly Within 10" and Line of Sight of this Unit. In this simulation, '
                    "NON-LETHAL DAMAGE (1) is represented as regular Damage, so the kills chart is not rules-accurate."
                ),
                cost=Cost(20),
                flags=Upgrade.Flags.Workaround,
            ),
            Upgrade(
                "! Plague / Second BM",
                apply=lambda unit: unit.weapon("! Plague").buff_hit(1),
                message="Select together with ! Plague. Spend a second BM to improve the Plague roll from 5+ to 4+.",
                flags=Upgrade.Flags.Workaround,
            ),
            Upgrade(
                "! Plague / Third BM",
                apply=lambda unit: unit.weapon("! Plague").buff_hit(1),
                message="Select together with ! Plague and ! Plague / Second BM. Spend a third BM to improve the Plague roll from 4+ to 3+.",
                flags=Upgrade.Flags.Workaround,
            ),
            Upgrade(
                "Devastating Charge",
                message="Immediately after this Unit completes a successful Charge, resolve the IMPACT (4) 4+ effect.",
                cost=Cost(),
                flags=Upgrade.Flags.TypeOther | Upgrade.Flags.ReplacedByWorkaround,
            ),
        ),
    ),
    Unit(
        faction=Faction.Zerg,
        name="Vileling (Zergling)",
        unit_type=UnitType.Core,
        size=1,
        keywords=("Zerg", "Zagara's Swarm"),
        shield=None,
        speed=Speed(4, 8),
        evade=5,
        armour=6,
        hit_points=1,
        weapons=(
            Weapon("Claws", "E", Tag.Ground, 2, 5, None, None, 1),
            Weapon(
                "! Devastating Charge",
                "A",
                Tag.Ground,
                1,
                5,
                None,
                None,
                1,
                tags=Tag.Impact,
                flags=Weapon.Flags.SimulationProfile | Weapon.Flags.TriggeredByCharge,
            ),
        ),
        squad=(Squad(Range(7, 18), 2, 180),),
        tags=Tag.Biological | Tag.Ground | Tag.Light,
        upgrades=(
            Upgrade(
                "Squadron",
                message='This Unit’s Horizontal Coherency is 4".',
                cost=Cost(),
                flags=Upgrade.Flags.TypeOther,
            ),
            Upgrade(
                "Burrow Ambush",
                message=(
                    "When this Unit is nominated to deploy from the Reserves, it may resolve the PLACE (18) effect from the controlling player's Entry "
                    "Edge. No model may be set Within 10\" of any Enemy model. This Unit's Activation ends."
                ),
                cost=Cost(),
                flags=Upgrade.Flags.TypeOther,
            ),
            Upgrade(
                "Zergling Reconstitution",
                message="Resolve the RESPAWN (2) effect, or RESPAWN (3) if the Unit is ON CREEP.",
                cost=Cost(points=1),
                flags=Upgrade.Flags.TypeOther,
            ),
            Upgrade(
                "Metabolic Boost",
                message=(
                    "When determining Charge Distance for this Unit, roll 2D6 instead of D6 and use the higher result to add to the Unit’s Speed "
                    "characteristic."
                ),
                cost=Cost(points=1),
                flags=Upgrade.Flags.TypeOther,
            ),
            Upgrade(
                "Devastating Charge",
                message="Immediately after this Unit completes a successful Charge, resolve the IMPACT (1) 5+ effect.",
                cost=Cost(),
                flags=Upgrade.Flags.TypeOther | Upgrade.Flags.ReplacedByWorkaround,
            ),
            Upgrade(
                "Debilitating Claws",
                message="After an Enemy Unit suffers Damage from this Unit, apply DEBUFF Hit (1) to each of that Unit's Weapons.",
                cost=Cost(),
                flags=Upgrade.Flags.TypeOther,
            ),
        ),
    ),
    Unit(
        faction=Faction.Zerg,
        name="Zagara",
        unit_type=UnitType.Hero,
        size=3,
        keywords=(),
        shield=None,
        speed=Speed(7, 7),
        evade=6,
        armour=4,
        hit_points=10,
        weapons=(
            Weapon("Zagara's Talons", 8, Tag.Ground, 4, 3, Tag.Light | Tag.Armoured, SurgeDie.D3, 2),
            Weapon(
                "Zagara's Acid Spines",
                14,
                Tag.Flying,
                8,
                3,
                Tag.Light | Tag.Armoured,
                SurgeDie.D3,
                1,
                exchange_for="Zagara's Talons",
            ),
            Weapon("Talons", "E", Tag.Ground, 4, 3, None, None, 1),
            Weapon(
                "! Devastating Charge",
                "A",
                Tag.Ground,
                6,
                3,
                None,
                None,
                1,
                tags=Tag.Impact,
                flags=Weapon.Flags.SimulationProfile | Weapon.Flags.TriggeredByCharge,
            ),
        ),
        squad=(Squad(Range(1, 1), 1, 250),),
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
                "! Zagara's Acid Spines",
                apply=lambda unit: unit.activate_weapon("Zagara's Acid Spines"),
                message="Use Zagara's Acid Spines instead of Zagara's Talons.",
                flags=Upgrade.Flags.Workaround,
            ),
            Upgrade(
                "Transfusion",
                message=(
                    'Use when another Friendly Biological Unit (including a Structure) suffers Damage Within 4". Reduce the Total Damage before '
                    "allocation by 2."
                ),
                cost=Cost(points=1),
                flags=Upgrade.Flags.TypeOther | Upgrade.Flags.ReplacedByWorkaround,
            ),
            Upgrade(
                "Psionic Link",
                message=(
                    'Once per Round, if there are at least 7 Friendly models Within 6" of this Unit, it may resolve its Special Ability with the BM cost '
                    "reduced by 1."
                ),
                cost=Cost(),
                flags=Upgrade.Flags.TypeOther,
            ),
            Upgrade(
                "Broodmother",
                message=(
                    "Apply one of the following effects to all Friendly units (Line of Sight is not required). You cannot apply the effect chosen in the "
                    "previous Game Round:\n\nUnits of Size 1 gain a +1 Modifier to all IMPACT Rolls.\n\nAll weapons of Size 2 Units gain CRITICAL HIT "
                    "(1).\n\nUnits of Size 3 or more gain TOUGH (1)."
                ),
                cost=Cost(points=1),
                flags=Upgrade.Flags.TypeOther | Upgrade.Flags.ReplacedByWorkaround,
            ),
            Upgrade(
                "Infested Drop",
                message=(
                    "The base of the Zagara counts as an Entry Edge. Each Round, Friendly Units with a combined Supply cost of 1 may be Deployed via "
                    "this Entry Edge."
                ),
                cost=Cost(),
                flags=Upgrade.Flags.TypeOther,
            ),
            Upgrade(
                "Indomitable",
                message=(
                    "While Engaged, this Unit may target and be targeted by Unengaged Enemy Units. In both cases, the defending Unit gains an Evade "
                    "Roll against those attacks."
                ),
                cost=Cost(),
                flags=Upgrade.Flags.TypeOther,
            ),
            Upgrade(
                "Devastating Charge",
                message="Immediately after this Unit completes a successful Charge, resolve the IMPACT (6) 3+ effect.",
                cost=Cost(),
                flags=Upgrade.Flags.TypeOther | Upgrade.Flags.ReplacedByWorkaround,
            ),
        ),
    ),
)


def _apply_common_skills(units):
    dark_swarm = Upgrade(
        "! Dark Swarm / Defiler",
        message=(
            'REPEATABLE. Use when this Friendly Unit is selected as the target of an attack while it is Within 4" of a Friendly Dark Swarm token. If '
            'a Friendly Defiler is Within 4" of the same token, this Unit is eligible to make an Evade Roll against that attack. If this Unit is '
            "Size 1, it also gains a +1 Modifier to this Evade Roll."
        ),
        cost=Cost(points=1),
        apply=_apply_dark_swarm,
        flags=Upgrade.Flags.TypeDefensive | Upgrade.Flags.Workaround,
    )
    transfusion = Upgrade(
        "! Transfusion / Queen/Zagara",
        message=(
            'Use when this Friendly Biological Unit, including a Structure, suffers Damage while Within 4" of a Friendly Queen or Zagara. Reduce '
            "the Total Damage before allocation by 2."
        ),
        cost=Cost(points=1),
        apply={Hook.ModifyTotalDamage: _transfusion},
        flags=Upgrade.Flags.TypeDefensive | Upgrade.Flags.Workaround,
    )

    for unit in units:
        to_add = []

        if unit.evade is not None:
            to_add.append(dark_swarm)

        if Tag.Biological in unit.tags:
            to_add.append(transfusion)

        broodmother = _broodmother_upgrade(unit)
        if broodmother is not None:
            to_add.append(broodmother)

        unit.upgrades = (*unit.upgrades, *to_add)

    return units


ZERG_UNITS = _apply_common_skills(_ZERG_UNITS)
