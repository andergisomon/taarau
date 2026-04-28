#!/usr/bin/env python3
"""
Correct contour direction for all glyphs in Taarau.sfd.

FontForge's correctDirection() enforces the PostScript convention:
outer contours counter-clockwise, inner contours (counters/holes) clockwise.
Mixed directions cause incorrect fills (white overlaps) in renderers.

Usage:
    fontforge -script scripts/fix_direction.py
"""

import fontforge
import os

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SFD_PATH = os.path.join(REPO_ROOT, "src", "Taarau.sfd")


def main():
    print(f"Opening {SFD_PATH}")
    font = fontforge.open(SFD_PATH)

    fixed = 0
    for glyph in font.glyphs():
        if glyph.isWorthOutputting():
            glyph.correctDirection()
            fixed += 1

    print(f"Corrected direction for {fixed} glyphs.")
    font.save(SFD_PATH)
    print(f"Saved to {SFD_PATH}")


if __name__ == "__main__":
    main()
