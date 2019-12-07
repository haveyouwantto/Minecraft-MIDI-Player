import mido

# TODO 
def parse_midi(file):
    mid=mido.MidiFile(file)
    time=0
    for i in mid:
        print(time,i)
        time+=(i.time)

if __name__ == "__main__":
    parse_midi(r'midis\e.mid')