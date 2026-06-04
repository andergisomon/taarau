#!/usr/bin/env python3
"""
Generate precomposed composite glyphs for Taarau / Pimato Tokou.

Produces 4,408 ligature glyphs:
  -   152 open syllable / independent vowel + i_sait/u_sait
  - 1,064 plain CVC/VC     (base + coda)
  - 1,064 CVC/VC + i_sait  (base + coda + diphthong /i/)
  - 1,064 CVC/VC + u_sait  (base + coda + diphthong /u/)
  - 1,064 CVC/VC + pangnau (base + coda + vowel lengthening)

Anchor-based auto-positioning:
  - coda marks: aligned via "saau" anchor (fully automatic)
  - pangnau:    aligned via "pangnau" anchor (fully automatic)
  - i_sait:     approximated using base "i_sait" / mark "i_sait_lig" anchors
  - u_sait:     approximated using base "u_sait" / mark "u_sait_lig" anchors

Usage:
    fontforge -script scripts/generate_composites.py
    fontforge -script scripts/generate_composites.py --overwrite
"""

import fontforge
import psMat
import math
import os
import sys

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

INDEPENDENT_VOWELS = ["a_bas", "i_bas", "u_bas", "o_bas"]

EXTRA_MARKS = ["i_sait", "u_sait", "pangnau"]
OPEN_SAIT_MARKS = ["i_sait", "u_sait"]
OPEN_SAIT_BASES = OPEN_SYLLABLES + INDEPENDENT_VOWELS
CODA_BASES = OPEN_SYLLABLES + INDEPENDENT_VOWELS

LOOKUP_NAME = "composite-liga"
SUBTABLE_NAME = "composite-liga-1"


# Maps each mark glyph to the anchor classes used to position it:
# (base_anchor_class, mark_anchor_class[, mark_anchor_type]).
# The mark anchor type defaults to "mark"; i_sait_lig is currently stored as
# a base anchor in the source SFD, so it is called out explicitly.
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
    # diphthong glides: cross-class approximation
    "i_sait":     ("i_sait",  "i_sait_lig", "base"),
    "u_sait":     ("u_sait",  "u_sait_lig"),
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
    are missing.
    """
    pair = MARK_ANCHORS.get(mark_name)
    if pair is None:
        return psMat.identity()

    base_class, mark_class = pair[:2]
    mark_type = pair[2] if len(pair) > 2 else "mark"
    base_pos = get_anchor(font[base_name], base_class, "base")
    mark_pos = get_anchor(font[mark_name], mark_class, mark_type)

    if base_pos is None or mark_pos is None:
        return psMat.identity()

    return psMat.translate(base_pos[0] - mark_pos[0], base_pos[1] - mark_pos[1])


def translation_offset(transform):
    """Return the x/y offset from the translation-only transforms used here."""
    return (transform[4], transform[5])


def translated_bbox(font, glyph_name, transform):
    xmin, ymin, xmax, ymax = font[glyph_name].boundingBox()
    dx, dy = translation_offset(transform)
    return (xmin + dx, ymin + dy, xmax + dx, ymax + dy)


def compute_width(font, syllable, components):
    """
    Set the advance wide enough for all positioned components while preserving
    the base syllable's right side bearing as spacing after the rightmost mark.
    """
    base_width = font[syllable].width
    base_bbox = font[syllable].boundingBox()
    base_rsb = max(0, base_width - base_bbox[2])
    max_x = max(translated_bbox(font, name, transform)[2] for name, transform in components)

    return int(math.ceil(max(base_width, max_x + base_rsb)))


def glyph_name(components):
    return ".".join(components)


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


def parse_args(argv):
    overwrite = False
    for arg in argv[1:]:
        if arg == "--skip-existing":
            overwrite = False
        elif arg == "--overwrite":
            overwrite = True
        else:
            raise SystemExit(f"Unknown argument: {arg}")
    return overwrite


def reset_glyph(glyph):
    """Remove previous generated outlines/references/lookups before rebuilding."""
    try:
        glyph.removePosSub(SUBTABLE_NAME)
    except:
        pass
    glyph.clear()


def create_composite(font, components, overwrite=True):
    name = glyph_name(components)
    existed = name in font
    if existed:
        if not overwrite:
            return "skipped"
        g = font[name]
        reset_glyph(g)
    else:
        g = font.createChar(-1, name)
    base_name = components[0]
    placed_components = [
        (base_name, psMat.identity()),
    ]
    for mark_name in components[1:]:
        placed_components.append((mark_name, mark_transform(font, base_name, mark_name)))

    g.width = compute_width(font, base_name, placed_components)
    for component_name, transform in placed_components:
        g.addReference(component_name, transform)

    g.addPosSub(SUBTABLE_NAME, tuple(components))

    return "updated" if existed else "created"


def count_result(result, counts):
    if result == "created":
        counts["created"] += 1
    elif result == "updated":
        counts["updated"] += 1
    else:
        counts["skipped"] += 1


def verify_inputs(font):
    missing = []
    for name in OPEN_SAIT_BASES + CODA_MARKS + EXTRA_MARKS:
        if name not in font:
            missing.append(name)
    if missing:
        print(f"WARNING: missing glyphs in font: {missing}")
    return missing


def main():
    overwrite = parse_args(sys.argv)
    print(f"Opening {SFD_PATH}")
    font = fontforge.open(SFD_PATH)

    missing = verify_inputs(font)
    if missing:
        print("Proceeding, but composites referencing missing glyphs will be skipped.")

    ensure_lookup(font)

    counts = {"created": 0, "updated": 0, "skipped": 0}

    for base in OPEN_SAIT_BASES:
        if base not in font:
            continue
        for extra in OPEN_SAIT_MARKS:
            if extra not in font:
                continue
            result = create_composite(font, [base, extra], overwrite=overwrite)
            count_result(result, counts)

    for base in CODA_BASES:
        if base not in font:
            continue
        for coda in CODA_MARKS:
            if coda not in font:
                continue
            # plain CVC/VC
            result = create_composite(font, [base, coda], overwrite=overwrite)
            count_result(result, counts)
            # CVC/VC + extra mark
            for extra in EXTRA_MARKS:
                if extra not in font:
                    continue
                result = create_composite(font, [base, coda, extra], overwrite=overwrite)
                count_result(result, counts)

    print(
        f"Done: {counts['created']} glyphs created, "
        f"{counts['updated']} regenerated, {counts['skipped']} already existed."
    )
    font.save(SFD_PATH)
    move_lookup_last(SFD_PATH)
    print(f"Saved to {SFD_PATH}")


if __name__ == "__main__":
    main()
