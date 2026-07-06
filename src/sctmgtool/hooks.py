# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Łukasz Gieryk

from typing import NamedTuple, Any


class RollHookArgs(NamedTuple):
    attacker: Any
    weapon_batch: Any
    defender: Any


class PoolHookArgs(NamedTuple):
    attack_pool: Any
    armour_pool: Any
    damage_pool: Any
    discard_pool: Any
