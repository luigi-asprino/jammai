include "globals.mzn";

int: N; % num of samples in the dataset
int: E = N + 1; % num of samples in the dataset + one sample used for padding
set of int: SAMPLES = 1..N;
set of int: SAMPLES_WITH_EMPTY = 1..E;

int: NUM_TRACKS;
set of int: TRACKS = 1..NUM_TRACKS;

% initialize search space
int: L; % num of measures to have in the final segment
set of int: MEASURES = 1..L;
array[SAMPLES] of int: num_measures;

int: NUM_INSTRUMENTS;
set of int: INSTRUMENTS = 1..NUM_INSTRUMENTS;
array[SAMPLES] of INSTRUMENTS: instruments;

% the segment is modeled as a TRACKS grid where ROLES = 6 for now, since at most we can have one sample
% sized 1 measure repeated L times for each timestep
array[TRACKS, MEASURES] of var SAMPLES_WITH_EMPTY : segment;

% the length of the segments have to match L
constraint forall (r in TRACKS) (sum(t in MEASURES where segment[r, t] != E) (num_measures[segment[r, t]]) = L);

% constrain each row of segment to only contain samples of that instrument
constraint forall (r in TRACKS) (nvalue([instruments[segment[r, t]] | t in MEASURES where segment[r, t] != E]) = 1);

% load features for the objective function
int: NUM_FEATURES; % total number of features
set of int: FEATURES = 1..NUM_FEATURES;
array[FEATURES, SAMPLES] of float: features;

% constrain each feature to have the right value or 0 if the empty sample is used
array[1..(NUM_TRACKS * L * NUM_FEATURES)] of var float: segment_feature = [
      if segment[r, t] != E then features[f, segment[r, t]] else 0.0 endif
      | r in TRACKS, t in MEASURES, f in FEATURES
];

% objective function: we compute the variance of each feature and try to minimize it
function var float: average(array[int] of var opt float: x) = sum(x) / length(x);

function var float: squared_average(array[int] of var opt float: x) = average(x) * average(x);

function var float: average_of_squares(array[int] of var opt float: x) = sum([i * i | i in x]) / length(x);

function var float: variance(array[int] of var opt float: x) = average_of_squares(x) - squared_average(x);

array[1..(NUM_TRACKS * NUM_FEATURES)] of var float: features_variance = [
      variance([segment_feature[r * t * f] | t in MEASURES where segment[r, t] != E]) | r in TRACKS, f in FEATURES
];

solve minimize sum(features_variance);

output [ 
        show_int(5, segment[i,j]) ++
        if j = L  then "\n" else " " endif
       | i in TRACKS, j in MEASURES]; 