#!/usr/bin/env python3
"""
Prepare outlines in Taarau.sfd for reliable CFF/OTF rendering.

FontForge's correctDirection() fixes winding on real contours, but it does
not merge overlaps between referenced components. The generated composite
glyphs are reference-only, so renderers can still show white overlap regions
unless those references are decomposed and overlaps are removed before export.

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
    decomposed = 0
    for glyph in font.glyphs():
        if glyph.isWorthOutputting():
            glyph.correctDirection()
            if glyph.references:
                glyph.unlinkRef()
                glyph.removeOverlap()
                decomposed += 1
            glyph.correctDirection()
            fixed += 1

    print(f"Decomposed references and removed overlaps for {decomposed} glyphs.")
    print(f"Corrected direction for {fixed} glyphs.")
    font.save(SFD_PATH)
    print(f"Saved to {SFD_PATH}")


if __name__ == "__main__":
    main()
