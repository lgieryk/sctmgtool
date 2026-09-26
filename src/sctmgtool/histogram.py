# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Łukasz Gieryk

from typing import NamedTuple

import numpy as np
from matplotlib import ticker
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from sctmgtool.tools import ClashType, HookContext, MusteredUnit, roll_damage, select_weapons

BACKGROUND_COLOR = "#0f172a"
PLOT_BACKGROUND_COLOR = "#3D3D3D"
TEXT_COLOR = "#e2e8f0"
BORDER_COLOR = "#475569"
DAMAGE_COLOR = "#d67886"
KILLS_COLOR = "#497AB6"


class Histogram(NamedTuple):
    damage: np.ndarray
    kills: np.ndarray


def draw_histogram_subfigure(
    histogram: Histogram,
    damage_axis: Axes,
    kills_axis: Axes,
    clash_type: ClashType,
) -> None:
    damage_axis.figure.patch.set_facecolor(BACKGROUND_COLOR)

    damage_axis.clear()
    damage_axis.patch.set_visible(False)
    damage_axis.bar(np.arange(len(histogram.damage)), histogram.damage, width=0.6, align="center", color=DAMAGE_COLOR, label="Damage")
    damage_axis.set_xticks(np.arange(len(histogram.damage)))
    damage_axis.set_xlim(-0.5, len(histogram.damage) - 0.5)
    damage_axis.xaxis.set_tick_params(colors=DAMAGE_COLOR)
    damage_axis.yaxis.set_tick_params(colors=TEXT_COLOR)
    damage_axis.set_xlabel("Damage", color=DAMAGE_COLOR)
    damage_axis.set_ylabel("Probability (%)", color=TEXT_COLOR)
    damage_axis.set_ylim(0, 100)

    if len(histogram.damage) == 1:
        damage_axis.set_xticks([0])
    else:
        damage_axis.xaxis.set_major_locator(ticker.MaxNLocator(integer=True, steps=[1, 2, 5, 10]))

    kills_axis.clear()
    kills_axis.set_facecolor(PLOT_BACKGROUND_COLOR)
    kills_axis.patch.set_visible(True)
    kills_axis.bar(np.arange(len(histogram.kills)), histogram.kills, width=1.0, color=KILLS_COLOR, label="Kills")
    kills_axis.set_xlim(-0.5, len(histogram.kills) - 0.5)
    kills_axis.xaxis.set_tick_params(colors=KILLS_COLOR)
    kills_axis.xaxis.set_label_position("top")
    kills_axis.set_xlabel(f"{clash_type.value} Kills", color=KILLS_COLOR)

    for axis in (damage_axis, kills_axis):
        for spine in axis.spines.values():
            spine.set_color(BORDER_COLOR)

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
        kills_samples = []
        batches = select_weapons(attacker, defender, clash_type)

        for _ in range(roll_count):
            context.reset_hook_state()
            total_damage = 0
            for batch in batches:
                kills_before = defender.num_killed(total_damage)
                total_damage += roll_damage(attacker, batch, defender, context)

                has_concentrated_fire = batch.weapon.tags.concentrated_fire() > 0
                if has_concentrated_fire:
                    max_kills = min(defender.models, kills_before + batch.weapon.tags.concentrated_fire())
                    max_damage = (defender.shield or 0) + max_kills * defender.hit_points
                    total_damage = min(total_damage, max_damage)

            damage_samples.append(total_damage)
            kills_samples.append(defender.num_killed(total_damage))

        damage_count = np.bincount(np.clip(damage_samples, 0, damage_limit), minlength=damage_limit + 1)
        kills_count = np.bincount(kills_samples, minlength=defender.models + 1)

        histograms[clash_type] = Histogram(
            damage=damage_count / damage_count.sum() * 100,
            kills=kills_count / kills_count.sum() * 100,
        )

    return histograms
