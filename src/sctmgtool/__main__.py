# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Łukasz Gieryk

import logging
from multiprocessing import freeze_support
from sctmgtool.tools import process_unit_list
from sctmgtool.tk import tkinter_main
from sctmgtool.units import ALL_UNITS


if __name__ == "__main__":
    freeze_support()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    process_unit_list(ALL_UNITS)
    tkinter_main(ALL_UNITS)
