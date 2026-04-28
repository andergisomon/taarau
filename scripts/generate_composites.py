#!/usr/bin/env python3
"""
Generate precomposed composite glyphs for Taarau / Pimato Tokou.

Produces 4,032 ligature glyphs:
  - 1,008 plain CVC        (syllable + coda)
  - 1,008 CVC + i_sait     (syllable + coda + diphthong /i/)
  - 1,008 CVC + u_sait     (syllable + coda + diphthong /u/)
  - 1,008 CVC + pangnau    (syllable + coda + vowel lengthening)

Anchor-based auto-positioning:
  - coda marks: aligned via "saau" anchor (fully automatic)
  - pangnau:    aligned via "pangnau" anchor (fully automatic)
  - u_sait:     approximated using base "u_sait" / mark "u_sait_lig" anchors
  - i_sait:     placed at origin (no anchor defined; needs manual adjustment)

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


# Maps each mark glyph to the (base_anchor_class, mark_anchor_class) pair used
# to position it. Where the classes differ (u_sait), we cross-match the best
# available anchor. i_sait has no anchor, so it falls back to identity.
MARK_ANCHORS = {
    # coda marks: all use "saau" on both base and mark
    "kaak_saau":  ("saau",    "saau"),
    "gaag_saau":  ("saau",    "saau"),
    "baab_saau":  ("saau",    "saau"),
    "daad_saau":  ("saau",    "saau"),
    "taat_saau":  ("saau",    "saau"),
    "paap_saau":  ("saau",    "saau"),
    "haah_saau":  ("saau",    "saau"),
    "raar_saau":  ("saau",    "saau"),
    "saas_saau":  ("saau",    "saau"),
    "maam_saau":  ("saau_maam", "saau_maam"),
    "naan_saau":  ("saau",    "saau"),
    "ngaang_saau":("saau",    "saau"),
    "laal_saau":  ("saau",    "saau"),
    "sigot":      ("saau_maam", "saau_maam"),
    # vowel lengthening
    "pangnau":    ("pangnau", "pangnau"),
    # diphthong glides — cross-class approximation
    "u_sait":     ("u_sait",  "u_sait_lig"),
    # i_sait has no anchor; caller falls back to identity
}


def get_anchor(glyph, anchor_class, anchor_type):
    """Return (x, y) for the named anchor, or None if absent."""
    for ap in glyph.anchorPoints:
        if ap[0] == anchor_class and ap[1] == anchor_type:
            return (ap[2], ap[3])
    return None


def mark_transform(font, base_name, mark_name):
    """
    Compute the translation that aligns mark_name's attachment anchor to the
    base_name glyph's attachment anchor. Falls back to identity if anchors
    are missing (e.g. i_sait).
    """
    pair = MARK_ANCHORS.get(mark_name)
    if pair is None:
        return psMat.identity()

    base_class, mark_class = pair
    base_pos = get_anchor(font[base_name], base_class, "base")
    mark_pos = get_anchor(font[mark_name], mark_class, "mark")

    if base_pos is None or mark_pos is None:
        return psMat.identity()

    return psMat.translate(base_pos[0] - mark_pos[0], base_pos[1] - mark_pos[1])


def glyph_name(syllable, coda, extra=None):
    if extra:
        return f"{syllable}.{coda}.{extra}"
    return f"{syllable}.{coda}"


def ensure_lookup(font):
    try:
        font.getLookupInfo(LOOKUP_NAME)
    except:
        font.addLookup(
            LOOKUP_NAME,
            "gsub_ligature",
            (),
            (("liga", (("DFLT", ("dflt",)), ("latn", ("dflt",)))),),
        )
        font.addLookupSubtable(LOOKUP_NAME, SUBTABLE_NAME)


def move_lookup_last(sfd_path):
    """Move the composite-liga Lookup line to be last among all GSUB (type 4) lookups."""
    with open(sfd_path, "r") as f:
        lines = f.readlines()

    target = None
    target_idx = None
    for i, line in enumerate(lines):
        if line.startswith("Lookup:") and f'"{LOOKUP_NAME}"' in line:
            target = line
            target_idx = i
            break

    if target is None:
        return

    lines.pop(target_idx)

    # Find the last GSUB ligature lookup (type 4) and insert after it
    last_gsub_idx = None
    for i, line in enumerate(lines):
        if line.startswith("Lookup: 4 "):
            last_gsub_idx = i

    insert_at = (last_gsub_idx + 1) if last_gsub_idx is not None else target_idx
    lines.insert(insert_at, target)

    with open(sfd_path, "w") as f:
        f.writelines(lines)


def create_composite(font, syllable, coda, extra=None):
    name = glyph_name(syllable, coda, extra)
    if name in font:
        return False

    g = font.createChar(-1, name)
    g.width = font[syllable].width

    g.addReference(syllable, psMat.identity())
    g.addReference(coda, mark_transform(font, syllable, coda))
    if extra:
        # For extra marks on a composite, use the syllable's base anchors as
        # the reference point (close enough for initial placement).
        g.addReference(extra, mark_transform(font, syllable, extra))

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
    move_lookup_last(SFD_PATH)
    print(f"Saved to {SFD_PATH}")


if __name__ == "__main__":
    main()
