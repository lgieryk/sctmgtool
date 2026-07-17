# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Łukasz Gieryk

from enum import Flag, Enum, auto
from typing import NamedTuple, Callable
from dataclasses import dataclass
import enum

# pylint: disable=invalid-name


class Faction(Flag):
    Zerg = auto()
    Terran = auto()
    Protoss = auto()


class Tag(Flag):
    # fmt: off
    _None           = 0b0000000000000000000000000000000000000000000000
    Biological      = 0b0000000000000000000000000000000000000000000001
    Mechanical      = 0b0000000000000000000000000000000000000000000010
    Flying          = 0b0000000000000000000000000000000000000000000100
    Ground          = 0b0000000000000000000000000000000000000000001000
    Light           = 0b0000000000000000000000000000000000000000010000
    Armoured        = 0b0000000000000000000000000000000000000000100000
    Psionic         = 0b0000000000000000000000000000000000000001000000
    Sidearm         = 0b0000000000000000000000000000000000000010000000
    Specialist      = 0b0000000000000000000000000000000000000100000000
    _AntiEvade      = 0b0000000000000000000000000000000000001000000000
    AntiEvade1      = 0b0000000000000000000000000000000000011000000000
    AntiEvade2      = 0b0000000000000000000000000000000000101000000000
    AntiEvade3      = 0b0000000000000000000000000000000001001000000000
    _Precision      = 0b0000000000000000000000000000000010000000000000
    Precision1      = 0b0000000000000000000000000000000110000000000000
    Precision2      = 0b0000000000000000000000000000001010000000000000
    Precision3      = 0b0000000000000000000000000000010010000000000000
    Pinpoint        = 0b0000000000000000000000000000100000000000000000
    _LockedIn       = 0b0000000000000000000000000001000000000000000000
    LockedIn6       = 0b0000000000000000000001000001000000000000000000
    _PierceArmoured = 0b0000000000000000000010000000000000000000000000
    PierceArmoured2 = 0b0000000000000000001010000000000000000000000000
    PierceArmoured3 = 0b0000000000000000010010000000000000000000000000
    _PierceLight    = 0b0000000000000000100000000000000000000000000000
    PierceLight2    = 0b0000000000000010100000000000000000000000000000
    _Tough          = 0b0000000000001000000000000000000000000000000000
    Tough1          = 0b0000000000011000000000000000000000000000000000
    Tough2          = 0b0000000000101000000000000000000000000000000000
    Unique          = 0b0000000001000000000000000000000000000000000000
    IndirectFire    = 0b0000000010000000000000000000000000000000000000
    Bulky           = 0b0000000100000000000000000000000000000000000000
    BurstFire       = 0b0000001000000000000000000000000000000000000000
    _CriticalHit    = 0b0000010000000000000000000000000000000000000000
    CriticalHit2    = 0b0001010000000000000000000000000000000000000000
    Instant         = 0b0010000000000000000000000000000000000000000000
    # fmt: on

    def __str__(self):
        masked_value = self.value & ~Tag(Tag._AntiEvade | Tag._Precision | Tag._PierceArmoured | Tag._Tough).value
        first = True
        ret = ""
        for name, member in Tag.__members__.items():
            if not name.startswith("_") and member.value & masked_value:
                if not first:
                    ret += "|"
                first = False
                ret += name
        return ret

    @staticmethod
    def _lsb(val):
        return (val & -val).bit_length() - 1

    def sibling_bits(self):
        siblings = 0
        for _name, member in Tag.__members__.items():
            if member.value & self.value:
                siblings |= member.value
        return siblings

    def _extract(self, tag):
        if tag not in self:
            return 0
        masked = ~((tag.value << 1) - 1) & self.value
        return Tag._lsb(masked) - Tag._lsb(tag.value)

    def anti_evade(self):
        return self._extract(Tag._AntiEvade)

    def precision(self):
        return self._extract(Tag._Precision)

    def pierce_armoured(self):
        return self._extract(Tag._PierceArmoured)

    def pierce_light(self):
        return self._extract(Tag._PierceLight)

    def tough(self):
        return self._extract(Tag._Tough)

    def critical_hit(self):
        return self._extract(Tag._CriticalHit)


class SurgeDie(Enum):
    @enum.nonmember
    class _Inner(NamedTuple):
        d3: int
        d6: int
        add: int

    D3 = _Inner(1, 0, 0)
    D6 = _Inner(0, 1, 0)
    D3P1 = _Inner(1, 0, 1)

    def __str__(self):
        return self.name


@dataclass
class Weapon:
    name: str
    range: int | str
    target: Tag
    rate_of_attack: int
    hit: int
    surge: Tag
    surge_die: SurgeDie
    damage: int
    exchange_for: str = ""
    # pylint: disable-next=protected-access
    tags: Tag = Tag._None

    def add_tag(self, tag: Tag):
        if tag & self.tags:  # replace the existing value-tag with a new value, e.g., Pierce1 -> Pierce2
            new = Tag(self.tags.value & ~tag.sibling_bits())
            self.tags = new
        self.tags |= tag

    def add_surge_tag(self, tag: Tag):
        if self.surge is None:
            self.surge = tag
        else:
            self.surge |= tag

    def set_surge_die(self, die: SurgeDie):
        self.surge_die = die

    def buff_roa(self, val: int):
        self.rate_of_attack += val

    def buff_hit(self, val: int):
        self.hit = max(2, self.hit - val)

    def set_damage(self, val: int):
        self.damage = val

    @property
    def type_letter(self):
        return self.range if self.range in ("E", "C") else "R"

    def __str__(self):
        ef = f" FOR:{self.exchange_for}" if self.exchange_for != "" else ""
        surge = f" {str(self.surge or ''):<16} {str(self.surge_die or ''):<4}"

        if Tag.Flying in self.target and Tag.Ground in self.target:
            tgt = "GF"
        else:
            tgt = "G " if Tag.Ground in self.target else "F "

        return f"{self.name:<30} {self.range:>2} {tgt} {self.rate_of_attack}D6 {self.hit}+ {surge} DMG:{self.damage} {str(self.tags):<20}{ef}"


class Range(NamedTuple):
    start: int
    stop: int


class Squad(NamedTuple):
    models: Range
    supply: int
    points: int


@dataclass
class Speed:
    unit: int
    model: int

    def __str__(self):
        return f"{self.unit}/{self.model}"


@dataclass
class Cost:
    small: int | None = None
    large: int | None = None
    points: int | None = None

    def __str__(self):
        points = f"/{self.points}P" if self.points else ""
        return f"{self.small or '-'}/{self.large or '-'}{points}"


class Hook(Enum):
    ModifyOwner = auto()
    RollPoolsInitiated = auto()


class Upgrade:
    class Type(Flag):
        Other = auto()
        Defensive = auto()
        Offensive = auto()

    def __init__(self, name: str, /, apply: Callable | dict = None, *, message="", cost=None, upgrade_type=None):
        if apply is Upgrade.activate_weapon:

            def wrapper(unit):
                return Upgrade.activate_weapon(unit, name)

            apply = wrapper
            message = "Upgrade weapon"

        if callable(apply):
            apply = {Hook.ModifyOwner: apply}
        else:
            assert isinstance(apply, dict)

        self.name = name
        self.apply = apply
        self.upgrade_type = upgrade_type
        self.message = message
        self.cost = cost

    def __str__(self):
        return f"{self.name} {self.cost or '-'} {self.message}"

    @staticmethod
    def activate_weapon(unit, weapon_name: str):
        unit.activate_weapon(weapon_name)


@dataclass
class Unit:
    faction: Faction
    name: str
    shield: int
    speed: Speed
    evade: int
    armour: int
    hit_points: int
    weapons: tuple[Weapon]
    squad: tuple[Squad]
    tags: Tag
    upgrades: tuple[Upgrade]

    def __str__(self):
        return f"{self.name} SHLD:{self.shield} EVA:{self.evade}+ ARM:{self.armour}+ HP:{self.hit_points} {self.tags}"
