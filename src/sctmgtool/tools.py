# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Łukasz Gieryk

from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict
from typing import NamedTuple
import random
import re
import operator
import copy
import logging
from sctmgtool.base import Unit, Weapon, Tag, Upgrade, Hook
from sctmgtool.hooks import PoolHookArgs, RollHookArgs


D6POP = (1, 2, 3, 4, 5, 6)


class DicePool:
    def __init__(self, dice: list[int]):
        self.dice = list(dice)

    @staticmethod
    def empty(_limit: int = None):
        return DicePool([])

    @staticmethod
    def n_dice(n: int):
        dice = [0] * n
        return DicePool(dice)

    def size(self):
        return len(self.dice)

    def roll(self):
        self.dice = random.choices(D6POP, k=len(self.dice))

    def extend(self, dice: list[int]):
        self.dice.extend(dice)

    @staticmethod
    def _default_predicate(_x):
        return True

    @staticmethod
    def auto_fail_pass_predicate(pred):
        def _wrap(roll_val: int):
            return roll_val == 6 or (roll_val != 1 and pred(roll_val))

        return _wrap

    def transfer_dice_to(self, target_pool: "DicePool", pred: callable = None, up_to: int | None = None):
        assert isinstance(target_pool, DicePool)

        if pred is None:
            pred = DicePool._default_predicate

        if up_to is None:
            up_to = len(self.dice)

        selected = []
        remaining = []
        count = 0

        for die in self.dice:
            if pred(die) and count < up_to:
                selected.append(die)
                count += 1
            else:
                remaining.append(die)

        self.dice = remaining
        target_pool.extend(selected)

    def __repr__(self):
        return f"{self.size()}D6: " + ", ".join(str(d) for d in self.dice)


class Query:
    _ops = {
        "<": operator.lt,
        "<=": operator.le,
        ">": operator.gt,
        ">=": operator.ge,
        "==": operator.eq,
        "!=": operator.ne,
    }

    def __init__(self, container, query: list | str):
        if isinstance(query, str):
            query = [query]

        self.items = []
        for q in query:
            if q == "*":
                found = list(container)
            else:
                if q[0] == "@":
                    attr, _op, value = re.match(r"(.*?)([<>=!]+)(.*)", q[1:]).groups()
                else:
                    attr, _op, value = ("name", "==", q)
                op = Query._ops[_op]
                found = [e for e in container if op(getattr(e, attr), value)]

            assert len(found) > 0, f"Query '{q}' found nothing"
            self.items += found

    def __getattr__(self, func_name):
        def method(*args, **kwargs):
            for item in self.items:
                func = getattr(item, func_name)
                func(*args, **kwargs)

        return method


@dataclass
class WeaponBatch:
    model_num: int
    weapon: Weapon

    def __repr__(self):
        return f"{self.model_num}x{self.weapon.name}"


class Fingerprint(NamedTuple):
    unit_name: str
    squad_size: int
    configuration: int


@dataclass
class MusteredUnit(Unit):
    models: int = 0
    weapon_batches: list[WeaponBatch] = field(default_factory=list)
    evade_reroll: str = ""
    fingerprint: Fingerprint = None

    def weapon(self, query: list | str):
        return Query(self.weapons, query)

    def batch(self, name: str):
        return next((b for b in self.weapon_batches if b.weapon.name == name), None)

    def add_tag(self, tag: Tag):
        self.tags |= tag

    def buff_armour(self, value: int):
        self.armour = max(2, self.armour - value)

    def buff_hit_points(self, value: int):
        self.hit_points += value

    def buff_evade(self, value: int):
        self.evade = max(2, self.evade - value)

    def grant_reroll(self, rt: str):
        for letter in rt:
            assert letter in "REC"
            if letter not in self.evade_reroll:
                self.evade_reroll += letter

    @staticmethod
    def make_fingerprint(prototype: Unit, config: dict[str, bool], attacker: bool) -> Fingerprint:
        def _key(var):
            return f"{var}" if attacker else f"{var}_def"

        configuration = 0
        for i, upgrade in enumerate(prototype.upgrades):
            if config.get(upgrade.name, False):
                is_offensive = upgrade.upgrade_type is None or Upgrade.Type.Offensive in upgrade.upgrade_type
                is_defensive = upgrade.upgrade_type is None or Upgrade.Type.Defensive in upgrade.upgrade_type
                if (attacker and is_offensive) or (not attacker and is_defensive):
                    configuration |= 1 << i

        num_models = config.get(_key("_squad_size"), prototype.squad[0].models.stop)
        return Fingerprint(prototype.name, num_models, configuration)

    @staticmethod
    def make(prototype: Unit, config: dict[str, bool], is_attacker: bool = True) -> "MusteredUnit":
        proto_copy = copy.deepcopy(prototype)
        unit = MusteredUnit(**vars(proto_copy))
        unit.fingerprint = MusteredUnit.make_fingerprint(prototype, config, is_attacker)
        unit.models = unit.fingerprint.squad_size

        def upgrade_exists(weapon_name):
            return any(weapon_name == u.name for u in unit.upgrades)

        default_added = []

        # Enable the 1st non-upgrade weapon of each type (clash, melee, ranged) and all sidearms
        for w in unit.weapons:
            if upgrade_exists(w.name):
                continue

            if w.tags & Tag.Sidearm:
                pass
            elif w.type_letter() not in default_added:
                default_added.append(w.type_letter())
            else:
                continue

            unit.weapon_batches.append(WeaponBatch(unit.models, w))

        # Determine active upgrades and apply those affecting the unit directly
        unit.upgrades = tuple(up for i, up in enumerate(unit.upgrades) if unit.fingerprint.configuration & (1 << i))
        for up in unit.upgrades:
            for hook_type, apply in up.apply.items():
                if hook_type == Hook.ModifyOwner:
                    apply(unit)

        return unit

    def activate_weapon(self, name: str):
        w = next(w for w in self.weapons if w.name == name)

        if w.exchange_for != "":
            batch = self.batch(w.exchange_for)
            assert batch is not None
            count = 1 if w.tags & Tag.Specialist else batch.model_num

            if batch.model_num > count:
                batch.model_num -= count
            else:
                self.weapon_batches.remove(batch)

            self.weapon_batches.append(WeaponBatch(count, w))
        elif w.tags is not None and w.tags & Tag.Sidearm:
            count = 1 if w.tags & Tag.Specialist else self.models
            self.weapon_batches.append(WeaponBatch(count, w))
        else:
            raise RuntimeError("Unexpected weapon configuration")

    def num_killed(self, damage: int):
        shielded = min((self.shield if self.shield is not None else 0), damage)
        damage = damage - shielded

        kills = int(damage / self.hit_points)
        kills = min(kills, self.models)  # trim excess kills

        return kills


class HookContext:
    class _H(NamedTuple):
        owner: MusteredUnit
        apply: callable

    def __init__(self, units: list[MusteredUnit] = None):
        self.hooks = defaultdict(list)
        if units is None:
            return
        for unit in units:
            for upgrade in unit.upgrades:
                for hook_type, action in upgrade.apply.items():
                    self.hooks[hook_type].append(self._H(unit, action))

    def call_hooks(self, hook_type, *args, **kwargs):
        for hook in self.hooks[hook_type]:
            hook.apply(hook.owner, *args, **kwargs)


def roll_surge(weapon: Weapon, defender: MusteredUnit):
    if weapon.surge is None:
        return 0
    if not any(tags in defender.tags for tags in weapon.surge):
        return 0
    roll_params = weapon.surge_die.value
    return sum(map(lambda x: (x + 1) // 2, random.choices(D6POP, k=roll_params.d3))) + sum(random.choices(D6POP, k=roll_params.d6)) + roll_params.add


def roll_damage(attacker: MusteredUnit, batch: WeaponBatch, defender: MusteredUnit, ctx: HookContext = HookContext()) -> int:
    # pylint: disable=protected-access

    afp = DicePool.auto_fail_pass_predicate

    attack_pool = DicePool.n_dice(batch.model_num * batch.weapon.rate_of_attack)
    armour_pool = DicePool.empty()
    damage_pool = DicePool.empty()
    discard_pool = DicePool.empty()

    php = PoolHookArgs(attack_pool, armour_pool, damage_pool, discard_pool)
    ctx.call_hooks(Hook.RollPoolsInitiated, RollHookArgs(attacker, batch, defender), php)

    # 1. Roll to hit
    attack_pool.roll()
    attack_pool.transfer_dice_to(armour_pool, afp(lambda x: x >= batch.weapon.hit))

    armour_bypass = DicePool.empty()

    if batch.weapon.tags & Tag._Precision:
        attack_pool.transfer_dice_to(armour_bypass, up_to=batch.weapon.tags.precision())

    # 2. Resolve surge
    surge_result = roll_surge(batch.weapon, defender)
    armour_pool.transfer_dice_to(armour_bypass, up_to=surge_result)

    # TODO: dodge - drop from armour_bypass
    armour_bypass.transfer_dice_to(damage_pool)

    if batch.weapon.tags & Tag._CriticalHit:
        armour_pool.transfer_dice_to(damage_pool, up_to=batch.weapon.tags.critical_hit())

    # 3. Armour rolls
    armour_pool.roll()
    armour_pool.transfer_dice_to(discard_pool, afp(lambda x: x >= defender.armour))
    if defender.tags & Tag._Tough:
        armour_pool.transfer_dice_to(discard_pool, up_to=defender.tags.tough())

    armour_pool.transfer_dice_to(damage_pool)

    # 4. Evade rolls
    if batch.weapon.type_letter() in defender.evade_reroll:
        assert defender.evade is not None
        success_val = defender.evade
        if Tag._AntiEvade & batch.weapon.tags:
            success_val += batch.weapon.tags.anti_evade()
        damage_pool.roll()
        damage_pool.transfer_dice_to(discard_pool, afp(lambda x: x >= success_val))

    dmg_per_hit = batch.weapon.damage
    if batch.weapon.tags & Tag._PierceArmoured:
        if defender.tags & Tag.Armoured:
            dmg_per_hit = batch.weapon.tags.pierce_armoured()
        assert Tag._PierceLight not in batch.weapon.tags
    if batch.weapon.tags & Tag._PierceLight:
        if defender.tags & Tag.Light:
            dmg_per_hit = batch.weapon.tags.pierce_light()

    return damage_pool.size() * dmg_per_hit


class ClashType(Enum):
    # pylint: disable=invalid-name
    Charge = "Charge"
    Ranged = "Ranged"
    CloseCombat = "Close Combat"


def select_weapons(attacker: MusteredUnit, defender: MusteredUnit, clash_type: ClashType) -> list[WeaponBatch]:
    def is_applicable(weapon: Weapon):
        if clash_type == ClashType.Charge:
            return Tag.Ground in defender.tags and weapon.type_letter() == "C"
        elif clash_type == ClashType.CloseCombat:
            return Tag.Ground in defender.tags and weapon.type_letter() == "E"
        else:
            return weapon.type_letter() == "R" and weapon.target & defender.tags

    return [batch for batch in attacker.weapon_batches if is_applicable(batch.weapon)]


def process_unit_list(units):
    for unit in units:
        # Grant the generic evade reroll for units with evade
        if unit.evade is not None:
            unit.upgrades = (*unit.upgrades, Upgrade("! Generic Evade-All", lambda unit: unit.grant_reroll("REC")))

        # Decide if upgrades are offensive or defensive
        for upgrade in unit.upgrades:
            if upgrade.upgrade_type is None:  # and hook is target unit
                w = MusteredUnit.make(unit, config={upgrade.name: True})
                wo = MusteredUnit.make(unit, config={upgrade.name: False})

                if w.weapons != wo.weapons or w.weapon_batches != wo.weapon_batches:
                    upgrade.upgrade_type = Upgrade.Type.Offensive

                w.weapons = wo.weapons = None
                w.weapon_batches = wo.weapon_batches = None
                w.upgrades = wo.upgrades = None
                w.fingerprint = wo.fingerprint = None

                if w != wo:
                    upgrade.upgrade_type = Upgrade.Type.Defensive

                if upgrade.upgrade_type is None:
                    upgrade.upgrade_type = Upgrade.Type.Other
                    logging.warning("Useless upgrade: %s", upgrade.name)

            if Upgrade.Type.Offensive in upgrade.upgrade_type and Upgrade.Type.Defensive in upgrade.upgrade_type:
                raise RuntimeError(f"{upgrade} is both: offensive and defensive; combination not supported")
