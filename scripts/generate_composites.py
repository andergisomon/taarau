#!/usr/bin/env python3
"""
Generate precomposed composite glyphs for Taarau / Pimato Tokou.

Produces 4,032 ligature glyphs:
  - 1,008 plain CVC        (syllable + coda)
  - 1,008 CVC + i_sait     (syllable + coda + diphthong /i/)
  - 1,008 CVC + u_sait     (syllable + coda + diphthong /u/)
  - 1,008 CVC + pangnau    (syllable + coda + vowel lengthening)

All component references are placed at the origin; manual positioning in
the FontForge GUI is still required per glyph.

Usage:
    fontforge -script scripts/generate_composites.py
"""

import fontforge
import psMat
import os

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SFD_PATH = os.path.join(REPO_ROOT, "src", "Taarau.sfd")

OPEN_SYLLABLES = [
    "ka", "ki", "ku", "ko",
    "ga", "gi", "gu", "go",
    "ba", "bi", "bu", "bo",
    "da", "di", "du", "do",
    "ta", "ti", "tu", "to",
    "pa", "pi", "pu", "po",
    "ha", "hi", "hu", "ho",
    "ra", "ri", "ru", "ro",
    "sa", "si", "su", "so",
    "ya", "yi", "yu", "yo",
    "wa", "wi", "wu", "wo",
    "ma", "mi", "mu", "mo",
    "na", "ni", "nu", "no",
    "nga", "ngi", "ngu", "ngo",
    "la", "li", "lu", "lo",
    "za", "zi", "zu", "zo",
    "va", "vi", "vu", "vo",
    "ja", "ji", "ju", "jo",
]

CODA_MARKS = [
    "kaak_saau", "gaag_saau", "baab_saau", "daad_saau", "taat_saau",
    "paap_saau", "haah_saau", "raar_saau", "saas_saau", "maam_saau",
    "naan_saau", "ngaang_saau", "laal_saau", "sigot",
]

EXTRA_MARKS = ["i_sait", "u_sait", "pangnau"]

LOOKUP_NAME = "composite-liga"
SUBTABLE_NAME = "composite-liga-1"


def glyph_name(syllable, coda, extra=None):
    if extra:
        return f"{syllable}.{coda}.{extra}"
    return f"{syllable}.{coda}"


def ensure_lookup(font):
    existing = font.getLookupInfo(LOOKUP_NAME) if LOOKUP_NAME in font.gsub_lookups else None
    if existing is None:
        font.addLookup(
            LOOKUP_NAME,
            "gsub_ligature",
            (),
            (("liga", (("latn", ("dflt",)),)),),
        )
        font.addLookupSubtable(LOOKUP_NAME, SUBTABLE_NAME)


def create_composite(font, syllable, coda, extra=None):
    name = glyph_name(syllable, coda, extra)
    if name in font:
        return False

    g = font.createChar(-1, name)
    g.width = font[syllable].width

    g.addReference(syllable, psMat.identity())
    g.addReference(coda, psMat.identity())
    if extra:
        g.addReference(extra, psMat.identity())

    components = [syllable, coda] + ([extra] if extra else [])
    g.addPosSub(SUBTABLE_NAME, tuple(components))

    return True


def verify_inputs(font):
    missing = []
    for name in OPEN_SYLLABLES + CODA_MARKS + EXTRA_MARKS:
        if name not in font:
            missing.append(name)
    if missing:
        print(f"WARNING: missing glyphs in font: {missing}")
    return missing


def main():
    print(f"Opening {SFD_PATH}")
    font = fontforge.open(SFD_PATH)

    missing = verify_inputs(font)
    if missing:
        print("Proceeding, but composites referencing missing glyphs will be skipped.")

    ensure_lookup(font)

    created = 0
    skipped = 0

    for syllable in OPEN_SYLLABLES:
        if syllable not in font:
            continue
        for coda in CODA_MARKS:
            if coda not in font:
                continue
            # plain CVC
            if create_composite(font, syllable, coda):
                created += 1
            else:
                skipped += 1
            # CVC + extra mark
            for extra in EXTRA_MARKS:
                if extra not in font:
                    continue
                if create_composite(font, syllable, coda, extra):
                    created += 1
                else:
                    skipped += 1

    print(f"Done: {created} glyphs created, {skipped} already existed.")
    font.save(SFD_PATH)
    print(f"Saved to {SFD_PATH}")


if __name__ == "__main__":
    main()
