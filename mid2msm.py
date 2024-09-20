import xml.etree.ElementTree as ET
import sys
import mido
import json
import math
import argparse
import lz4.block

#Filenames
out_xml_msm_filename = None
midi_input_filename = None

monster_data_file = open("mdata.json")
monster_data = json.load(monster_data_file)


#Class

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

midi_to_msm_note = {
    #Nuta + 1 = Wyzej
    #Nuta + 2 = Costam
    #Nuta + 3 = Nizej
    #Nuta + 4 = Nastepny bialy klawisz
    58:31,  #   A#3
    59:28,  #   B3
    60:32,  #   C
    61:33,  #   C#4
    62:36,  #   D4
    63:37,  #   D#4
    64:40,  #   E4
    65:44,  #   F4
    66:45,  #   F#4
    67:48,  #   G4
    68:49,  #   G#4
    69:52,  #   A4
    70:53,  #   A#4
    71:56,  #   B4
    72:60,  #   C5
    73:61,  #   C#5
    74:64,  #   D5
    75:65,  #   D#5
    76:68,  #   E5
    77:72,  #   F5
    78:73,  #   F#5
    79:76,  #   G5
    80:77,  #   G#5
    81:80,  #   A5
    82:81,  #   A#5
    83:84,  #   B5
    84:85,  #   C6
}


MonstersList = []
TracksList = []

SongSetting1 = SongSettings(4,4,120,"Song")

#XML/MSM-File Structure BEGIN

root = ET.Element('SFSOBJECT', key="root")
monsters_and_tracks_settings_array = ET.SubElement(root, 'SFSARRAY', key="islands")
monsters_and_tracks_settings_object = ET.SubElement(monsters_and_tracks_settings_array, 'SFSOBJECT', key="")
ET.SubElement(monsters_and_tracks_settings_object, 'INT', key="island", value='11')
monsters_settings_array = ET.SubElement(monsters_and_tracks_settings_object, 'SFSARRAY', key="monsters")
song_title = ET.SubElement(monsters_and_tracks_settings_object, 'STRING', key="name", value="")
song_settings = ET.SubElement(monsters_and_tracks_settings_object, 'SFSOBJECT', key="song")

song_key_sig = ET.SubElement(song_settings, 'INT', key="key_sig",value="0")
song_tempo = ET.SubElement(song_settings, 'INT', key="tempo",value="0")
song_time_denom = ET.SubElement(song_settings, 'INT', key="time_denom",value="0")
song_time_numerator = ET.SubElement(song_settings, 'INT', key="time_numerator",value="0")

tracks_assign = ET.SubElement(song_settings, 'SFSARRAY', key="tracks")
ET.SubElement(song_settings, 'LONG', key="user", value="1 0")

ET.SubElement(monsters_and_tracks_settings_object, 'LONG', key="user", value="1 0")
ET.SubElement(monsters_and_tracks_settings_object, 'LONG', key="user_island_id", value="1 0")


tracks_list = ET.SubElement(root, 'SFSARRAY', key="tracks")

ET.SubElement(root, 'INT', key="versionCode", value="3")
#XML/MSM-File Structure END

def testMidiFile(g_tempo=None,note_division=None, min_note=None):
    midi = None
    try:
        midi = mido.MidiFile(midi_input_filename)
    except:
        print("Invalid MIDI File!")
        sys.exit(1)
    
    print("PPQ: "+str(midi.ticks_per_beat))

    if min_note != None:
        if min_note == 8:
            note_division = midi.ticks_per_beat/2
        elif min_note == 16:
            note_division = midi.ticks_per_beat/4
        elif min_note == 32:
            note_division = midi.ticks_per_beat/8
        else:
            note_division = midi.ticks_per_beat/2
    else:
        note_division = midi.ticks_per_beat/2
    
    for i,track in enumerate(midi.tracks):
        if i == 0:
            for msg in track:
                if msg.type == 'track_name':
                    SongSetting1.song_name = msg.name
                if msg.type == 'time_signature':
                    SongSetting1.time_numerator = msg.numerator
                    SongSetting1.time_denominator = msg.denominator
                if msg.type == 'set_tempo':
                    print("MIDI Tempo: "+str(msg.tempo))
                    if g_tempo == None: 
                        SongSetting1.tempobpm = int(mido.tempo2bpm(msg.tempo))
                        g_tempo = int(mido.tempo2bpm(msg.tempo))
                    else:
                        SongSetting1.tempobpm = int(g_tempo)

        if i > 0:
            tmpMonster = MonsterSetting(200,1,i,i+1,None,None,None,0)
            
            delta_midi_time = 0
            allnotesdata = []
            
            midi_program = 0
            midi_bank_select = 0

            for g,msg in enumerate(track):
                if msg.type == 'control_change' and msg.control == 7:
                    tmpMonster.volume = float("{:.6f}".format(translateVolume(msg.value,0,127,float(0), float(1))))
                    delta_midi_time += msg.time
                if msg.type == 'control_change' and msg.control == 102:
                    tmpMonster.pos_x = msg.value
                    delta_midi_time += msg.time
                if msg.type == 'control_change' and msg.control == 103:
                    tmpMonster.pos_y = msg.value
                    delta_midi_time += msg.time
                if msg.type == 'control_change' and msg.control == 104:
                    if msg.value == 0:
                        tmpMonster.flip = 0
                    elif msg.value > 0:
                        tmpMonster.flip = 1
                    delta_midi_time += msg.time
                if msg.type == 'control_change' and msg.control == 105:
                    if msg.value == 0:
                        tmpMonster.muted = 0
                    elif msg.value > 0:
                        tmpMonster.muted = 1
                    delta_midi_time += msg.time
                if msg.type == 'program_change':
                    midi_program = msg.program
                    delta_midi_time += msg.time
                    #MIDI Program
                if msg.type == "control_change" and msg.control == 0:
                    midi_bank_select = msg.value
                    delta_midi_time += msg.time
                    #MIDI Bank Select
                '''if msg.type == 'instrument_name':
                    for key in json_data_tmp:
                        if(json_data_tmp[key]['name'] == msg.name):
                            tmpMonster.monster_id = int(key) 
                    delta_midi_time += msg.time    '''               

                #NOTE ON
                if msg.type == 'note_on':
                    delta_midi_time += msg.time
                    notedata = {'note': 0, 'delta_start': 0, 'delta_stop': 0}
                    
                    #Note on with velocity 0 is note off
                    if msg.velocity == 0:
                        for l,key in enumerate(allnotesdata):
                            if msg.note == key['note'] and key['delta_stop'] == 0:
                                key['delta_stop'] = delta_midi_time
                                break
                            else:
                                continue
                        continue

                    notedata['note'] = msg.note
                    notedata['delta_start'] = delta_midi_time
                    
                    allnotesdata.append(notedata)
                #NOTE OFF
                if msg.type == 'note_off':
                    delta_midi_time += msg.time
                    for l,key in enumerate(allnotesdata):
                        if msg.note == key['note'] and key['delta_stop'] == 0:
                            key['delta_stop'] = delta_midi_time
                            break
                        else:
                            continue
            note_num = []
            note_pos = []
            note_len = []



            for l,key in enumerate(allnotesdata):
                note = key['note']
                if note <= 57 and note >= 36:
                    note = note + 24
                elif note <= 96 and note >= 85:
                    note = note - 12
                elif note >= 58 and note <= 84:
                    note = note
                else:
                    print("Key out of range Track {} key {}".format(i,note))
                    sys.exit(1)
                
                if int((key['delta_stop'] - key['delta_start'])/note_division) == 0:
                    print("Detected invalid note with length 0 at Track {}. Please check your midi file or use --min-note".format(i))
                    sys.exit(1)

                note_num.append(midi_to_msm_note[note])
                note_pos.append(int(key['delta_start']/note_division))
                note_len.append(int((key['delta_stop'] - key['delta_start'])/note_division))
                

            for key in monster_data:
                if(monster_data[key]['midi_program'] == midi_program and monster_data[key]['midi_bank_select_msb'] == midi_bank_select):
                    tmpMonster.monster_id = int(key) 
                    break

            tmpTrackData = TrackData(note_len,note_num,note_pos,i,i+1,"")
            print("Track {} instrument: {}, id: {}, notes: {}".format(i,monster_data[str(tmpMonster.monster_id)]['name'],tmpMonster.monster_id,len(note_num)))

            TracksList.append(tmpTrackData)
            MonstersList.append(tmpMonster)       
                

def WriteToXmlFile():
    song_time_numerator.set("value", str(SongSetting1.time_numerator))
    song_time_denom.set("value", str(SongSetting1.time_denominator))
    song_tempo.set("value",str(SongSetting1.tempobpm))
    song_title.set("value", str(SongSetting1.song_name))

    for monster in MonstersList:
        tmp_x = ET.SubElement(monsters_settings_array,'SFSOBJECT', key="")

        if monster.flip == None:
            ET.SubElement(tmp_x,'INT', key="flip", value=str(monster_data[str(monster.monster_id)]['flip']))
        else:
            ET.SubElement(tmp_x,'INT', key="flip", value=str(monster.flip))
        
        ET.SubElement(tmp_x,'INT', key="monster", value=str(monster.monster_id))
        
        if monster.pos_x == None:
            ET.SubElement(tmp_x,'INT', key="pos_x", value=str(monster_data[str(monster.monster_id)]['pos_x']))
        else:
            ET.SubElement(tmp_x,'INT', key="pos_x", value=str(monster.pos_x))
        if monster.pos_y == None:
            ET.SubElement(tmp_x,'INT', key="pos_y", value=str(monster_data[str(monster.monster_id)]['pos_y']))
        else:
            ET.SubElement(tmp_x,'INT', key="pos_y", value=str(monster.pos_y))


        ET.SubElement(tmp_x,'INT', key="muted", value=str(monster.muted))
        ET.SubElement(tmp_x, 'LONG', key="user_monster_id", value=str(monster.user_monster_id)+" 0")
        ET.SubElement(tmp_x, 'DOUBLE', key="volume", value=str(monster.volume))
        tmp_y = ET.SubElement(tracks_assign,'SFSOBJECT',key="")
        ET.SubElement(tmp_y, 'LONG', key="monster", value=str(monster.user_monster_id)+" 0")
        ET.SubElement(tmp_y, 'LONG', key="track", value=str(monster.dst_user_track_id)+" 0")
    
    for tracks in TracksList:
        tmp_x = ET.SubElement(tracks_list,'SFSOBJECT', key="")
        ET.SubElement(tmp_x, 'INT', key="format", value="2 0")
        
        #lengths
        tmp_array_lengths = ET.SubElement(tmp_x,'INTARRAY', key="lengths")
        tmp_text = ""
        for length in tracks.lengths:
            tmp_text = tmp_text + str(length)+","
        tmp_array_lengths.text = tmp_text

        ET.SubElement(tmp_x,'STRING', key="name", value=str(tracks.name))

        #notes
        tmp_notes_arr = ET.SubElement(tmp_x,'INTARRAY', key="notes")
        tmp_text = ""
        for note in tracks.notes:
            tmp_text = tmp_text+str(note)+","
        tmp_notes_arr.text = tmp_text

        #times
        tmp_times_arr = ET.SubElement(tmp_x,'INTARRAY', key="times")
        tmp_text = ""
        for time in tracks.times:
            tmp_text = tmp_text+str(time)+","
        tmp_times_arr.text = tmp_text

        ET.SubElement(tmp_x,'LONG', key="user", value="1 0")
        ET.SubElement(tmp_x,'LONG', key="user_track_id", value=str(tracks.dst_user_track_id)+" 0")



def translateVolume(value, leftMin, leftMax, rightMin, rightMax):
    leftSpan = leftMax - leftMin
    rightSpan = rightMax - rightMin
    valueScaled = float(value - leftMin) / float(leftSpan)
    return rightMin + (valueScaled * rightSpan)

def compressFile(data,write_xml=False):
    if write_xml == True:
        print("Writting XML file...")
        xml_filename = out_xml_msm_filename[:len(out_xml_msm_filename)-4]+".xml"
        with open(xml_filename, 'wb') as f:
            f.write(data)
            f.close()

    print("Compressing file...")
    compressed_data = lz4.block.compress(data+b'\0', compression=9, mode="high_compression",store_size=False)

    with open(out_xml_msm_filename, 'wb') as f:
        f.write(compressed_data)
        f.close()

parser = argparse.ArgumentParser(prog='mid2msm',description="Convert MIDI file into MSM file")
parser.add_argument('--out', metavar="OUTFILE",type=str, help="Specify output file")
parser.add_argument('--division',metavar=480,type=int, help='MIDI division time (default=480)')
parser.add_argument('--tempo', metavar=120, type=int, help='Overwrite tempo in MIDI file')
parser.add_argument('--min-note', type=int, help="1/X (8/16/32)")
parser.add_argument('--write-xml', action=argparse.BooleanOptionalAction, default=False)
parser.add_argument('MIDIFILE', type=str)


args = parser.parse_args()

midi_input_filename = str(args.MIDIFILE)
if args.out == None:
    out_xml_msm_filename = midi_input_filename[:len(midi_input_filename)-4]+".msm"
else:
    out_xml_msm_filename = str(args.out)

print("Parsing MIDI File...")
testMidiFile(args.tempo, args.division, args.min_note)

print("Writing XML/MSM file...")
WriteToXmlFile()

ET.indent(root,space='\t',level=0)
b_xml = ET.tostring(root,short_empty_elements=True)
b_xmlhead = bytearray()
b_xmlhead.extend(map(ord, "<?xml version=\"1.0\"?>\n"))

compressFile(b_xmlhead+b_xml,args.write_xml)
