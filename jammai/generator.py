from typing import List
import pandas as pd
import math
from itertools import groupby, combinations
from collections import defaultdict, namedtuple
import re
import os

from minizinc import Instance, Model, Solver


class MusicCSP(object):
    def __init__(self, meta_path: str):
        meta = pd.read_csv(meta_path, index_col=0)

        # map id to actual path
        BASE = os.path.dirname(meta_path)
        meta["path"] = meta.apply(lambda r: os.path.join(BASE, "commu_midi", r.split_data, "raw", r.id + ".mid"), axis=1)

        # reduce instruments to unique
        meta["inst"] = meta.inst.map(lambda i: re.sub(r"-\d+", "", i))
        # only pick 4/4 samples
        meta = meta[meta["time_signature"] == "4/4"]
        
        meta = meta.reset_index(drop=True)
        
        self.paths = meta.path.tolist()

        # define CSP structure based on pool
        # each group has a array of N, since it can be composed of a different sample
        # for each measure. The domain of each array is the number of samples available in the group.
        self.model = Model("models/naive.mzn")
        
        # set CSP variables
        self.model["N"] = meta.shape[0]
        
        # bind ids for variables
        self.num_measures = {i: row.num_measures for i, row in meta.iterrows()}
        self.model["num_measures"] = list(self.num_measures.values())
        
        self.ROLE_MAP = meta.track_role.unique().tolist()
        self.roles = {i: self.ROLE_MAP.index(row.track_role) + 1 for i, row in meta.iterrows()}
        self.model["NUM_ROLES"] = len(self.ROLE_MAP)
        self.model["roles"] = list(self.roles.values())

        self.INSTRUMENT_MAP = meta.inst.unique().tolist()
        self.instruments = {i: self.INSTRUMENT_MAP.index(row.inst) + 1 for i, row in meta.iterrows()}
        self.model["NUM_INSTRUMENTS"] = len(self.INSTRUMENT_MAP)
        self.model["instruments"] = list(self.instruments.values())

        self.samples = {i: row.id for i, row in meta.iterrows()}
        
    def generate(self, num_measures: int, segments: int = 1):
        self.model["L"] = num_measures
        solver = Solver.lookup("gecode")
        instance = Instance(solver, self.model)
        result = instance.solve(nr_solutions=segments)

        # parse result
        output = [
            {
                role_k: [ 
                    (self.samples[sample_i], self.paths[sample_i])
                    for sample_i in output.segment[role_i] if sample_i in self.samples 
                ]
                for role_i, role_k in enumerate(self.ROLE_MAP)
            }
            for output in result.solution
        ]

        return output
    
    
#         main_melody_ids = get_domain_from_track_role(df, "main_melody")
# main_melody_num_measures = get_num_measures_array(df, main_melody_ids)
# main_melody_instruments = get_instrument_array(df, main_melody_ids, instruments)
# main_melody_scores = get_score_array(main_melody_ids, sample_score_example)
# print(f"Number of samples with main_melody role: {len(main_melody_ids)}")


# # Sample can be repeated 0, 1 or 2 times in a segment to match the number of measures of the samples in the other tracks
# sample_repetitions = {1, 2}

# num_measures = [int(m) for m in df.num_measures.unique()]