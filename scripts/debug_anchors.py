import fontforge, os

f = fontforge.open(os.path.join(os.path.dirname(os.path.dirname(__file__)), "src", "Taarau.sfd"))

ka   = f["ka"]
kaak = f["kaak_saau"]

print("ka anchorPoints:")
for ap in ka.anchorPoints:
    print(" ", ap)

print("kaak_saau anchorPoints:")
for ap in kaak.anchorPoints:
    print(" ", ap)
