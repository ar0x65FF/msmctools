import xml.etree.ElementTree as ET
import sys
import miditoolkit.midi.containers
import miditoolkit.midi.parser
import miditoolkit.midi.utils
import miditoolkit.pianoroll
import mido
import json
import math
import argparse
import lz4.block
import miditoolkit

d_data = b""

#monsters data
monsters_data_file = open("mdata.json")
monsters_data = json.load(monsters_data_file)

#note
msm_to_midi_note = {
    #Nuta + 1 = Wyzej
    #Nuta + 2 = Costam
    #Nuta + 3 = Nizej
    #Nuta + 4 = Nastepny bialy klawisz
    31:58,  #   A#3
    28:59,  #   B3
    32:60,  #   C
    33:61,  #   C#4
    36:62,  #   D4
    37:63,  #   D#4
    40:64,  #   E4
    44:65,  #   F4
    45:66,  #   F#4
    48:67,  #   G4
    49:68,  #   G#4
    52:69,  #   A4
    53:70,  #   A#4
    56:71,  #   B4
    60:72,  #   C5
    61:73,  #   C#5
    64:74,  #   D5
    65:75,  #   D#5
    68:76,  #   E5
    72:77,  #   F5
    73:78,  #   F#5
    76:79,  #   G5
    77:80,  #   G#5
    80:81,  #   A5
    81:82,  #   A#5
    84:83,  #   B5
    85:84,  #   C6
}

# Class

class SongSettings:
    def __init__(self, time_numerator, time_denominator, tempobpm, song_name):
        self.time_numerator = time_numerator
        self.time_denominator = time_denominator
        self.tempobpm = tempobpm
        self.song_name = song_name

class MonsterSetting:
    def __init__(self, monster_id, volume, user_monster_id, dst_user_track_id, pos_x, pos_y, flip, muted):
        self.monster_id = monster_id
        self.volume = volume
        self.user_monster_id = user_monster_id
        self.dst_user_track_id = dst_user_track_id
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.flip = flip
        self.muted = muted

class TrackData:
    def __init__(self,lengths,notes,times,src_user_monster_id,dst_user_track_id,name):
        self.lengths = lengths
        self.notes = notes
        self.times = times
        self.src_user_monster_id = src_user_monster_id
        self.dst_user_track_id = dst_user_track_id
        self.name = name

SongSettings1 = SongSettings(4,4,120,"Song")
MonstersList = []
TracksList = []

def writeMidiFile(filename, min_note, ntime_division):
    target_filename = filename[:len(filename)-4]+".mid"
    print("Creating MIDI File: "+target_filename)

    midi = mido.MidiFile(ticks_per_beat=960)
    meta_track = mido.MidiTrack()
    midi.tracks.append(meta_track)
    meta_track.append(mido.MetaMessage('track_name', name=SongSettings1.song_name, time=0))
    meta_track.append(mido.MetaMessage('time_signature', numerator=SongSettings1.time_numerator, denominator=SongSettings1.time_denominator, time=0))
    meta_track.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(SongSettings1.tempobpm),time=0))

    note_division = 0
    if ntime_division == None:
        if min_note == 8:
            note_division = int(midi.ticks_per_beat/2)
        elif min_note == 16:
            note_division = int(midi.ticks_per_beat/4)
        elif min_note == 32:
            note_division = int(midi.ticks_per_beat/8)
        else:
            print("Min note not accepted")
            sys.exit(1)
    else:
        note_division = ntime_division

    print("MIDI: note division "+str(note_division))

    for i,mlist in enumerate(MonstersList):
        print("Track {}: {}".format(i,monsters_data[mlist.monster_id]['name']))
        tmp_track = mido.MidiTrack()
        midi.tracks.append(tmp_track)
        tmp_track.append(mido.Message('program_change', program=monsters_data[mlist.monster_id]['midi_program']))
        tmp_track.append(mido.Message('control_change', control=0,value=monsters_data[mlist.monster_id]['midi_bank_select_msb']))
        
        tmp_track.append(mido.MetaMessage('track_name', name=monsters_data[mlist.monster_id]['name']))
        tmp_track.append(mido.Message('control_change', control=102, value=mlist.pos_x))
        tmp_track.append(mido.Message('control_change', control=103, value=mlist.pos_y))
        tmp_track.append(mido.Message('control_change', control=104, value=mlist.flip))
        tmp_track.append(mido.Message('control_change', control=105, value=mlist.muted))
        tmp_track.append(mido.Message('control_change', control=7, value=int(translateVolume(mlist.volume,float(0), float(1), 0, 127))))
        
        for ttdata in TracksList:
            #print(ttdata.notes)
            if mlist.dst_user_track_id == ttdata.dst_user_track_id:
                for xnote,xlen,xpos in zip(ttdata.notes, ttdata.lengths, ttdata.times):
                    delta_note_start = (xpos * note_division)
                    delta_note_stop = (xpos * note_division) + (xlen * note_division)
                break
    midi.save(target_filename)

def writeMidiFile2(filename,min_note, ntime_division, outfile):
    if outfile == None:
        target_filename = filename[:len(filename)-4]+".mid"
    else:
        target_filename = outfile
    print("Creating MIDI File: "+target_filename)

    midi = miditoolkit.midi.parser.MidiFile()

    note_division = 0
    if ntime_division == None:
        if min_note == 8:
            note_division = int(midi.ticks_per_beat/2)
        elif min_note == 16:
            note_division = int(midi.ticks_per_beat/4)
        elif min_note == 32:
            note_division = int(midi.ticks_per_beat/8)
        else:
            print("Min note not accepted")
            sys.exit(1)
    else:
        note_division = ntime_division

    print("MIDI: note division "+str(note_division))

    for i,mlist in enumerate(MonstersList):
        print("Track {}: {}".format(i,monsters_data[mlist.monster_id]['name']))
        track = miditoolkit.midi.containers.Instrument(program=monsters_data[mlist.monster_id]['midi_program'], is_drum=False, name=monsters_data[mlist.monster_id]['name'])
        track.control_changes.append(miditoolkit.midi.containers.ControlChange(number=102, value=mlist.pos_x, time=0))
        track.control_changes.append(miditoolkit.midi.containers.ControlChange(number=103, value=mlist.pos_y, time=0))
        track.control_changes.append(miditoolkit.midi.containers.ControlChange(number=104, value=mlist.flip, time=0))
        track.control_changes.append(miditoolkit.midi.containers.ControlChange(number=105, value=mlist.muted, time=0))
        track.control_changes.append(miditoolkit.midi.containers.ControlChange(number=7, value=int(translateVolume(mlist.volume,float(0), float(1), 0, 127)), time=0))
        track.control_changes.append(miditoolkit.midi.containers.ControlChange(number=0, value=monsters_data[mlist.monster_id]['midi_bank_select_msb'], time=0))

        midi.instruments.append(track)
        for ttdata in TracksList:
            if mlist.dst_user_track_id == ttdata.dst_user_track_id:
                for xnote,xlen,xpos in zip(ttdata.notes, ttdata.lengths, ttdata.times):
                    delta_note_start = (xpos * note_division)
                    delta_note_stop = (xpos * note_division) + (xlen * note_division)

                    note = miditoolkit.midi.containers.Note(velocity=100, pitch=msm_to_midi_note[xnote], start=delta_note_start, end=delta_note_stop)
                    miditoolkit.midi
                    track.notes.append(note)

                break
    
    midi.dump(target_filename)


def testXmlFile(root,skip_time_signature,tempo):
    print("Reading XML Data")
    if skip_time_signature == False:
        SongSettings1.time_numerator = int(root.find(".//INT[@key='time_numerator']").get("value"))
        SongSettings1.time_denominator = int(root.find(".//INT[@key='time_denom']").get("value"))
    if tempo == None:
        SongSettings1.tempobpm = int(root.find(".//INT[@key='tempo']").get("value"))
    else:
        SongSettings1.tempobpm = tempo
    SongSettings1.song_name = root.find(".//STRING[@key='name']").get("value")
    monstersarray = root.find(".//SFSARRAY[@key='monsters']")
    monsterstrackassign = root.find(".//SFSOBJECT[@key='song'].//SFSARRAY[@key='tracks']")
    for child in monstersarray:
        tmpMonster = MonsterSetting(200,1.0,0,0,0,0,0,0)
        tmpMonster.flip = int(child.find(".//INT[@key='flip']").get("value"))
        tmpMonster.monster_id = child.find(".//INT[@key='monster']").get("value")
        tmpMonster.muted = int(child.find(".//INT[@key='muted']").get("value"))
        tmpMonster.pos_x = int(child.find(".//INT[@key='pos_x']").get("value"))
        tmpMonster.pos_y = int(child.find(".//INT[@key='pos_y']").get("value"))
        tmpMonster.user_monster_id = int(child.find(".//LONG[@key='user_monster_id']").get("value")[0:2])
        tmpMonster.volume = float(child.find(".//DOUBLE[@key='volume']").get("value"))
        for child2 in monsterstrackassign.findall(".//SFSOBJECT"):
            if tmpMonster.user_monster_id == int(child2.find(".//LONG[@key='monster']").get("value")[0:2]):
                tmpMonster.dst_user_track_id = int(child2.find(".//LONG[@key='track']").get("value")[0:2])
                break
        MonstersList.append(tmpMonster)
        #print(vars(tmpMonster))
    trackdata = root[1]
    for child in trackdata:
        tmpLen = []
        tmpNote = []
        tmpPos = []

        len_str = child.find(".//INTARRAY[@key='lengths']").text
        if len_str != None:
            len_str = len_str[:len(len_str)-1]
            tmpLen = list(map(int, len_str.split(",")))

        note_str = child.find(".//INTARRAY[@key='notes']").text
        if note_str != None:
            note_str = note_str[:len(note_str)-1]
            tmpNote = list(map(int, note_str.split(",")))

        pos_str = child.find(".//INTARRAY[@key='times']").text
        if pos_str != None:
            pos_str = pos_str[:len(pos_str)-1]
            tmpPos = list(map(int, pos_str.split(",")))

        dst_user_track_id = int(child.find(".//LONG[@key='user_track_id']").get("value")[0:2])
        tmpTrack = TrackData(tmpLen, tmpNote, tmpPos, 0, dst_user_track_id, "")
        TracksList.append(tmpTrack)
    
def translateVolume(value, leftMin, leftMax, rightMin, rightMax):
    leftSpan = leftMax - leftMin
    rightSpan = rightMax - rightMin
    valueScaled = float(value - leftMin) / float(leftSpan)
    return rightMin + (valueScaled * rightSpan)


def decompress_data(filename,write_xml=None):
    global d_data
    print("Decompressing file "+filename+"...")
    with open(filename, 'rb') as f:
        rawdata = f.read()

    ccvariable = True
    filesize = len(rawdata)
    trysize = 0
    
    while True:
        try:
            decompressed_data = None
            decompressed_data = lz4.block.decompress(rawdata, uncompressed_size=filesize+trysize)
            if decompressed_data != None:
                d_data = decompressed_data[:len(decompressed_data)-1] # Drop 0x00 at the end
                break
        except:
            trysize += 1
    
    if write_xml == True:
        print("Writing XML File")
        dest_file = filename[:len(filename)-4]+'.xml'
        with open(dest_file, 'wb') as f:
            f.write(decompressed_data[:len(decompressed_data)-1]) # Drop 0x00 at the end
            f.close()
        

parser = argparse.ArgumentParser(prog="msm2mid", description="Convert MSM file into MIDI file")
parser.add_argument('--write-xml', action=argparse.BooleanOptionalAction,default=False, help="Write XML File")
parser.add_argument('--skip-time-signature', action=argparse.BooleanOptionalAction,default=False,help="Skip tempo signature (default 4/4)")
parser.add_argument('--tempo', metavar=120, type=int, help='Overwrite tempo in target MIDI file')
parser.add_argument('--division', type=int, help="MIDI Note division")
parser.add_argument('--min-note', type=int, default=8, help="1/X (8/16/32)")
parser.add_argument('--outfile',type=str)
parser.add_argument('MSMFILE', type=str)

args = parser.parse_args()
decompress_data(args.MSMFILE,args.write_xml)

dest_str = d_data.decode("utf-8")
root = ET.fromstring(dest_str)

testXmlFile(root,args.skip_time_signature, args.tempo)
writeMidiFile2(args.MSMFILE, args.min_note, args.division, args.outfile)