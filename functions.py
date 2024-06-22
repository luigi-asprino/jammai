def reduce_inst(inst_id):
    return inst_id[:inst_id.index("-")] if "-" in inst_id else inst_id

def to_inst_id(instruments, instrument):
    return instruments.index(reduce_inst(instrument)) + 1

def get_domain_from_track_role(df, track_role):
    return list(df[df["track_role"]==track_role].id.unique())

# Create commu_id to num_measures correspondence
def get_num_measures_correspondence(df, track_role):
    return {
        (row["id"], int(row["num_measures"]))
        for index, row in df[df["track_role"] == track_role].iterrows()
    }

def get_num_measures_array(df, ids):
    result = [None] * len(ids)
    for index, commu_id in enumerate(ids):
        result[index] = int(df[df["id"]==commu_id].num_measures)
    return result

def get_instrument_array(df, ids):
    result = [None] * len(ids)
    for index, commu_id in enumerate(ids):
        result[index] = to_inst_id(str(df[df["id"]==commu_id].inst.values[0]))
    return result