def doctor_matches(patient, doctor):
    if doctor.get("available") != 1:
        return False

    patient_cond = str(patient.get("condition", "")).strip().lower()
    doctor_spec = str(doctor.get("specialization", "")).strip().lower()

    # Direct match or partial word match (e.g. "cardiology" inside "heart / cardiac issue (cardiology)")
    if doctor_spec in patient_cond or patient_cond in doctor_spec:
        return True

    # Common keyword mappings
    keywords = {
        "cardiology": ["heart", "cardiac", "chest"],
        "neurology": ["brain", "neuro", "stroke", "head"],
        "orthopedics": ["bone", "fracture", "joint", "ortho"],
        "pediatrics": ["child", "pediatric", "kid", "baby"],
        "general": ["fever", "cold", "cough", "checkup", "general"]
    }

    words = keywords.get(doctor_spec, [])
    for word in words:
        if word in patient_cond:
            return True

    return False


def bed_matches(patient, bed):
    if bed.get("available") != 1:
        return False
    
    req_bed = str(patient.get("required_bed", "")).strip().lower()
    bed_type = str(bed.get("bed_type", "")).strip().lower()

    return req_bed in bed_type or bed_type in req_bed


def room_matches(patient, room):
    if room.get("available") != 1:
        return False
    
    req_bed = str(patient.get("required_bed", "")).strip().lower()
    room_type = str(room.get("room_type", "")).strip().lower()

    if "icu" in req_bed:
        return "icu" in room_type
    
    return True