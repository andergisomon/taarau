open syllable glyphs (ligatures):

ka ki ku ko
ga gi gu go
ba bi bu bo
da di du do
ta ti tu to
pa pi pu po
ha hi hu ho
ra ri ru ro
sa si su so
ya yi yu yo
wa wi wu wo
ma mi mu mo
na ni nu no
nga ngi ngu ngo
la li lu lo
za zi zu zo
va vi vu vo
ja ji ju jo

14 codas:
	
kaak_saau (-k)
gaag_saau (-g)
baab_saau (-b)
daad_saau (-d)
taat_saau (-t)
paap_saau (-p)
haah_saau (-h)
raar_saau (-r)
saas_saau (-s)
maam_saau (-m)
naan_saau (-n)
ngaang_saau (-ng)
laal_saau (-l)
sigot (glottal stop)

these are marks attached to the open syllable glyphs to form closed syllable glyphs with the respective coda consonants

diphthong marks:
	
i_sait (V + /i/)
u_sait (V + /u/)

for CVC_glide where C_glide is either /j/ or /w/ don't count as regular codas. they're diphthongs and respectively use different marks that are attached on the top left or bottom left of an open/closed syllable glyph.

i.e., C_onset V (vowel lengthening) C_glide C_coda is the most complex single composite glyph possible (e.g. naauk "drunk", kaai' "to be able to finish", naait "to be already said", nooug "to be already washed (hands)", nooit "to be already brought with" etc.)

vowel lengthening mark:

pangnau

## technical problem

how do we most reliably ensure that all of these components don't collide and have fixed and proper positions relative to each other?

the best solution to this is to precompose glyphs by combining the open syllable glyphs with all of the marks:
	
(Total no. of open syllable glyphs = 72) x (14 coda marks) x (2 diphtong marks + 1 vowel lengthening mark) = 3024 composite glyphs requiring manual positioning

the 72*14 =1,008 combos of simple CVC syllables don't need dedicated composite glyphs. just dynamic mark to base is enough (for now, because libreoffice justification has problems with it, which would be solved via the dedicated composite glyph approach, inflating the count by +1008=4032 composite glyphs).

doing this manually via the fontforge gui is tedious. the workflow can be sped up by scripting to automatically generate all of these composite glyphs and name them consistently. then whats left would be going through all of them for manual inspection and adjustment, which is still only a few clicks per glyph.

even though we're calling them composite glyphs, they're actually just basic opentype ligatures. guaranteed to work almost everywhere. same cannot be said for stuff like contextual chaining position.



Run the script from the repo root with:

/Applications/FontForge.app/Contents/Resources/opt/local/bin/fontforge -script scripts/generate_composites.py

/Applications/FontForge.app/Contents/Resources/opt/local/bin/fontforge -script scripts/fix_direction.py