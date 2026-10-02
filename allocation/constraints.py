def doctor_matches(patient, doctor):
    # Doctor free ga undali
    if int(doctor.get("available", 0)) != 1:
        return False

    patient_cond = str(patient.get("condition", "")).lower()
    doctor_spec = str(doctor.get("specialization", "")).lower()

    # Exact match or substring match
    if doctor_spec in patient_cond or patient_cond in doctor_spec:
        return True

    # Keyword mappings
    mappings = {
        "cardiology": ["heart", "cardiac", "chest", "bp", "cardio"],
        "neurology": ["brain", "neuro", "stroke", "paralysis", "head"],
        "orthopedics": ["bone", "fracture", "joint", "ortho", "leg", "hand"],
        "pediatrics": ["child", "pediatric", "kid", "baby", "infant"],
        "general": ["fever", "cold", "cough", "checkup", "general", "pain"]
    }

    # Match doctor spec keywords inside patient condition
    spec_keywords = mappings.get(doctor_spec, [])
    for kw in spec_keywords:
        if kw in patient_cond:
            return True

    # If general physician, accept general conditions
    if doctor_spec == "general":
        return True

    return False


def bed_matches(patient, bed):
    # Bed free ga undali
    if int(bed.get("available", 0)) != 1:
        return False
    
    req_bed = str(patient.get("required_bed", "")).strip().lower()
    bed_type = str(bed.get("bed_type", "")).strip().lower()

    if req_bed == bed_type or req_bed in bed_type or bed_type in req_bed:
        return True

    return False


def room_matches(patient, room):
    # Room free ga undali
    if int(room.get("available", 0)) != 1:
        return False
    
    req_bed = str(patient.get("required_bed", "")).strip().lower()
    room_type = str(room.get("room_type", "")).strip().lower()

    if "icu" in req_bed:
        return "icu" in room_type

    # Non-ICU patients can use general or private rooms
    if "icu" in room_type:
        return False

    return True