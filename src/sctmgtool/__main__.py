# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Łukasz Gieryk

import logging
import ctypes
import os
from multiprocessing import freeze_support
from sctmgtool.tools import process_unit_list
from sctmgtool.tk import tkinter_main
from sctmgtool.units import ALL_UNITS


if __name__ == "__main__":
    if os.name == "nt":
        # Workaround for high resolution displays on Windows with the scaling
        # enabled. Matplotlib renders with too small font for the figures to be
        # readable otherwise.
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # 2 = per-monitor DPI awareness

    freeze_support()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    process_unit_list(ALL_UNITS)
    tkinter_main(ALL_UNITS)
