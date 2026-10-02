def doctor_matches(patient, doctor):
    if doctor.get("available") != 1:
        return False
    return True


def bed_matches(patient, bed):
    if bed.get("available") != 1:
        return False

    required = str(patient.get("required_bed", "")).strip().lower()
    bed_type = str(bed.get("bed_type", "")).strip().lower()

    if not required or required == "any":
        return True

    if required == "icu":
        return bed_type == "icu"

    if required == "general":
        return bed_type in ["general", "private"]

    return True


def room_matches(patient, room):
    if room.get("available") != 1:
        return False

    required = str(patient.get("required_bed", "")).strip().lower()
    room_type = str(room.get("room_type", "")).strip().lower()

    if required == "icu":
        return room_type == "icu"

    return True