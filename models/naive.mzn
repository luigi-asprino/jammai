include "globals.mzn";


% initialize search space
int: L; % num of measures to have in the final segment
set of int: MEASURES = 1..L;
array[SAMPLES] of int: num_measures;

int: NUM_TRACKS;
set of int: TRACKS = 1..NUM_TRACKS;

int: NUM_ROLES;
set of int: ROLES = 1..NUM_ROLES;
array[SAMPLES] of ROLES: roles;

int: NUM_INSTRUMENTS;
set of int: INSTRUMENTS = 1..NUM_INSTRUMENTS;
array[SAMPLES] of INSTRUMENTS: instruments;

int: N; % num of samples in the dataset
int: E = N + 1; % num of samples in the dataset + one sample used for padding
set of int: SAMPLES = 1..N;
set of int: SAMPLES_WITH_EMPTY = 1..E;

% the segment is modeled as a ROLESxL grid where ROLES = 6 for now, since at most we can have one sample
% sized 1 measure repeated L times for each timestep
array[TRACKS, MEASURES] of var SAMPLES_WITH_EMPTY : segment;

% the length of the segments have to match L
constraint forall (r in TRACKS) (sum(t in MEASURES where segment[r, t] != E) (num_measures[segment[r, t]]) = L);

% constrain each row of segment to only contain samples of that role
constraint forall (r in TRACKS, t in MEASURES where segment[r, t] != E) (r == roles[segment[r, t]]);

% constrain each row of segment to only contain samples of that instrument
constraint forall (r in TRACKS) (nvalue([instruments[segment[r, t]] | t in MEASURES where segment[r, t] != E]) = 1);

solve :: int_search(segment, first_fail, outdomain_random)
      satisfy;

output [ 
        show_int(5, segment[i,j]) ++
        if j = L  then "\n" else " " endif
       | i in TRACKS, j in MEASURES]; 