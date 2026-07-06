# SC:TMG Tool

A combat analysis tool for StarCraft: Tabletop Miniatures Game. It calculates
the expected outcome of clashes between units to help players with list-building
decisions.

**Disclaimer:** This is an unofficial fan-made project. It is not affiliated
with, sponsored by, or endorsed by the owners of the StarCraft or StarCraft:
Tabletop Miniatures Game trademarks.

Any references to unit names, factions, stats, or other game data are used
solely for identification and analytical purposes under fair use — see
[NOTICE.txt](src/sctmgtool/units/NOTICE.txt) for details.

## A word from the author
Is that UpgradeX, which gives TAG-Y, worth Z minerals? I wanted to know, so I
created SC:TMG Tool - an unofficial, poorly written, and _slow_ application
written in my spare time.

The main idea was to visualize how an upgrade affects the outcome of a clash
between two units. So if an upgrade does not directly translate to a lost (or
saved) hit point, it's not included.

While the rules of SC:TMG are not that complex, they do not translate easily
into a computer program. I applied multiple shortcuts to achieve the
functionality I needed most. And - obviously - I might have gotten a more
complex rule wrong. Typos (and a wrong stat here and there) are also to be
expected.

The tool is slow. It happens so as the result of every clash is simulated 10000
times. The results are saved, though, so returning to an already simulated clash
is slightly faster.

## Installation
### Binary package for Windows
Download a precompiled binary for Windows from here:

### Python package
    git clone https://github.com/lgieryk/sctmgtool.git
    cd sctmgtool
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -e .
    python3 -m sctmgtool

You may need to install some additional system packages:

    apt-get update && apt-get install python3-tk

## License
- Source code: [MIT License](LICENSE)
- Data files in `src/sctmgtool/units/`: distributed under separate terms, see
  [NOTICE.txt](src/sctmgtool/units/NOTICE.txt).
