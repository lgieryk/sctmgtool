# Files in this package (stcmgtool.units) are distributed under separate terms —
# see NOTICE.txt in this directory. They are NOT covered by the project's MIT
# License.

from sctmgtool.base import Cost, Faction, Hook, Range, Speed, Squad, SurgeDie, Tag, Unit, UnitType, Upgrade, Weapon


def _aftershock_rounds(_, roll, damage):
    if roll.weapon_batch.weapon.name == "Shock Cannon":
        damage.value = max(1, roll.defender.size or 1)


def _apply_lethal_hologram(unit):
    for weapon in unit.weapons:
        if weapon.type_letter != "A" and weapon.hit is not None:
            weapon.add_tag(Tag.Precision1)


_TERRAN_UNITS: tuple[Unit, ...] = (
    Unit(
        faction=Faction.Terran,
        name="Marine",
        unit_type=UnitType.Core,
        size=2,
        keywords=(),
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
                apply=lambda unit: unit.grant_reroll("EA"),
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
        unit_type=UnitType.Elite,
        size=3,
        keywords=(),
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
            Upgrade(
                "! Activate LockedIn6",
                lambda unit: unit.weapon("Scatter Missiles").buff_roa(6),
                flags=Upgrade.Flags.Workaround,
            ),
            Upgrade("Indomitable", flags=Upgrade.Flags.TypeOther),
        ),
    ),
    Unit(
        faction=Faction.Terran,
        name="Marauder",
        unit_type=UnitType.Core,
        size=2,
        keywords=(),
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
            Upgrade("Concussive Shells", flags=Upgrade.Flags.TypeOther),
            Upgrade("Laser Targeting Systems", flags=Upgrade.Flags.TypeOther),
        ),
    ),
    Unit(
        faction=Faction.Terran,
        name="Jim Raynor",
        unit_type=UnitType.Hero,
        size=2,
        keywords=(),
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
            Upgrade(
                '! Activate BURST FIRE (3) on C-14 Rifle - target within 8"',
                lambda unit: unit.weapon("C-14 rifle").buff_roa(3),
                flags=Upgrade.Flags.Workaround,
            ),
            Upgrade("Commander", flags=Upgrade.Flags.TypeOther),
            Upgrade("Freedom Fighters", flags=Upgrade.Flags.TypeOther),
            Upgrade(
                "Orders",
                message=(
                    'REPEATABLE. Select another Friendly Biological Unit Within 8", spend CP and apply one of the following effects:\n\n'
                    "1 CP: That Unit’s first used weapon gains the CRITICAL HIT (2).\n\n"
                    "1 CP: That Unit ignores the Disengage penalty for the remainder of the Round.\n\n"
                    "2 CP: Remove the Activation Marker from that Unit."
                ),
                cost=Cost(),
                flags=Upgrade.Flags.TypeOther | Upgrade.Flags.ReplacedByWorkaround,
            ),
        ),
    ),
    Unit(
        faction=Faction.Terran,
        name="Medic",
        unit_type=UnitType.Support,
        size=2,
        keywords=(),
        shield=None,
        speed=Speed(4, 7),
        evade=5,
        armour=5,
        hit_points=2,
        weapons=(Weapon("Strike", "E", Tag.Ground, 1, 5, None, None, 1),),
        squad=(Squad(Range(2, 3), 1, 110),),
        tags=Tag.Biological | Tag.Light | Tag.Ground,
        upgrades=(
            Upgrade("Life Support", flags=Upgrade.Flags.TypeOther),
            Upgrade("Advanced Medic Facilities", flags=Upgrade.Flags.TypeOther),
            Upgrade("Restoration", flags=Upgrade.Flags.TypeOther),
            Upgrade("A-13 Flash Grenade Launcher", flags=Upgrade.Flags.TypeOther),
            Upgrade("Stabilizer Medpacks", flags=Upgrade.Flags.TypeOther),
            Upgrade("Medpack", flags=Upgrade.Flags.TypeOther),
            Upgrade("Optical Flare", flags=Upgrade.Flags.TypeOther),
        ),
    ),
    Unit(
        faction=Faction.Terran,
        name="Point Defense Drone",
        unit_type=UnitType.Other,
        size=None,
        keywords=("Raynor's Raiders",),
        shield=None,
        speed=Speed(0, 0),
        evade=6,
        armour=6,
        hit_points=3,
        weapons=(),
        squad=(Squad(Range(1, 1), 0, 0),),
        tags=Tag.Armoured | Tag.Flying | Tag.Mechanical,
        upgrades=(
            Upgrade("Point Defense Laser", flags=Upgrade.Flags.TypeOther),
            Upgrade("Gliding", flags=Upgrade.Flags.TypeOther),
            Upgrade("Structure", flags=Upgrade.Flags.TypeOther),
        ),
    ),
    Unit(
        faction=Faction.Terran,
        name="Raynor's Raider (Marine)",
        unit_type=UnitType.Core,
        size=2,
        keywords=("Raynor's Raiders",),
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
            Upgrade("Raiders Roll!", flags=Upgrade.Flags.TypeOther),
            Upgrade("Rapid Reinforcements", flags=Upgrade.Flags.TypeOther),
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
    Unit(
        faction=Faction.Terran,
        name="Siege Tank",
        unit_type=UnitType.Elite,
        size=2,
        keywords=(),
        shield=None,
        speed=Speed(7, 7),
        evade=None,
        armour=5,
        hit_points=14,
        weapons=(
            Weapon("Twin Cannon", 12, Tag.Ground, 8, 3, Tag.Armoured, SurgeDie.D6, 1, tags=Tag.PierceArmoured2),
            Weapon("Shock Cannon", 18, Tag.Ground, "BT:Shock Cannon+4", 4, Tag.Light | Tag.Armoured, SurgeDie.BT, 1, exchange_for="Twin Cannon"),
            Weapon("Rolling Over", "E", Tag.Ground, 2, 2, None, None, 1),
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
        squad=(Squad(Range(1, 1), 2, 220),),
        tags=Tag.Mechanical | Tag.Ground | Tag.Armoured,
        upgrades=(
            Upgrade(
                "Aftershock Rounds",
                message=(
                    "When this Unit has the SIEGE MODE Status, its Damage characteristic is treated as equal to "
                    "the Size characteristic of the current target Unit (to a minimum of 1)."
                ),
                cost=Cost(),
                flags=Upgrade.Flags.TypeOther | Upgrade.Flags.ReplacedByWorkaround,
            ),
            Upgrade(
                "! Shock Cannon / Aftershock Rounds",
                message=(
                    "When this Unit has the SIEGE MODE Status, its Damage characteristic is treated as equal to "
                    "the Size characteristic of the current target Unit (to a minimum of 1)."
                ),
                apply={
                    Hook.ModifyOwner: lambda unit: Upgrade.activate_weapon(unit, "Shock Cannon"),
                    Hook.ModifyDamage: _aftershock_rounds,
                },
                flags=Upgrade.Flags.Workaround,
            ),
            Upgrade("Large", flags=Upgrade.Flags.TypeOther),
            Upgrade(
                "Heavy Plating",
                message="When this Unit resolves an Armour Roll, it gains TOUGH (1), provided it does not currently have the SIEGE MODE Status.",
                cost=Cost(),
                apply=lambda unit: unit.add_tag(Tag.Tough1),
            ),
            Upgrade(
                "Mode Transformation",
                message=(
                    "The active Unit gains or loses the SIEGE MODE Status. "
                    "While this Unit has the SIEGE MODE Status, its Size characteristic is treated as if it was 3."
                ),
                cost=Cost(points=1),
                flags=Upgrade.Flags.TypeDefensive,
                apply=lambda unit: unit.set_size(3),
            ),
            Upgrade("Coordinated Strike", flags=Upgrade.Flags.TypeOther),
            Upgrade("Indomitable", flags=Upgrade.Flags.TypeOther),
            Upgrade("Point Blank", flags=Upgrade.Flags.TypeOther),
            Upgrade(
                "Shaped Blast",
                message="Once per Game. When this Unit declares a Ranged Attack action. If this Unit has SIEGE MODE Status, its weapon gains PINPOINT and LOCKED IN (4).",
                cost=Cost(10),
                apply=lambda unit: unit.weapon("Shock Cannon").buff_roa(4) or unit.weapon("Shock Cannon").add_tag(Tag.Pinpoint | Tag.LockedIn4),
            ),
            Upgrade("Smart Shells", flags=Upgrade.Flags.TypeOther),
        ),
    ),
    Unit(
        faction=Faction.Terran,
        name="Auto-Turret",
        unit_type=UnitType.Other,
        size=2,
        keywords=(),
        shield=None,
        speed=Speed(0, 0),
        evade=None,
        armour=5,
        hit_points=3,
        weapons=(Weapon("Gauss Cannon", 8, Tag.Flying | Tag.Ground, 6, 3, None, None, 1, tags=Tag.Pinpoint),),
        squad=(Squad(Range(1, 1), 0, 0),),
        tags=Tag.Mechanical | Tag.Ground | Tag.Armoured,
        upgrades=(
            Upgrade("Timed Life", message="Remove this Unit at the End of the Round.", cost=Cost(), flags=Upgrade.Flags.TypeOther),
            Upgrade(
                "Structure",
                message=(
                    "This Unit cannot be Activated in any Phase and cannot perform actions. Additionally, its Current Supply Value is treated as 0, "
                    "and it can never Control or Contest Mission Markers, ignoring the standard Zero Supply Exception. "
                    "This Unit cannot be a target of an ability, unless stated otherwise."
                ),
                cost=Cost(),
                flags=Upgrade.Flags.TypeOther,
            ),
            Upgrade(
                "Overwatch",
                message='Use when an Enemy Unit ends its Activation Within 8" of this Unit. This Unit immediately performs a Ranged Attack against that Enemy Unit.',
                cost=Cost(),
                flags=Upgrade.Flags.TypeOther,
            ),
            Upgrade(
                "! Explosive Shrapnel Shells / Raven",
                message=(
                    "Apply Explosive Shrapnel Shells purchased for the Raven that deployed this Auto-Turret: this Unit's Gauss Cannon gains Surge "
                    "Type: Light and S-Dice: D3+1."
                ),
                apply=lambda unit: unit.weapon("Gauss Cannon").add_surge_tag(Tag.Light) or unit.weapon("Gauss Cannon").set_surge_die(SurgeDie.D3P1),
                flags=Upgrade.Flags.Workaround,
            ),
        ),
    ),
    Unit(
        faction=Faction.Terran,
        name="Holo Decoy",
        unit_type=UnitType.Other,
        size=2,
        keywords=(),
        shield=None,
        speed=Speed(7, 7),
        evade=6,
        armour=6,
        hit_points=1,
        weapons=(),
        squad=(Squad(Range(1, 1), 0, 0),),
        tags=Tag.Biological | Tag.Ground | Tag.Psionic,
        upgrades=(
            Upgrade(
                "Lethal Hologram",
                message='All Weapons of Friendly Units targeting an Enemy Unit Within 4" of this Unit gain PRECISION (1).',
                cost=Cost(),
                flags=Upgrade.Flags.TypeOther | Upgrade.Flags.ReplacedByWorkaround,
            ),
            Upgrade("Timed Life", message="Remove this Unit at the End of the Round.", cost=Cost(), flags=Upgrade.Flags.TypeOther),
            Upgrade(
                "Decoy",
                message=(
                    "This Unit is never Engaged. It cannot Engage Enemy Units, cannot be Engaged by Enemy Units and cannot perform a Charge Action. "
                    "This Unit cannot be the target of an ability, unless stated otherwise. It can never Control or Contest Mission Markers."
                ),
                cost=Cost(),
                flags=Upgrade.Flags.TypeOther,
            ),
            Upgrade(
                "Surprise!",
                message="At the End of the Round, you can set a Friendly Nova Stealth Mode or Nova Assault Mode in Coherency with this Unit.",
                cost=Cost(),
                flags=Upgrade.Flags.TypeOther,
            ),
        ),
    ),
    Unit(
        faction=Faction.Terran,
        name="Nova Assault Mode",
        unit_type=UnitType.Hero,
        size=2,
        keywords=(),
        shield=None,
        speed=Speed(7, 7),
        evade=5,
        armour=5,
        hit_points=8,
        weapons=(
            Weapon("Hellfire Shotgun", 8, Tag.Ground, 3, 4, Tag.Light, SurgeDie.D3, 2, tags=Tag.AntiEvade1 | Tag.BurstFire),
            Weapon("Monomolecular Blade", "E", Tag.Ground, 8, 3, Tag.Light | Tag.Armoured, SurgeDie.D6, 1),
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
        squad=(Squad(Range(1, 1), 1, 260),),
        tags=Tag.Biological | Tag.Ground | Tag.Psionic | Tag.Unique,
        upgrades=(
            Upgrade(
                "Battle Preparation",
                message="During Army Building, your army cannot include both the Nova Assault Mode Unit and the Nova Stealth Mode Unit.",
                cost=Cost(),
                flags=Upgrade.Flags.TypeOther,
            ),
            Upgrade(
                "Ghost Visor",
                message='While Enemy Units are Within 6" of this Unit, they lose the HIDDEN Status.',
                cost=Cost(),
                flags=Upgrade.Flags.TypeOther,
            ),
            Upgrade(
                "Holo Decoy",
                message="Resolve the SUMMON (Holo Decoy) effect. Then, Holo Decoy may immediately perform a Move action.",
                cost=Cost(points=1),
                flags=Upgrade.Flags.TypeOther,
            ),
            Upgrade(
                "Super Stimpack",
                message="This Unit gains BUFF Speed (2). Additionally, all its Weapons gain PRECISION (2).",
                cost=Cost(points=1),
                apply=lambda unit: unit.weapon("@type_letter!=A").add_tag(Tag.Precision2),
            ),
            Upgrade(
                '! Activate BURST FIRE (3) on Hellfire Shotgun - target within 4"',
                lambda unit: unit.weapon("Hellfire Shotgun").buff_roa(3),
                flags=Upgrade.Flags.Workaround,
            ),
            Upgrade(
                "Phase Reactor Suit",
                message="If Unengaged, resolve the PLACE (6) effect.",
                cost=Cost(points=1),
                flags=Upgrade.Flags.TypeOther,
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
        faction=Faction.Terran,
        name="Nova Stealth Mode",
        unit_type=UnitType.Hero,
        size=2,
        keywords=(),
        shield=None,
        speed=Speed(7, 7),
        evade=5,
        armour=5,
        hit_points=8,
        weapons=(
            Weapon("C-20A Canister Rifle", 12, Tag.Flying | Tag.Ground, 4, 3, None, None, 2, tags=Tag.CriticalHit2),
            Weapon("Combat Knife", "E", Tag.Ground, 3, 5, None, None, 1),
        ),
        squad=(Squad(Range(1, 1), 1, 240),),
        tags=Tag.Biological | Tag.Ground | Tag.Psionic | Tag.Unique,
        upgrades=(
            Upgrade(
                "Battle Preparation",
                message="During Army Building, your army cannot include both the Nova Assault Mode Unit and the Nova Stealth Mode Unit.",
                cost=Cost(),
                flags=Upgrade.Flags.TypeOther,
            ),
            Upgrade(
                "Tactical Stealth Suit",
                message="After this Unit fully resolves an Action, it gains the HIDDEN Status.",
                cost=Cost(),
                flags=Upgrade.Flags.TypeOther,
            ),
            Upgrade(
                "Ghost Visor",
                message='While Enemy Units are Within 6" of this Unit, they lose the HIDDEN Status.',
                cost=Cost(),
                flags=Upgrade.Flags.TypeOther,
            ),
            Upgrade(
                "Super Stimpack",
                message="This Unit gains BUFF Speed (2). Additionally, all its Weapons gain PRECISION (2).",
                cost=Cost(points=1),
                apply=lambda unit: unit.weapon("@type_letter!=A").add_tag(Tag.Precision2),
            ),
            Upgrade(
                "Holo Decoy",
                message="Resolve the SUMMON (Holo Decoy) effect. Then, Holo Decoy may immediately perform a Move action.",
                cost=Cost(points=1),
                flags=Upgrade.Flags.TypeOther,
            ),
            Upgrade(
                "Operational Efficiency",
                message=(
                    "After this Unit fully resolves a Ranged Attack with its C-20A Canister Rifle, if the target Enemy Unit was Destroyed or its Current "
                    "Supply Value was reduced, the active player may return one of their Exhausted non-Unique Tactical Cards to its Ready state."
                ),
                cost=Cost(),
                flags=Upgrade.Flags.TypeOther,
            ),
            Upgrade(
                "Head Shot",
                message=(
                    "Once Per Game. While this Unit is Unengaged and has the Stationary Status, when it makes a Ranged Attack with its C-20A Canister "
                    "Rifle, treat that weapon's Damage characteristic as 3, and it gains CONCENTRATED FIRE (1)."
                ),
                cost=Cost(points=1),
                apply=lambda unit: unit.weapon("C-20A Canister Rifle").set_damage(3) or unit.weapon("C-20A Canister Rifle").add_tag(Tag.ConcentratedFire1),
            ),
        ),
    ),
    Unit(
        faction=Faction.Terran,
        name="Raven",
        unit_type=UnitType.Support,
        size=None,
        keywords=(),
        shield=None,
        speed=Speed(7, 7),
        evade=6,
        armour=5,
        hit_points=8,
        weapons=(
            Weapon("Railguns", 12, Tag.Ground, 4, 3, None, None, 1),
            Weapon(
                "! Seeker Missile",
                "A",
                Tag.Flying | Tag.Ground,
                4,
                None,
                None,
                None,
                2,
                tags=Tag.Sidearm | Tag.Hits,
                flags=Weapon.Flags.SimulationProfile,
            ),
        ),
        squad=(Squad(Range(1, 1), 1, 170),),
        tags=Tag.Mechanical | Tag.Flying | Tag.Light,
        upgrades=(
            Upgrade(
                "Detection",
                message='While Enemy Units are Within 6" of this Unit, they lose the HIDDEN Status.',
                cost=Cost(),
                flags=Upgrade.Flags.TypeOther,
            ),
            Upgrade(
                "Corvid Reactor",
                message="This Unit may resolve its first Special Ability with the CP cost reduced by 1 if it targets the closest Enemy Unit.",
                cost=Cost(30),
                flags=Upgrade.Flags.TypeOther,
            ),
            Upgrade(
                "Internal Tech Module",
                message=(
                    "When this Unit is nominated to deploy from Reserves, it may Deploy from any table edge that is not a player's Entry Edge. "
                    'This Unit cannot be set Within 8" of any Enemy model.'
                ),
                cost=Cost(20),
                flags=Upgrade.Flags.TypeOther,
            ),
            Upgrade(
                "Deploy Auto-Turret",
                message='Set a Friendly Auto-Turret Unit Within 6", and not Within the Engagement Range of any Enemy Unit.',
                cost=Cost(points=1),
                flags=Upgrade.Flags.TypeOther,
            ),
            Upgrade(
                "Anti-Armour Missile",
                message='Select one Enemy Unit Within 12". Apply DEBUFF Armour (1).',
                cost=Cost(points=1),
                apply={Hook.ModifyOpponent: lambda unit: unit.debuff_armour(1)},
                flags=Upgrade.Flags.TypeOffensive,
            ),
            Upgrade(
                "Seeker Missile",
                apply=lambda unit: unit.activate_weapon("! Seeker Missile"),
                message=(
                    "Select one Enemy Unit Within 12\". At the End of the Assault Phase, if that Enemy Unit has the Stationary Status or it is Within 8'' "
                    "of this Unit, it suffers HITS 4 (2). If that Unit is Engaged, it is eligible to make an Evade Roll against these hits."
                ),
                cost=Cost(20, points=1),
            ),
            Upgrade(
                "Explosive Shrapnel Shells",
                message="The Gauss Cannon of the Auto-Turret set by this Unit gains Surge Type: Light and S-Dice: D3+1.",
                cost=Cost(10),
                flags=Upgrade.Flags.TypeOther | Upgrade.Flags.ReplacedByWorkaround,
            ),
        ),
    ),
    Unit(
        faction=Faction.Terran,
        name="Sabotage Drone",
        unit_type=UnitType.Other,
        size=1,
        keywords=(),
        shield=None,
        speed=Speed(0, 0),
        evade=6,
        armour=6,
        hit_points=3,
        weapons=(
            Weapon(
                "! Have a Nice Day",
                3,
                Tag.Flying | Tag.Ground,
                5,
                None,
                None,
                None,
                1,
                tags=Tag.Sidearm | Tag.Hits,
                flags=Weapon.Flags.SimulationProfile,
            ),
            Weapon(
                "! Have a Nice Day / Structure",
                3,
                Tag.Flying | Tag.Ground,
                10,
                None,
                None,
                None,
                1,
                exchange_for="! Have a Nice Day",
                tags=Tag.Sidearm | Tag.Hits,
                flags=Weapon.Flags.SimulationProfile,
            ),
        ),
        squad=(Squad(Range(1, 1), 0, 0),),
        tags=Tag.Mechanical | Tag.Ground | Tag.Armoured,
        upgrades=(
            Upgrade(
                "Structure",
                message=(
                    "This Unit cannot be Activated in any Phase and cannot perform actions. Additionally, its Current Supply Value is treated as 0, "
                    "and it can never Control or Contest Mission Markers, ignoring the standard Zero Supply Exception. "
                    "This Unit cannot be a target of an ability, unless stated otherwise."
                ),
                cost=Cost(),
                flags=Upgrade.Flags.TypeOther,
            ),
            Upgrade(
                "Have a Nice Day",
                message=(
                    'At the End of the Assault Phase, target each Unit Within 3" of this Unit (including Units with the Structure ability) suffers HITS 5 '
                    "(1). If an affected Unit has the Structure ability, that Unit suffers an additional HITS 5 (1)."
                ),
                cost=Cost(),
                flags=Upgrade.Flags.TypeOther | Upgrade.Flags.ReplacedByWorkaround,
            ),
            Upgrade(
                "! Have a Nice Day / Structure",
                message=("Use this profile to resolve the combined HITS 10 (1) against one affected Structure Unit."),
                cost=Cost(),
                apply=Upgrade.activate_weapon,
                flags=Upgrade.Flags.Workaround,
            ),
        ),
    ),
    Unit(
        faction=Faction.Terran,
        name="Spec Ops Marauder (Marauder)",
        unit_type=UnitType.Core,
        size=2,
        keywords=("Terran", "Nova Covert Ops"),
        shield=None,
        speed=Speed(4, 7),
        evade=6,
        armour=4,
        hit_points=5,
        weapons=(
            Weapon("Quad K12", 12, Tag.Ground, 3, 3, Tag.Armoured, SurgeDie.D3, 1, tags=Tag.PierceArmoured2),
            Weapon("Strike", "E", Tag.Ground, 3, 4, None, None, 1),
        ),
        squad=(Squad(Range(2, 2), 1, 230),),
        tags=Tag.Biological | Tag.Ground | Tag.Armoured,
        upgrades=(
            Upgrade(
                "Spec Ops Armour",
                message="This Unit gains the HIDDEN Status until it performs another action.",
                cost=Cost(points=1),
                flags=Upgrade.Flags.TypeOther,
            ),
            Upgrade(
                "Commando Stimpack",
                message="This Unit gains BUFF Speed (3). Additionally, its Quad K12 and all Close Combat Weapons gain PRECISION (2).",
                cost=Cost(points=1),
                apply=lambda unit: unit.weapon(["Quad K12", "@range==E"]).add_tag(Tag.Precision2),
            ),
            Upgrade(
                "Magrail Munitions",
                message="This Unit's first Attack in the game with its Quad K12 gains PIERCE Armoured (3).",
                cost=Cost(),
                apply=lambda unit: unit.weapon("Quad K12").add_tag(Tag.PierceArmoured3),
            ),
            Upgrade(
                "Suppression Shells",
                message='When an Enemy declares a Charge against a Friendly Unit Within 8", that Enemy gains DEBUFF Speed (3).',
                cost=Cost(points=1),
                flags=Upgrade.Flags.TypeOther,
            ),
        ),
    ),
)


def apply_jim_raynors_orders(unit: Unit) -> list[Upgrade]:
    eligible_weapons = [weapon for weapon in unit.weapons if weapon.type_letter in ("R", "E")]
    if Tag.Biological not in unit.tags or not eligible_weapons:
        return []

    special_tags = Tag.Sidearm | Tag.Specialist
    has_special_weapon = any(weapon.tags & special_tags for weapon in eligible_weapons)
    has_multiple_base_weapons_of_one_type = any(
        sum(weapon.type_letter == type_letter and not weapon.exchange_for for weapon in eligible_weapons) > 1 for type_letter in ("R", "E")
    )
    use_individual_orders = has_special_weapon and has_multiple_base_weapons_of_one_type

    if not use_individual_orders:
        weapon_query = "*" if len(eligible_weapons) == len(unit.weapons) else [weapon.name for weapon in eligible_weapons]
        return [
            Upgrade(
                "! Orders / Jim Raynor",
                message='Apply active Orders of a friendly Jim Raynor within 8" - Unit’s first used weapon gains the CRITICAL HIT (2)',
                apply=lambda mustered_unit, query=weapon_query: mustered_unit.weapon(query).add_tag(Tag.CriticalHit2),
                flags=Upgrade.Flags.Workaround,
            )
        ]

    weapons_by_name = {weapon.name: weapon for weapon in eligible_weapons}
    grouped_names = set()
    weapon_groups = []
    for weapon in eligible_weapons:
        if weapon.name in grouped_names:
            continue

        base_weapon = weapons_by_name.get(weapon.exchange_for, weapon)
        can_group = not (weapon.tags | base_weapon.tags) & special_tags and weapon.type_letter == base_weapon.type_letter
        if can_group:
            group = [
                base_weapon,
                *[
                    alternative
                    for alternative in eligible_weapons
                    if alternative.exchange_for == base_weapon.name
                    and alternative.type_letter == base_weapon.type_letter
                    and not alternative.tags & special_tags
                ],
            ]
        else:
            group = [weapon]

        group = [grouped_weapon for grouped_weapon in group if grouped_weapon.name not in grouped_names]
        grouped_names.update(grouped_weapon.name for grouped_weapon in group)
        weapon_groups.append(group)

    def make_orders_upgrade(group: list[Weapon]) -> Upgrade:
        weapon_names = [weapon.name for weapon in group]
        return Upgrade(
            f"! Orders / Jim Raynor / {'/'.join(weapon_names)}",
            message='Apply active Orders of a friendly Jim Raynor within 8" - Unit’s first used weapon gains the CRITICAL HIT (2)',
            apply=lambda mustered_unit: mustered_unit.weapon(weapon_names).add_tag(Tag.CriticalHit2),
            flags=Upgrade.Flags.Workaround,
        )

    return [make_orders_upgrade(group) for group in weapon_groups]


def _apply_common_skills(units):
    lethal_hologram = Upgrade(
        "! Lethal Hologram / Holo Decoy",
        message='Apply Lethal Hologram of a friendly Holo Decoy: all Weapons targeting an Enemy Unit Within 4" of it gain PRECISION (1).',
        apply=_apply_lethal_hologram,
        flags=Upgrade.Flags.Workaround,
    )

    for unit in units:
        if unit.is_structure:
            to_add = []
        else:
            to_add = apply_jim_raynors_orders(unit)

        if any(weapon.hit is not None for weapon in unit.weapons):
            to_add.append(lethal_hologram)

        unit.upgrades = (*unit.upgrades, *to_add)

    return units


TERRAN_UNITS = _apply_common_skills(_TERRAN_UNITS)
