#!/usr/bin/env python3
import argparse
import csv
import sys
import logging

from pathlib import Path
from vfj import Font

logging.basicConfig(format="%(levelname)s: %(message)s")
log = logging.getLogger()


def process(font, positions):
    offsets = {}
    for name in positions:
        gname, x, y = positions[name]
        glyph = font[gname]
        if glyph is None:
            log.warning(f"Glyph '{gname}' is missing from font")
            continue

        for layer in glyph.layers:
            if layer.name not in offsets:
                offsets[layer.name] = {}
            assert name[1:] not in offsets[layer.name]
            for anchor in layer.anchors:
                if anchor.name == name:
                    xoff, yoff = x - anchor.x, y - anchor.y
                    offsets[layer.name][name[1:]] = (xoff, yoff)
            if name[1:] not in offsets[layer.name]:
                log.warning(f"Glyph '{gname}' does not have anchor named '{name}'")

    for glyph in font:
        for layer in glyph.layers:
            for anchor in layer.anchors:
                name = anchor.name
                if name.startswith("_"):
                    name = name[1:]

                if name not in offsets[layer.name]:
                    continue

                xoff, yoff = offsets[layer.name][name]
                anchor.x += xoff
                anchor.y += yoff


def main(args=None):
    parser = argparse.ArgumentParser(
        description="Move anchor to new positions in FontLab VFJ files."
    )
    parser.add_argument("input", type=Path, help="input VFJ file")
    parser.add_argument("output", type=Path, help="output VFJ file")
    parser.add_argument(
        "-p",
        "--positions",
        type=Path,
        required=True,
        help="CSV file with new anchor positions",
    )

    options = parser.parse_args(args)

    font = Font(options.input)

    positions = {}
    with open(options.positions) as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) != 4:
                log.error("Invalid CSV data, there must exactly 4 columns.")
                return 1

            if row[0] in positions:
                log.warning(
                    f"Anchor '{row[0]}' is already set for another glyph, ignoring."
                )
                continue

            positions[row[0]] = (row[1], int(row[2]), int(row[3]))

    process(font, positions)

    font.save(options.output)


if __name__ == "__main__":
    sys.exit(main())
