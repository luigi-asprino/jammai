from time import time_ns
from jammai.generator import MusicCSP
import mido

mcsp = MusicCSP("/home/n28div/projects/jammai/dataset/commu_meta.csv")

start_s = time_ns()
samples = mcsp.generate(4, segments=1)
end_s = time_ns()

print(f"Took {end_s - start_s}")

for i, sample in enumerate(samples):
    print("Sample", i)
    
    ticks_per_beat = 180
    midi = mido.MidiFile()
    midi.ticks_per_beat = ticks_per_beat

    for role_name, v in sample.items():
        midi.add_track(name=role_name)

        for name, path in v:
            v_midi = mido.MidiFile(path, ticks_per_beat=ticks_per_beat)
            midi.tracks[-1].extend(v_midi.tracks[-1])
    
    midi.save(f"gen_{i}.mid")
        
