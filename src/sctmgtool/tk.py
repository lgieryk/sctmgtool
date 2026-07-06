# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Łukasz Gieryk

from dataclasses import dataclass, field, fields, is_dataclass
from enum import Enum
import tkinter as tk
from collections import defaultdict
import json
import hashlib
from typing import NamedTuple
from itertools import product
from pathlib import Path
from functools import partial
import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from matplotlib import ticker
import numpy as np
from platformdirs import user_data_dir
import sctmgtool
from sctmgtool.tools import Unit, MusteredUnit, Upgrade, ClashType, HookContext
from sctmgtool.tools import roll_damage, select_weapons
from sctmgtool.cache import Cache

ROLL_COUNT = 10000
THREADS = 4


def get_config_path():
    return Path(user_data_dir("sctmgtool"), "save.json")


def load_config():
    config = defaultdict(lambda: defaultdict(lambda: False))
    file_path = get_config_path()

    try:
        with open(file_path, "r", encoding="utf8") as f:
            data = json.load(f)
            if data["_version"] != sctmgtool.__version__:
                return config
            del data["_version"]

            for u, v in data.items():
                config[u].update(v)

    except FileNotFoundError:
        pass

    return config


def save_config(config):
    file_path = get_config_path()
    file_path.parent.mkdir(parents=True, exist_ok=True)

    config["_version"] = sctmgtool.__version__

    with open(file_path, "w", encoding="utf8") as f:
        json.dump(config, f, indent=4)


class Histogram(NamedTuple):
    damage: list
    kills: list


class RollCache(Cache):
    def __init__(self, units: tuple[Unit], save_path: Path):
        minor_rev = hashlib.sha256(json.dumps(self.normalize(units), sort_keys=True).encode()).hexdigest()
        super().__init__(minor_rev, save_path)
        self.units = units

        # for i in range(THREADS):
        #     if RollCache._completed_key(i) in self.data:
        #         continue

        #     self.start_worker_func(self.worker_func, arguments=(i, ))

    @staticmethod
    def _completed_key(thread_id: int):
        return f"_thread{thread_id}_done"

    @staticmethod
    def normalize(obj):
        if is_dataclass(obj):
            return {f.name: RollCache.normalize(getattr(obj, f.name)) for f in fields(obj)}
        elif isinstance(obj, Enum):
            return obj.value
        elif isinstance(obj, (list, tuple)):
            return [RollCache.normalize(x) for x in obj]
        elif isinstance(obj, Upgrade):
            return (obj.name, RollCache.normalize(obj.upgrade_type), obj.message, RollCache.normalize(obj.cost))
        return obj

    def worker_func(self, thread_id: int):
        def upgrades(unit: Unit, ut: Upgrade.Type):
            return [u for u in unit.upgrades if u.upgrade_type == ut]

        def make_configs(unit, ut):
            upg = upgrades(unit, ut)
            sizes = [squad.models.stop for squad in unit.squad]
            size_key = "_squad_size" if ut == Upgrade.Type.Offensive else "_squad_size_def"

            for size in sizes:
                for flags in product([False, True], repeat=len(upg)):
                    yield {size_key: size, **{upgrade.name: enabled for upgrade, enabled in zip(upg, flags)}}

        for a, d in product(self.units, self.units):
            for i, (ac, dc) in enumerate(product(make_configs(a, Upgrade.Type.Offensive), make_configs(d, Upgrade.Type.Defensive))):
                if self.stop_event.is_set():
                    return

                if i % THREADS != thread_id:
                    continue

                ma = MusteredUnit.make(a, ac, True)
                md = MusteredUnit.make(d, dc, False)
                _ = self[(ma, md)]

        with self.lock:
            self.data.setdefault(RollCache._completed_key(thread_id), True)

        with self.new_inserts.get_lock():
            self.new_inserts.value += 1

    def compute_func(self, obj):
        attacker, defender = obj
        entry = []

        kills_limit = defender.models
        damage_limit = defender.models * defender.hit_points
        if defender.shield is not None:
            damage_limit += defender.shield

        for ct in ClashType:
            ctx = HookContext((attacker, defender))
            active_batches = select_weapons(attacker, defender, ct)

            damage = [sum(roll_damage(attacker, batch, defender, ctx) for batch in active_batches) for _ in range(ROLL_COUNT)]
            damage_count = np.bincount(np.clip(damage, 0, damage_limit), minlength=damage_limit)
            damage_percent = damage_count / damage_count.sum() * 100

            kills = [defender.num_killed(dmg) for dmg in damage]
            kills_count = np.bincount(kills, minlength=kills_limit)
            kills_percent = kills_count / kills_count.sum() * 100

            entry.append(Histogram(damage_percent, kills_percent))

        return entry

    def obj_to_key(self, obj):
        return (obj[0].fingerprint, obj[1].fingerprint)


def tkinter_main(units: list[Unit]):
    # This code is awful. Shame on me.

    class _IntVar(tk.IntVar):
        def __init__(self, *args, extra=None, **kwargs):
            super().__init__(*args, **kwargs)
            self.extra = extra

    @dataclass
    class _Fig:
        ax1: Axes
        ax2: Axes

    @dataclass
    class _UnitData:
        prototype: Unit = None
        unit_label: ctk.CTkLabel = None
        unit_size: tk.IntVar = None
        radios: list[ctk.CTkRadioButton] = field(default_factory=list)
        upgrade_vars: list[ctk.CTkLabel] = field(default_factory=list)
        weapon_labels: list[ctk.CTkLabel] = field(default_factory=list)

    name_to_unit = {u.name: u for u in units}
    assert len(name_to_unit) == len(units)

    weapon_labels = {}
    subfigures = []
    attacker = _UnitData()
    defender = _UnitData()
    config = load_config()
    roll_cache = RollCache(units, get_config_path().parent)

    root = ctk.CTk()
    root.geometry("1200x800")
    root.title("SC:TMG Tool")

    mono_font = ctk.CTkFont(family="Consolas")

    def refresh_graphs():
        if not attacker.prototype:
            return

        mustered_atk = MusteredUnit.make(attacker.prototype, config[attacker.prototype.name], True)
        attacker.unit_label.configure(text=str(mustered_atk))

        for weapon in mustered_atk.weapons:
            batch = mustered_atk.batch(weapon.name)
            label = weapon_labels[weapon.name]

            if batch is None:
                label.configure(text=f"{0:2}x {weapon}", text_color=["#A0A0A0", "#505050"])
            else:
                label.configure(text=f"{batch.model_num:2}x {weapon}", text_color=["black", "white"])

        if not defender.prototype:
            return

        mustered_def = MusteredUnit.make(defender.prototype, config[defender.prototype.name], False)
        defender.unit_label.configure(text=str(mustered_def))

        hist_data = roll_cache[(mustered_atk, mustered_def)]

        for data, fig, ct in zip(hist_data, subfigures, ClashType):
            draw_histogram(data, fig, ct)

        figure.tight_layout()
        canvas.draw_idle()

    def draw_histogram(data: Histogram, fig: _Fig, clash_type: ClashType):
        fig.ax1.clear()
        fig.ax1.bar(np.arange(len(data.damage)), data.damage, width=1.0, alpha=0.6, color="blue", label="Damage")
        fig.ax1.set_xticks(np.arange(len(data.damage)))
        fig.ax1.xaxis.set_tick_params(colors="blue")
        fig.ax1.set_xlabel("Damage", color="blue")
        fig.ax1.set_ylabel("Probability (%)")
        fig.ax1.set_ylim(0, 100)

        if len(data.damage) == 1:
            fig.ax1.set_xticks([0])
        else:
            fig.ax1.xaxis.set_major_locator(ticker.MaxNLocator(integer=True, steps=[1, 2, 5, 10]))

        fig.ax2.clear()
        fig.ax2.bar(np.arange(len(data.kills)), data.kills, width=1.0, alpha=0.6, color="red", label="Kills")
        fig.ax2.xaxis.set_tick_params(colors="red")
        fig.ax2.xaxis.set_label_position("top")
        fig.ax2.set_xlabel(f"{clash_type.value} Kills", color="red")

        if len(data.kills) == 1:
            fig.ax2.set_xticks([0])
        else:
            fig.ax2.xaxis.set_major_locator(ticker.MaxNLocator(integer=True, steps=[1, 2, 5, 10]))

    def build_subfigure(parent: Figure, index: int):
        ax1 = parent.add_subplot(1, 3, index + 1)
        ax2 = ax1.twiny()
        return _Fig(ax1, ax2)

    def on_close():
        save_config(config)
        roll_cache.stop_and_save()
        root.destroy()

    def on_upgrade_toggled(ud: _UnitData, upgrade_name: str, var: ctk.BooleanVar):
        config[ud.prototype.name][upgrade_name] = var.get()
        refresh_graphs()

    def update_size_radios(data: _UnitData, config_key: str):
        for i, radio in enumerate(data.radios):
            if i < len(data.prototype.squad):
                value = data.prototype.squad[i].models.stop
                radio.configure(value=value, text=str(value), state=ctk.NORMAL)
            else:
                radio.configure(value=0, text="-", state=ctk.DISABLED)

        active_size = config[data.prototype.name].setdefault(config_key, data.prototype.squad[0].models.stop)
        data.unit_size.set(active_size)

    def refresh_atk(u_frame, w_frame, unit_name: str, *, refresh=True):
        for frame in (u_frame, w_frame):
            for widget in frame.winfo_children():
                widget.destroy()

        attacker.prototype = name_to_unit[unit_name]
        attacker.upgrade_vars.clear()
        weapon_labels.clear()

        for upgrade in attacker.prototype.upgrades:
            if Upgrade.Type.Offensive in upgrade.upgrade_type:
                var = ctk.BooleanVar(value=config[attacker.prototype.name][upgrade.name])
                attacker.upgrade_vars.append(var)
                cb = ctk.CTkCheckBox(u_frame, text=str(upgrade), variable=var, command=partial(on_upgrade_toggled, attacker, upgrade.name, var))
                cb.pack(anchor="w")
            if Upgrade.Type.Other in upgrade.upgrade_type:
                ctk.CTkLabel(u_frame, text=f"(other) {upgrade.name}").pack(anchor="w")

        if len(attacker.upgrade_vars) == 0:
            ctk.CTkLabel(u_frame, text="(no offensive upgrades)", padx=10).pack(anchor="w")

        for weapon in attacker.prototype.weapons:
            label = ctk.CTkLabel(w_frame, text="?", font=mono_font)
            label.pack(anchor="w")
            weapon_labels[weapon.name] = label

        update_size_radios(attacker, "_squad_size")

        if refresh:
            refresh_graphs()

    def refresh_def(u_frame, unit_name, *, refresh=True):
        for widget in u_frame.winfo_children():
            widget.destroy()

        defender.prototype = name_to_unit[unit_name]
        defender.upgrade_vars.clear()

        for upgrade in defender.prototype.upgrades:
            if Upgrade.Type.Defensive in upgrade.upgrade_type:
                var = ctk.BooleanVar(value=config[defender.prototype.name][upgrade.name])
                defender.upgrade_vars.append(var)
                cb = ctk.CTkCheckBox(u_frame, text=str(upgrade), variable=var, command=partial(on_upgrade_toggled, defender, upgrade.name, var))
                cb.pack(anchor="w")

        if len(defender.upgrade_vars) == 0:
            ctk.CTkLabel(u_frame, text="(no defensive upgrades)", padx=10).pack(anchor="w")

        update_size_radios(defender, "_squad_size_def")

        if refresh:
            refresh_graphs()

    def swap_units():
        to_swap = cba.get()
        cba.set(cbd.get())
        cbd.set(to_swap)
        refresh_atk(auf, awf, cba.get(), refresh=False)
        refresh_def(duf, cbd.get(), refresh=True)

    def select_units():
        cba.set(units[0].name)
        cbd.set(units[1].name)
        refresh_atk(auf, awf, cba.get(), refresh=False)
        refresh_def(duf, cbd.get(), refresh=True)

    sel = ctk.CTkFrame(root)
    sel.columnconfigure(0, weight=1)
    sel.columnconfigure(1, weight=0)
    sel.columnconfigure(2, weight=1)
    sel.pack(fill="x")

    cba = ctk.CTkOptionMenu(sel, values=[u.name for u in units], height=40, command=lambda value: refresh_atk(auf, awf, value))
    cba.grid(row=0, column=0, sticky="ew", padx=5)

    vs = ctk.CTkButton(sel, text="vs", command=swap_units)
    vs.grid(row=0, column=1)

    cbd = ctk.CTkOptionMenu(sel, values=[u.name for u in units], height=40, command=lambda value: refresh_def(duf, value))
    cbd.grid(row=0, column=2, sticky="ew", padx=5)

    af = ctk.CTkFrame(root)
    af.pack(padx=10, pady=2, fill="x")

    attacker.unit_size = _IntVar(extra="_squad_size")
    for i in range(2):
        radio = ctk.CTkRadioButton(
            af, text=str(i), width=50, variable=attacker.unit_size, command=partial(on_upgrade_toggled, attacker, "_squad_size", attacker.unit_size)
        )
        radio.pack(side=ctk.LEFT)
        attacker.radios.append(radio)
    attacker.unit_label = ctk.CTkLabel(af, font=mono_font, padx=10)
    attacker.unit_label.pack(anchor="w")

    awf = ctk.CTkFrame(root)
    awf.pack(padx=10, pady=2, fill="x")

    auf = ctk.CTkFrame(root)
    auf.pack(padx=10, pady=2, fill="x")

    df = ctk.CTkFrame(root)
    df.pack(padx=10, pady=2, fill="x")

    defender.unit_size = _IntVar(extra="_squad_size_def")
    for i in range(2):
        radio = ctk.CTkRadioButton(
            df, text=str(i), width=50, variable=defender.unit_size, command=partial(on_upgrade_toggled, defender, "_squad_size_def", defender.unit_size)
        )
        radio.pack(side=ctk.LEFT)
        defender.radios.append(radio)
    defender.unit_label = ctk.CTkLabel(df, font=mono_font, padx=10)
    defender.unit_label.pack(anchor="w")

    duf = ctk.CTkFrame(root)
    duf.pack(padx=10, pady=2, fill="x")

    plots = ctk.CTkFrame(root)
    figure = Figure(figsize=(15, 3), dpi=100)
    canvas = FigureCanvasTkAgg(figure, master=plots)
    canvas.get_tk_widget().pack(fill="x")
    plots.pack(fill="x")

    for i in range(len(ClashType)):
        subfigures.append(build_subfigure(figure, i))

    select_units()
    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()
