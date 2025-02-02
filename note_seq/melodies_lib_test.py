# Copyright 2022 The Magenta Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for melodies_lib."""

import os

from absl.testing import absltest
from note_seq import constants
from note_seq import melodies_lib
from note_seq import sequences_lib
from note_seq import testing_lib

NOTE_OFF = constants.MELODY_NOTE_OFF
NO_EVENT = constants.MELODY_NO_EVENT


class MelodiesLibTest(testing_lib.ProtoTestCase):

  def testGetNoteHistogram(self):
    events = [NO_EVENT, NOTE_OFF, 12 * 2 + 1, 12 * 3, 12 * 5 + 11, 12 * 6 + 3,
              12 * 4 + 11]
    melody = melodies_lib.Melody(events)
    expected = [1, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 2]
    self.assertEqual(expected, list(melody.get_note_histogram()))

    events = [0, 1, NO_EVENT, NOTE_OFF, 12 * 2 + 1, 12 * 3, 12 * 6 + 3,
              12 * 5 + 11, NO_EVENT, 12 * 4 + 11, 12 * 7 + 1]
    melody = melodies_lib.Melody(events)
    expected = [2, 3, 0, 1, 0, 0, 0, 0, 0, 0, 0, 2]
    self.assertEqual(expected, list(melody.get_note_histogram()))

    melody = melodies_lib.Melody()
    expected = [0] * 12
    self.assertEqual(expected, list(melody.get_note_histogram()))

  def testGetKeyHistogram(self):
    # One C.
    events = [NO_EVENT, 12 * 5, NOTE_OFF]
    melody = melodies_lib.Melody(events)
    expected = [1, 1, 0, 1, 0, 1, 0, 1, 1, 0, 1, 0]
    self.assertListEqual(expected, list(melody.get_major_key_histogram()))

    # One C and one C#.
    events = [NO_EVENT, 12 * 5, NOTE_OFF, 12 * 7 + 1, NOTE_OFF]
    melody = melodies_lib.Melody(events)
    expected = [1, 2, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1]
    self.assertListEqual(expected, list(melody.get_major_key_histogram()))

    # One C, one C#, and one D.
    events = [NO_EVENT, 12 * 5, NOTE_OFF, 12 * 7 + 1, NO_EVENT, 12 * 9 + 2]
    melody = melodies_lib.Melody(events)
    expected = [2, 2, 2, 2, 1, 2, 1, 2, 2, 2, 2, 1]
    self.assertListEqual(expected, list(melody.get_major_key_histogram()))

  def testGetMajorKey(self):
    # D Major.
    events = [NO_EVENT, 12 * 2 + 2, 12 * 3 + 4, 12 * 5 + 1, 12 * 6 + 6,
              12 * 4 + 11, 12 * 3 + 9, 12 * 5 + 7, NOTE_OFF]
    melody = melodies_lib.Melody(events)
    self.assertEqual(2, melody.get_major_key())

    # C# Major with accidentals.
    events = [NO_EVENT, 12 * 2 + 1, 12 * 4 + 8, 12 * 5 + 5, 12 * 6 + 6,
              12 * 3 + 3, 12 * 2 + 11, 12 * 3 + 10, 12 * 5, 12 * 2 + 8,
              12 * 4 + 1, 12 * 3 + 5, 12 * 5 + 9, 12 * 4 + 3, NOTE_OFF]
    melody = melodies_lib.Melody(events)
    self.assertEqual(1, melody.get_major_key())

    # One note in C Major.
    events = [NO_EVENT, 12 * 2 + 11, NOTE_OFF]
    melody = melodies_lib.Melody(events)
    self.assertEqual(0, melody.get_major_key())

  def testTranspose(self):
    # Melody transposed down 5 half steps. 2 octave range.
    events = [12 * 5 + 4, NO_EVENT, 12 * 5 + 5, NOTE_OFF, 12 * 6, NO_EVENT]
    melody = melodies_lib.Melody(events)
    melody.transpose(transpose_amount=-5, min_note=12 * 5, max_note=12 * 7)
    expected = [12 * 5 + 11, NO_EVENT, 12 * 5, NOTE_OFF, 12 * 5 + 7, NO_EVENT]
    self.assertEqual(expected, list(melody))

    # Melody transposed up 19 half steps. 2 octave range.
    events = [12 * 5 + 4, NO_EVENT, 12 * 5 + 5, NOTE_OFF, 12 * 6, NO_EVENT]
    melody = melodies_lib.Melody(events)
    melody.transpose(transpose_amount=19, min_note=12 * 5, max_note=12 * 7)
    expected = [12 * 6 + 11, NO_EVENT, 12 * 6, NOTE_OFF, 12 * 6 + 7, NO_EVENT]
    self.assertEqual(expected, list(melody))

    # Melody transposed zero half steps. 1 octave range.
    events = [12 * 4 + 11, 12 * 5, 12 * 5 + 11, NOTE_OFF, 12 * 6, NO_EVENT]
    melody = melodies_lib.Melody(events)
    melody.transpose(transpose_amount=0, min_note=12 * 5, max_note=12 * 6)
    expected = [12 * 5 + 11, 12 * 5, 12 * 5 + 11, NOTE_OFF, 12 * 5, NO_EVENT]
    self.assertEqual(expected, list(melody))

  def testSquash(self):
    # Melody in C, transposed to C, and squashed to 1 octave.
    events = [12 * 5, NO_EVENT, 12 * 5 + 2, NOTE_OFF, 12 * 6 + 4, NO_EVENT]
    melody = melodies_lib.Melody(events)
    melody.squash(min_note=12 * 5, max_note=12 * 6, transpose_to_key=0)
    expected = [12 * 5, NO_EVENT, 12 * 5 + 2, NOTE_OFF, 12 * 5 + 4, NO_EVENT]
    self.assertEqual(expected, list(melody))

    # Melody in D, transposed to C, and squashed to 1 octave.
    events = [12 * 5 + 2, 12 * 5 + 4, 12 * 6 + 7, 12 * 6 + 6, 12 * 5 + 1]
    melody = melodies_lib.Melody(events)
    melody.squash(min_note=12 * 5, max_note=12 * 6, transpose_to_key=0)
    expected = [12 * 5, 12 * 5 + 2, 12 * 5 + 5, 12 * 5 + 4, 12 * 5 + 11]
    self.assertEqual(expected, list(melody))

    # Melody in D, transposed to E, and squashed to 1 octave.
    events = [12 * 5 + 2, 12 * 5 + 4, 12 * 6 + 7, 12 * 6 + 6, 12 * 4 + 11]
    melody = melodies_lib.Melody(events)
    melody.squash(min_note=12 * 5, max_note=12 * 6, transpose_to_key=4)
    expected = [12 * 5 + 4, 12 * 5 + 6, 12 * 5 + 9, 12 * 5 + 8, 12 * 5 + 1]
    self.assertEqual(expected, list(melody))

  def testSquashCenterOctaves(self):
    # Move up an octave.
    events = [12 * 4, NO_EVENT, 12 * 4 + 2, NOTE_OFF, 12 * 4 + 4, NO_EVENT,
              12 * 4 + 5, 12 * 5 + 2, 12 * 4 - 1, NOTE_OFF]
    melody = melodies_lib.Melody(events)
    melody.squash(min_note=12 * 4, max_note=12 * 7, transpose_to_key=0)
    expected = [12 * 5, NO_EVENT, 12 * 5 + 2, NOTE_OFF, 12 * 5 + 4, NO_EVENT,
                12 * 5 + 5, 12 * 6 + 2, 12 * 5 - 1, NOTE_OFF]
    self.assertEqual(expected, list(melody))

    # Move down an octave.
    events = [12 * 6, NO_EVENT, 12 * 6 + 2, NOTE_OFF, 12 * 6 + 4, NO_EVENT,
              12 * 6 + 5, 12 * 7 + 2, 12 * 6 - 1, NOTE_OFF]
    melody = melodies_lib.Melody(events)
    melody.squash(min_note=12 * 4, max_note=12 * 7, transpose_to_key=0)
    expected = [12 * 5, NO_EVENT, 12 * 5 + 2, NOTE_OFF, 12 * 5 + 4, NO_EVENT,
                12 * 5 + 5, 12 * 6 + 2, 12 * 5 - 1, NOTE_OFF]
    self.assertEqual(expected, list(melody))

  def testSquashMaxNote(self):
    events = [12 * 5, 12 * 5 + 2, 12 * 5 + 4, 12 * 5 + 5, 12 * 5 + 11, 12 * 6,
              12 * 6 + 1]
    melody = melodies_lib.Melody(events)
    melody.squash(min_note=12 * 5, max_note=12 * 6, transpose_to_key=0)
    expected = [12 * 5, 12 * 5 + 2, 12 * 5 + 4, 12 * 5 + 5, 12 * 5 + 11, 12 * 5,
                12 * 5 + 1]
    self.assertEqual(expected, list(melody))

  def testSquashAllNotesOff(self):
    events = [NO_EVENT, NO_EVENT, NO_EVENT, NO_EVENT]
    melody = melodies_lib.Melody(events)
    melody.squash(min_note=12 * 4, max_note=12 * 7, transpose_to_key=0)
    self.assertEqual(events, list(melody))

  def testFromQuantizedNoteSequence(self):
    testing_lib.add_track_to_sequence(
        self.note_sequence, 0,
        [(12, 100, 0.01, 10.0), (11, 55, 0.22, 0.50), (40, 45, 2.50, 3.50),
         (55, 120, 4.0, 4.01), (52, 99, 4.75, 5.0)])
    quantized_sequence = sequences_lib.quantize_note_sequence(
        self.note_sequence, self.steps_per_quarter)
    melody = melodies_lib.Melody()
    melody.from_quantized_sequence(quantized_sequence,
                                   search_start_step=0, instrument=0)
    expected = ([12, 11, NOTE_OFF, NO_EVENT, NO_EVENT, NO_EVENT, NO_EVENT,
                 NO_EVENT, NO_EVENT, NO_EVENT, 40, NO_EVENT, NO_EVENT, NO_EVENT,
                 NOTE_OFF, NO_EVENT, 55, NOTE_OFF, NO_EVENT, 52])
    self.assertEqual(expected, list(melody))
    self.assertEqual(16, melody.steps_per_bar)

  def testFromQuantizedNoteSequenceNotCommonTimeSig(self):
    self.note_sequence.time_signatures[0].numerator = 7
    self.note_sequence.time_signatures[0].denominator = 8

    testing_lib.add_track_to_sequence(
        self.note_sequence, 0,
        [(12, 100, 0.01, 10.0), (11, 55, 0.22, 0.50), (40, 45, 2.50, 3.50),
         (55, 120, 4.0, 4.01), (52, 99, 4.75, 5.0)])

    quantized_sequence = sequences_lib.quantize_note_sequence(
        self.note_sequence, self.steps_per_quarter)

    melody = melodies_lib.Melody()
    melody.from_quantized_sequence(quantized_sequence,
                                   search_start_step=0, instrument=0)
    expected = ([12, 11, NOTE_OFF, NO_EVENT, NO_EVENT, NO_EVENT, NO_EVENT,
                 NO_EVENT, NO_EVENT, NO_EVENT, 40, NO_EVENT, NO_EVENT, NO_EVENT,
                 NOTE_OFF, NO_EVENT, 55, NOTE_OFF, NO_EVENT, 52])
    self.assertEqual(expected, list(melody))
    self.assertEqual(14, melody.steps_per_bar)

  def testFromNotesPolyphonic(self):
    testing_lib.add_track_to_sequence(
        self.note_sequence, 0,
        [(12, 100, 0.0, 10.0), (11, 55, 0.0, 0.50)])
    quantized_sequence = sequences_lib.quantize_note_sequence(
        self.note_sequence, self.steps_per_quarter)

    melody = melodies_lib.Melody()
    with self.assertRaises(melodies_lib.PolyphonicMelodyError):
      melody.from_quantized_sequence(quantized_sequence,
                                     search_start_step=0, instrument=0,
                                     ignore_polyphonic_notes=False)
    self.assertFalse(list(melody))

  def testFromNotesPolyphonicWithIgnorePolyphonicNotes(self):
    testing_lib.add_track_to_sequence(
        self.note_sequence, 0,
        [(12, 100, 0.0, 2.0), (19, 100, 0.0, 3.0),
         (12, 100, 1.0, 3.0), (19, 100, 1.0, 4.0)])
    quantized_sequence = sequences_lib.quantize_note_sequence(
        self.note_sequence, self.steps_per_quarter)

    melody = melodies_lib.Melody()
    melody.from_quantized_sequence(quantized_sequence,
                                   search_start_step=0, instrument=0,
                                   ignore_polyphonic_notes=True)
    expected = ([19] + [NO_EVENT] * 3 + [19] + [NO_EVENT] * 11)

    self.assertEqual(expected, list(melody))
    self.assertEqual(16, melody.steps_per_bar)

  def testFromNotesChord(self):
    testing_lib.add_track_to_sequence(
        self.note_sequence, 0,
        [(12, 100, 1, 1.25), (19, 100, 1, 1.25),
         (20, 100, 1, 1.25), (25, 100, 1, 1.25)])
    quantized_sequence = sequences_lib.quantize_note_sequence(
        self.note_sequence, self.steps_per_quarter)

    melody = melodies_lib.Melody()
    with self.assertRaises(melodies_lib.PolyphonicMelodyError):
      melody.from_quantized_sequence(quantized_sequence,
                                     search_start_step=0, instrument=0,
                                     ignore_polyphonic_notes=False)
    self.assertFalse(list(melody))

  def testFromNotesTrimEmptyMeasures(self):
    testing_lib.add_track_to_sequence(
        self.note_sequence, 0,
        [(12, 100, 1.5, 1.75), (11, 100, 2, 2.25)])
    quantized_sequence = sequences_lib.quantize_note_sequence(
        self.note_sequence, self.steps_per_quarter)

    melody = melodies_lib.Melody()
    melody.from_quantized_sequence(quantized_sequence,
                                   search_start_step=0, instrument=0,
                                   ignore_polyphonic_notes=False)
    expected = [NO_EVENT, NO_EVENT, NO_EVENT, NO_EVENT, NO_EVENT, NO_EVENT, 12,
                NOTE_OFF, 11]
    self.assertEqual(expected, list(melody))
    self.assertEqual(16, melody.steps_per_bar)

  def testFromNotesTimeOverlap(self):
    testing_lib.add_track_to_sequence(
        self.note_sequence, 0,
        [(12, 100, 1, 2), (11, 100, 3.25, 3.75),
         (13, 100, 2, 4)])
    quantized_sequence = sequences_lib.quantize_note_sequence(
        self.note_sequence, self.steps_per_quarter)

    melody = melodies_lib.Melody()
    melody.from_quantized_sequence(quantized_sequence,
                                   search_start_step=0, instrument=0,
                                   ignore_polyphonic_notes=False)
    expected = [NO_EVENT, NO_EVENT, NO_EVENT, NO_EVENT, 12, NO_EVENT, NO_EVENT,
                NO_EVENT, 13, NO_EVENT, NO_EVENT, NO_EVENT, NO_EVENT, 11,
                NO_EVENT]
    self.assertEqual(expected, list(melody))

  def testFromNotesStepsPerBar(self):
    self.note_sequence.time_signatures[0].numerator = 7
    self.note_sequence.time_signatures[0].denominator = 8
    quantized_sequence = sequences_lib.quantize_note_sequence(
        self.note_sequence, steps_per_quarter=12)

    melody = melodies_lib.Melody()
    melody.from_quantized_sequence(quantized_sequence,
                                   search_start_step=0, instrument=0,
                                   ignore_polyphonic_notes=False)
    self.assertEqual(42, melody.steps_per_bar)

  def testFromNotesStartAndEndStep(self):
    testing_lib.add_track_to_sequence(
        self.note_sequence, 0,
        [(12, 100, 1, 2), (11, 100, 2.25, 2.5), (13, 100, 3.25, 3.75),
         (14, 100, 8.75, 9), (15, 100, 9.25, 10.75)])
    quantized_sequence = sequences_lib.quantize_note_sequence(
        self.note_sequence, self.steps_per_quarter)

    melody = melodies_lib.Melody()
    melody.from_quantized_sequence(quantized_sequence,
                                   search_start_step=18, instrument=0,
                                   ignore_polyphonic_notes=False)
    expected = [NO_EVENT, 14, NOTE_OFF, 15, NO_EVENT, NO_EVENT, NO_EVENT,
                NO_EVENT, NO_EVENT]
    self.assertEqual(expected, list(melody))
    self.assertEqual(34, melody.start_step)
    self.assertEqual(43, melody.end_step)

  def testSetLength(self):
    events = [60]
    melody = melodies_lib.Melody(events, start_step=9)
    melody.set_length(5)
    self.assertListEqual([60, NOTE_OFF, NO_EVENT, NO_EVENT, NO_EVENT],
                         list(melody))
    self.assertEqual(9, melody.start_step)
    self.assertEqual(14, melody.end_step)

    melody = melodies_lib.Melody(events, start_step=9)
    melody.set_length(5, from_left=True)
    self.assertListEqual([NO_EVENT, NO_EVENT, NO_EVENT, NO_EVENT, 60],
                         list(melody))
    self.assertEqual(5, melody.start_step)
    self.assertEqual(10, melody.end_step)

    events = [60, NO_EVENT, NO_EVENT, NOTE_OFF]
    melody = melodies_lib.Melody(events)
    melody.set_length(3)
    self.assertListEqual([60, NO_EVENT, NO_EVENT], list(melody))
    self.assertEqual(0, melody.start_step)
    self.assertEqual(3, melody.end_step)

    melody = melodies_lib.Melody(events)
    melody.set_length(3, from_left=True)
    self.assertListEqual([NO_EVENT, NO_EVENT, NOTE_OFF], list(melody))
    self.assertEqual(1, melody.start_step)
    self.assertEqual(4, melody.end_step)

  def testToSequenceSimple(self):
    melody = melodies_lib.Melody(
        [NO_EVENT, 1, NO_EVENT, NOTE_OFF, NO_EVENT, 2, 3, NOTE_OFF, NO_EVENT])
    sequence = melody.to_sequence(
        velocity=10,
        instrument=1,
        sequence_start_time=2,
        qpm=60.0)

    self.assertProtoEquals(
        'ticks_per_quarter: 220 '
        'tempos < qpm: 60.0 > '
        'total_time: 3.75 '
        'notes < '
        '  pitch: 1 velocity: 10 instrument: 1 start_time: 2.25 end_time: 2.75 '
        '> '
        'notes < '
        '  pitch: 2 velocity: 10 instrument: 1 start_time: 3.25 end_time: 3.5 '
        '> '
        'notes < '
        '  pitch: 3 velocity: 10 instrument: 1 start_time: 3.5 end_time: 3.75 '
        '> ',
        sequence)

  def testToSequenceEndsWithSustainedNote(self):
    melody = melodies_lib.Melody(
        [NO_EVENT, 1, NO_EVENT, NOTE_OFF, NO_EVENT, 2, 3, NO_EVENT, NO_EVENT])
    sequence = melody.to_sequence(
        velocity=100,
        instrument=0,
        sequence_start_time=0,
        qpm=60.0)

    self.assertProtoEquals(
        'ticks_per_quarter: 220 '
        'tempos < qpm: 60.0 > '
        'total_time: 2.25 '
        'notes < pitch: 1 velocity: 100 start_time: 0.25 end_time: 0.75 > '
        'notes < pitch: 2 velocity: 100 start_time: 1.25 end_time: 1.5 > '
        'notes < pitch: 3 velocity: 100 start_time: 1.5 end_time: 2.25 > ',
        sequence)

  def testToSequenceEndsWithNonzeroStart(self):
    melody = melodies_lib.Melody([NO_EVENT, 1, NO_EVENT], start_step=4)
    sequence = melody.to_sequence(
        velocity=100,
        instrument=0,
        sequence_start_time=0.5,
        qpm=60.0)

    self.assertProtoEquals(
        'ticks_per_quarter: 220 '
        'tempos < qpm: 60.0 > '
        'total_time: 2.25 '
        'notes < pitch: 1 velocity: 100 start_time: 1.75 end_time: 2.25 > ',
        sequence)

  def testToSequenceEmpty(self):
    melody = melodies_lib.Melody()
    sequence = melody.to_sequence(
        velocity=10,
        instrument=1,
        sequence_start_time=2,
        qpm=60.0)

    self.assertProtoEquals(
        'ticks_per_quarter: 220 '
        'tempos < qpm: 60.0 > ',
        sequence)

  def testMidiFileToMelody(self):
    filename = os.path.join(testing_lib.get_testdata_dir(), 'melody.mid')
    melody = melodies_lib.midi_file_to_melody(filename)
    expected = melodies_lib.Melody([60, 62, 64, 66, 68, 70,
                                    72, 70, 68, 66, 64, 62])
    self.assertEqual(expected, melody)

  def testSlice(self):
    testing_lib.add_track_to_sequence(
        self.note_sequence, 0,
        [(12, 100, 1, 3), (11, 100, 5, 7), (13, 100, 9, 10)])
    quantized_sequence = sequences_lib.quantize_note_sequence(
        self.note_sequence, steps_per_quarter=1)

    melody = melodies_lib.Melody()
    melody.from_quantized_sequence(quantized_sequence,
                                   search_start_step=0, instrument=0,
                                   ignore_polyphonic_notes=False)
    expected = [NO_EVENT, 12, NO_EVENT, NOTE_OFF, NO_EVENT, 11, NO_EVENT,
                NOTE_OFF, NO_EVENT, 13]
    self.assertEqual(expected, list(melody))

    expected_slice = [NO_EVENT, NO_EVENT, NO_EVENT, 11, NO_EVENT, NOTE_OFF,
                      NO_EVENT]
    self.assertEqual(expected_slice, list(melody[2:-1]))


if __name__ == '__main__':
  absltest.main()
