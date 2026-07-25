# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Łukasz Gieryk

from typing import NamedTuple

import numpy as np
from matplotlib import ticker
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from sctmgtool.tools import ClashType, HookContext, MusteredUnit, roll_damage, select_weapons


class Histogram(NamedTuple):
    damage: np.ndarray
    kills: np.ndarray


def draw_histogram_subfigure(
    histogram: Histogram,
    damage_axis: Axes,
    kills_axis: Axes,
    clash_type: ClashType,
) -> None:
    damage_axis.clear()
    damage_axis.bar(np.arange(len(histogram.damage)), histogram.damage, width=1.0, alpha=0.6, color="blue", label="Damage")
    damage_axis.set_xticks(np.arange(len(histogram.damage)))
    damage_axis.xaxis.set_tick_params(colors="blue")
    damage_axis.set_xlabel("Damage", color="blue")
    damage_axis.set_ylabel("Probability (%)")
    damage_axis.set_ylim(0, 100)

    if len(histogram.damage) == 1:
        damage_axis.set_xticks([0])
    else:
        damage_axis.xaxis.set_major_locator(ticker.MaxNLocator(integer=True, steps=[1, 2, 5, 10]))

    kills_axis.clear()
    kills_axis.bar(np.arange(len(histogram.kills)), histogram.kills, width=1.0, alpha=0.6, color="red", label="Kills")
    kills_axis.xaxis.set_tick_params(colors="red")
    kills_axis.xaxis.set_label_position("top")
    kills_axis.set_xlabel(f"{clash_type.value} Kills", color="red")

    if len(histogram.kills) == 1:
        kills_axis.set_xticks([0])
    else:
        kills_axis.xaxis.set_major_locator(ticker.MaxNLocator(integer=True, steps=[1, 2, 5, 10]))

    damage_axis.set_zorder(kills_axis.get_zorder() + 1)


def draw_histograms(histograms: dict[ClashType, Histogram], fig_params: dict) -> Figure:
    figure = Figure(**fig_params)

    for index, clash_type in enumerate(ClashType):
        damage_axis = figure.add_subplot(1, len(ClashType), index + 1)
        kills_axis = damage_axis.twiny()
        draw_histogram_subfigure(histograms[clash_type], damage_axis, kills_axis, clash_type)

    figure.tight_layout()
    return figure


def simulate_clash(
    attacker: MusteredUnit,
    defender: MusteredUnit,
    roll_count: int = 10_000,
) -> dict[ClashType, Histogram]:
    damage_limit = defender.models * defender.hit_points + (defender.shield or 0)
    histograms = {}

    context = HookContext(attacker, defender)
    context.apply_opponent_hooks(attacker, defender)

    for clash_type in ClashType:
        damage_samples = []
        batches = select_weapons(attacker, defender, clash_type)

        for _ in range(roll_count):
            total_damage = 0
            for batch in batches:
                total_damage += roll_damage(attacker, batch, defender, context)
            damage_samples.append(total_damage)

        damage_count = np.bincount(np.clip(damage_samples, 0, damage_limit), minlength=damage_limit + 1)
        kills_count = np.bincount([defender.num_killed(damage) for damage in damage_samples], minlength=defender.models + 1)

        histograms[clash_type] = Histogram(
            damage=damage_count / damage_count.sum() * 100,
            kills=kills_count / kills_count.sum() * 100,
        )

    return histograms
