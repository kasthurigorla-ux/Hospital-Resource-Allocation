from allocation.constraints import (
    doctor_matches,
    bed_matches,
    room_matches
)


def find_allocation(patient, doctors, beds, rooms, slots):

    # CSP variables
    variables = [
        doctors,
        beds,
        rooms,
        slots
    ]

    # Backtracking search
    def backtrack(index, assignment):

        if index == len(variables):

            return assignment

        for resource in variables[index]:

            # Doctor
            if index == 0:

                if not doctor_matches(patient, resource):
                    continue

                assignment["doctor"] = resource

            # Bed
            elif index == 1:

                if not bed_matches(patient, resource):
                    continue

                assignment["bed"] = resource

            # Room
            elif index == 2:

                if not room_matches(patient, resource):
                    continue

                assignment["room"] = resource

            # Time slot
            elif index == 3:

                assignment["slot"] = resource

            result = backtrack(
                index + 1,
                assignment.copy()
            )

            if result:
                return result

        return None

    return backtrack(0, {})