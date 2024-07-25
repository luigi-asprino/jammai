from typing import List
import pandas as pd
import math
from itertools import groupby, combinations
from collections import defaultdict, namedtuple
import re
import os
from datetime import timedelta

from minizinc import Instance, Model, Solver


class BaseMusicCSP(object):
    NUM_MEASURES_KEY = "L"
    SAT_ONLY = False

    def __init__(self, meta_path: str, num_tracks: int):
        meta = pd.read_csv(meta_path)

        # map id to actual path
        BASE = os.path.dirname(meta_path)
        meta["path"] = meta.apply(lambda r: os.path.join(BASE, "commu_midi", r.split_data, "raw", r.id + ".mid"), axis=1)

        # reduce instruments to unique
        meta["inst"] = meta.inst.map(lambda i: re.sub(r"-\d+", "", i))
        # only pick 4/4 samples
        meta = meta[meta["time_signature"] == "4/4"]
        
        self.meta = meta.reset_index(drop=True)
        self.paths = meta.path.tolist()

        self.num_tracks = num_tracks
        self.setup_csp()

    def setup_csp(self):
        raise NotImplementedError

    def parse_solution(self, solution):
        raise NotImplementedError
        
    def generate(self, num_measures: int, seconds: int = 40, solver: str = "gecode"):
        self.model[self.NUM_MEASURES_KEY] = num_measures
        solver = Solver.lookup(solver)
        instance = Instance(solver, self.model)
        
        if self.SAT_ONLY:
            result = instance.solve(timeout=timedelta(seconds=seconds), all_solutions=True)    
        else:
            result = instance.solve(timeout=timedelta(seconds=seconds), intermediate_solutions=True)

        # parse result
        output = []
        for sol in result.solution:
            sol_d = self.parse_solution(sol)
            
            if not self.SAT_ONLY:
                sol_d["objective"] = sol.objective
            
            output.append(sol_d)

        return output


class RoleMusicCSP(BaseMusicCSP):
    SAT_ONLY = True

    def setup_csp(self):
        # define CSP structure based on pool
        # each group has a array of N, since it can be composed of a different sample
        # for each measure. The domain of each array is the number of samples available in the group.
        self.model = Model("models/naive.mzn")
    
        # set CSP variables
        self.model["N"] = self.meta.shape[0]
        
        # bind ids for variables
        self.num_measures = {i: row.num_measures for i, row in self.meta.iterrows()}
        self.model["num_measures"] = list(self.num_measures.values())
        
        self.model["NUM_TRACKS"] = self.num_tracks

        self.ROLE_MAP = self.meta.track_role.unique().tolist()
        self.roles = {i: self.ROLE_MAP.index(row.track_role) + 1 for i, row in self.meta.iterrows()}
        self.model["NUM_ROLES"] = len(self.ROLE_MAP)
        self.model["roles"] = list(self.roles.values())

        self.INSTRUMENT_MAP = self.meta.inst.unique().tolist()
        self.instruments = {i: self.INSTRUMENT_MAP.index(row.inst) + 1 for i, row in self.meta.iterrows()}
        self.model["NUM_INSTRUMENTS"] = len(self.INSTRUMENT_MAP)
        self.model["instruments"] = list(self.instruments.values())

        # setup the features of each sample for the objective function
        self.features = {
            i: [
                row["Strongest_Rhythmic_Pulse"] / 100,
            ]
            for i, row in self.meta.iterrows()
        }
        self.model["NUM_FEATURES"] = len(self.features[0])
        self.model["features"] = list(self.features.values())

        self.samples = {i: row.id for i, row in self.meta.iterrows()}

    def parse_solution(self, solution):
        return {
            f"track_{track_i}": [
                (self.samples[sample_i], self.paths[sample_i], self.features[sample_i])
                for sample_i in solution.segment[track_i]
                if sample_i in self.samples
            ]
            for track_i in range(self.num_tracks)
        }
        

class FeatureMusicCSP(BaseMusicCSP):
    SAT_ONLY = False

    def setup_csp(self):
        # define CSP structure based on pool
        # each group has a array of N, since it can be composed of a different sample
        # for each measure. The domain of each array is the number of samples available in the group.
        self.model = Model("models/features.mzn")
    
        # set CSP variables
        self.model["N"] = self.meta.shape[0]
        
        # bind ids for variables
        self.num_measures = {i: row.num_measures for i, row in self.meta.iterrows()}
        self.model["num_measures"] = list(self.num_measures.values())
        
        self.model["NUM_TRACKS"] = self.num_tracks

        self.INSTRUMENT_MAP = self.meta.inst.unique().tolist()
        self.instruments = {i: self.INSTRUMENT_MAP.index(row.inst) + 1 for i, row in self.meta.iterrows()}
        self.model["NUM_INSTRUMENTS"] = len(self.INSTRUMENT_MAP)
        self.model["instruments"] = list(self.instruments.values())

        # setup the features of each sample for the objective function
        self.features = {
            i: [
                row["Strongest_Rhythmic_Pulse"],
            ]
            for i, row in self.meta.iterrows()
        }
        self.model["NUM_FEATURES"] = len(self.features[0])
        self.model["features"] = list(self.features.values())

        self.samples = {i: row.id for i, row in self.meta.iterrows()}

    def parse_solution(self, solution):
        return {
            f"track_{track_i}": [
                (self.samples[sample_i], self.paths[sample_i], self.features[sample_i])
                for sample_i in solution.segment[track_i]
                if sample_i in self.samples
            ]
            for track_i in range(self.num_tracks)    
        }
        
