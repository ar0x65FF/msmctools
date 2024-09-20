# My Singing Monsters Composer MIDI Tools
Warning: Before use please backup all your song in My Singing Monster: Composer<br />

<br />

Python dependencies:
```
mido
lz4
miditoolkit (only for msm2mid)
```
## mid2msm

MIDI file to msm file

Usage:
```
python mid2msm.py MIDIFILE.mid
```

For more information:
```
python mid2msm.py -h
```
<br>

### Creating MIDI File

- MIDI file must be in Format 1 (Monster per track)
- Tested on TPQN 960
- MIDI notes from A#3(58) to C6(84)
    - C2 and C3 will be mapped to C4 and C5
    - C6 will be mapped back to C5
- MIDI controllers as:
    - 102 for X
    - 103 for Y
    - 104 for flip (1 - true, 0 - false)
    - 105 for muted (1 - true, 0 - false)
- Make sure all notes are in grid
- Select a instrument: <a href="docs/instrument_table.md">Instrument table</a>
- You can specify min note length (1/8, 1/16, 1/32)

## msm2mid

MSM file to MIDI file

Key signatures other than C Major/A Minor is not currently supported

Usage:
```
python msm2mid.py MSMFILE.msm
```

For more information:
```
python msm2mid.py -h
```
<br>