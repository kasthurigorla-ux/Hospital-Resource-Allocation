def doctor_matches(patient, doctor):
    if int(doctor.get("available", 0)) != 1:
        return False

    patient_cond = str(patient.get("condition", "")).lower()
    doc_spec = str(doctor.get("specialization", "")).lower()

    if doc_spec in patient_cond or patient_cond in doc_spec:
        return True

    return False


def bed_matches(patient, bed):
    if int(bed.get("available", 0)) != 1:
        return False

    req_bed = str(patient.get("required_bed", "")).lower()
    b_type = str(bed.get("bed_type", "")).lower()

    if req_bed in b_type or b_type in req_bed:
        return True

    return False


def room_matches(patient, room):
    if int(room.get("available", 0)) != 1:
        return False

    req_bed = str(patient.get("required_bed", "")).lower()
    r_type = str(room.get("room_type", "")).lower()

    if "icu" in req_bed:
        return "icu" in r_type

    if "icu" in r_type:
        return False

    return True