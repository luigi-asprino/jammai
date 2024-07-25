from time import time_ns
from jammai.generator import RoleMusicCSP, FeatureMusicCSP
import mido
import argparse

argparser = argparse.ArgumentParser()
argparser.add_argument("--meta", required=True, type=str)
argparser.add_argument("--num-tracks", required=True, type=int)
argparser.add_argument("--model", required=True, type=str, choices=["role", "features"])
argparser.add_argument("--measures", required=True, type=int)
argparser.add_argument("--max-time", required=False, type=float, default=30)

CSP_CLASS = {
    "role": RoleMusicCSP,
    "features": FeatureMusicCSP
}

if __name__ == "__main__":
    args = argparser.parse_args()

    mcsp = CSP_CLASS[args.model](args.meta, num_tracks=args.num_tracks)
    samples = mcsp.generate(args.measures, args.max_time)

    for i, sample in enumerate(samples):
        ticks_per_beat = 180
        midi = mido.MidiFile()
        midi.ticks_per_beat = ticks_per_beat

        objective = sample.pop("objective", "SAT")

        for role_name, v in sample.items():
            midi.add_track(name=role_name)

            for name, path, _ in v:
                v_midi = mido.MidiFile(path, ticks_per_beat=ticks_per_beat)
                midi.tracks[-1].extend(v_midi.tracks[-1])
        
        midi.save(f"gen_{i}_{objective}.mid")
            
