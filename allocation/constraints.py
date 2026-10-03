def doctor_matches(patient, doctor):
    if int(doctor.get("available", 0)) != 1:
        return False
    p_cond = str(patient.get("condition", "")).lower()
    d_spec = str(doctor.get("specialization", "")).lower()
    
    # Substring matching (General, Cardio, Ortho matches anywhere in the string)
    if d_spec in p_cond or p_cond in d_spec:
        return True
    return False

def bed_matches(patient, bed):
    if int(bed.get("available", 0)) != 1:
        return False
    p_bed = str(patient.get("required_bed", "")).lower()
    b_type = str(bed.get("bed_type", "")).lower()
    
    if b_type in p_bed or p_bed in b_type:
        return True
    return False

def room_matches(patient, room):
    if int(room.get("available", 0)) != 1:
        return False
    p_bed = str(patient.get("required_bed", "")).lower()
    r_type = str(room.get("room_type", "")).lower()
    
    if "icu" in p_bed:
        return "icu" in r_type
    if "icu" in r_type:
        return False
    return True