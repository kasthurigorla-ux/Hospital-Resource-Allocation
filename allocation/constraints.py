def doctor_matches(patient, doctor):
    # Available check
    if doctor.get("available") != 1:
        return False

    patient_condition = str(patient.get("condition", "")).strip().lower()
    doctor_spec = str(doctor.get("specialization", "")).strip().lower()

    # Exact match (e.g., cardiology == cardiology)
    if patient_condition == doctor_spec:
        return True

    # Mapping common health conditions to medical specializations
    condition_mapping = {
        "heart attack": "cardiology",
        "chest pain": "cardiology",
        "cardiac": "cardiology",
        "brain": "neurology",
        "stroke": "neurology",
        "nerve": "neurology",
        "fracture": "orthopedics",
        "bone": "orthopedics",
        "child": "pediatrics",
        "fever": "general",
        "cold": "general",
        "cough": "general"
    }

    # Condition map lo unna doctor ki match avvali
    expected_spec = condition_mapping.get(patient_condition)
    if expected_spec and expected_spec == doctor_spec:
        return True

    # General physician can treat general issues
    if doctor_spec == "general" and (patient_condition in ["general", "fever", "checkup"]):
        return True

    return False


def bed_matches(patient, bed):
    if bed.get("available") != 1:
        return False
    
    req_bed = str(patient.get("required_bed", "")).strip().lower()
    bed_type = str(bed.get("bed_type", "")).strip().lower()

    return req_bed == bed_type


def room_matches(patient, room):
    if room.get("available") != 1:
        return False
    
    req_bed = str(patient.get("required_bed", "")).strip().lower()
    room_type = str(room.get("room_type", "")).strip().lower()

    # ICU bed patient must get ICU room
    if req_bed == "icu":
        return room_type == "icu"
    
    return True