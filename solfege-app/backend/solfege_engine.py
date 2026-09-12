"""
Solfege conversion engine.
Takes a MusicXML file (produced by OMR) and converts each note's pitch
into movable-do solfege syllables, relative to the prevailing key signature.
"""
from music21 import converter, key, pitch
from fractions import Fraction

# Diatonic scale-degree -> solfege syllable (major keys / natural scale degrees)
DIATONIC_SOLFEGE = ["Do", "Re", "Mi", "Fa", "Sol", "La", "Ti"]

# Chromatic alterations relative to the diatonic degree below/above
# key: (scale_degree_index 0-6, accidental semitone offset) -> syllable
CHROMATIC_SOLFEGE = {
    (0, 1): "Di",   # raised Do
    (1, -1): "Ra",  # lowered Re
    (1, 1): "Ri",   # raised Re
    (2, -1): "Me",  # lowered Mi
    (3, 1): "Fi",   # raised Fa
    (4, -1): "Se",  # lowered Sol
    (4, 1): "Si",   # raised Sol
    (5, -1): "Le",  # lowered La
    (5, 1): "Li",   # raised La
    (6, -1): "Te",  # lowered Ti
}


def _closest_diatonic_index(semitone_offset_from_tonic, major_scale_semitones):
    """Find the closest diatonic scale degree (0-6) to a given semitone
    offset from the tonic, and the remaining chromatic offset."""
    best_idx, best_diff = 0, None
    for idx, deg_semitone in enumerate(major_scale_semitones):
        diff = semitone_offset_from_tonic - deg_semitone
        # consider wrap-around too (offset could be negative)
        for candidate in (diff, diff - 12, diff + 12):
            if best_diff is None or abs(candidate) < abs(best_diff):
                best_diff = candidate
                best_idx = idx
    return best_idx, best_diff


def pitch_to_solfege(p: pitch.Pitch, k: key.Key) -> str:
    """Convert a music21 Pitch to a movable-do solfege syllable given a Key."""
    tonic_pc = k.tonic.pitchClass
    # Determine the major-scale reference (relative major if minor key)
    if k.mode == "minor":
        # La-based minor: relative major is 3 semitones up
        ref_tonic_pc = (tonic_pc + 3) % 12
    else:
        ref_tonic_pc = tonic_pc

    major_scale_semitones = [0, 2, 4, 5, 7, 9, 11]
    offset = (p.pitchClass - ref_tonic_pc) % 12
    idx, chrom_diff = _closest_diatonic_index(offset, major_scale_semitones)

    if chrom_diff == 0:
        syll = DIATONIC_SOLFEGE[idx]
    else:
        syll = CHROMATIC_SOLFEGE.get((idx, int(chrom_diff)))
        if syll is None:
            syll = DIATONIC_SOLFEGE[idx] + ("#" if chrom_diff > 0 else "b")

    # If we used the relative-major trick for a minor key, shift the
    # syllable set so the minor tonic reads as "La" (La-based minor)
    if k.mode == "minor":
        rotate = 5  # major Do(0) -> minor La is degree index 5
        order = DIATONIC_SOLFEGE
        new_idx = (idx - rotate) % 7
        if chrom_diff == 0:
            syll = order[new_idx]
    return syll


def score_to_solfege(musicxml_path: str, part_index: int = 0):
    """
    Parse a MusicXML file and return a list of measures, each containing
    notes with their solfege syllable, octave, and rhythmic duration.
    """
    score = converter.parse(musicxml_path)
    parts = score.parts
    if not parts:
        raise ValueError("No parts found in score")
    part = parts[part_index] if part_index < len(parts) else parts[0]

    # Determine key signature (use the first Key/KeySignature found, else analyze)
    ks = part.flatten().getElementsByClass(key.Key)
    if ks:
        the_key = ks[0]
    else:
        key_sig = part.flatten().getElementsByClass('KeySignature')
        if key_sig:
            the_key = key_sig[0].asKey('major')
        else:
            the_key = part.analyze('key')

    result_measures = []
    for m in part.getElementsByClass('Measure'):
        measure_notes = []
        for el in m.notesAndRests:
            if el.isRest:
                measure_notes.append({"type": "rest", "duration": str(el.quarterLength)})
            elif el.isNote:
                syll = pitch_to_solfege(el.pitch, the_key)
                measure_notes.append({
                    "type": "note",
                    "syllable": syll,
                    "letter": el.pitch.nameWithOctave,
                    "duration": str(el.quarterLength),
                    "lyric": el.lyric or ""
                })
            elif el.isChord:
                # Use the highest note of the chord as the melody note
                top = el.pitches[-1]
                syll = pitch_to_solfege(top, the_key)
                measure_notes.append({
                    "type": "chord",
                    "syllable": syll,
                    "letter": top.nameWithOctave,
                    "duration": str(el.quarterLength),
                    "lyric": el.lyric or ""
                })
        result_measures.append({
            "measure_number": m.number,
            "notes": measure_notes
        })

    return {
        "key": f"{the_key.tonic.name} {the_key.mode}",
        "measures": result_measures
    }
