from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os

from allocation.csp import find_allocation

app = Flask(__name__)

# ---------------- DATABASE PATH ----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_DIR = os.path.join(BASE_DIR, "database")
os.makedirs(DATABASE_DIR, exist_ok=True)
DATABASE = os.path.join(DATABASE_DIR, "hospital.db")


# ---------------- DATABASE CONNECTION ----------------
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# ---------------- DATABASE INITIALIZATION ----------------
def initialize_database():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER,
            condition TEXT,
            priority TEXT,
            required_bed TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            specialization TEXT,
            available INTEGER
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS beds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bed_number TEXT,
            bed_type TEXT,
            available INTEGER
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_number TEXT,
            room_type TEXT,
            available INTEGER
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS time_slots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slot TEXT,
            available INTEGER
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS allocations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_name TEXT,
            doctor_id INTEGER,
            bed_id INTEGER,
            room_id INTEGER,
            slot_id INTEGER
        )
    """)

    cursor.execute("SELECT COUNT(*) FROM doctors")
    if cursor.fetchone()[0] == 0:
        doctors = [
            ("Dr. Anitha", "Cardiology", 1),
            ("Dr. Rahul", "Neurology", 1),
            ("Dr. Priya", "General", 1),
            ("Dr. Kumar", "Orthopedics", 1),
            ("Dr. Sneha", "Pediatrics", 1)
        ]
        cursor.executemany("INSERT INTO doctors (name, specialization, available) VALUES (?, ?, ?)", doctors)

    cursor.execute("SELECT COUNT(*) FROM beds")
    if cursor.fetchone()[0] == 0:
        beds = [
            ("B-101", "General", 1),
            ("B-102", "General", 1),
            ("B-103", "General", 1),
            ("B-104", "ICU", 1),
            ("B-105", "ICU", 1),
            ("B-106", "Private", 1),
            ("B-107", "Private", 1)
        ]
        cursor.executemany("INSERT INTO beds (bed_number, bed_type, available) VALUES (?, ?, ?)", beds)

    cursor.execute("SELECT COUNT(*) FROM rooms")
    if cursor.fetchone()[0] == 0:
        rooms = [
            ("R-201", "General", 1),
            ("R-202", "General", 1),
            ("R-203", "ICU", 1),
            ("R-204", "ICU", 1),
            ("R-205", "Operation", 1),
            ("R-206", "Private", 1)
        ]
        cursor.executemany("INSERT INTO rooms (room_number, room_type, available) VALUES (?, ?, ?)", rooms)

    cursor.execute("SELECT COUNT(*) FROM time_slots")
    if cursor.fetchone()[0] == 0:
        slots = [
            ("09:00 AM - 10:00 AM", 1),
            ("10:00 AM - 11:00 AM", 1),
            ("11:00 AM - 12:00 PM", 1),
            ("02:00 PM - 03:00 PM", 1),
            ("03:00 PM - 04:00 PM", 1)
        ]
        cursor.executemany("INSERT INTO time_slots (slot, available) VALUES (?, ?)", slots)

    conn.commit()
    conn.close()


# ---------------- ROUTES ----------------
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/patients", methods=["GET", "POST"])
def patients():
    conn = get_db()

    if request.method == "POST":
        name = request.form["name"]
        age = request.form["age"]
        condition = request.form["condition"]
        priority = request.form["priority"]
        required_bed = request.form["required_bed"]

        conn.execute("""
            INSERT INTO patients (name, age, condition, priority, required_bed)
            VALUES (?, ?, ?, ?, ?)
        """, (name, age, condition, priority, required_bed))
        conn.commit()
        conn.close()

        return redirect(url_for("allocate"))

    available_doctors = conn.execute("""
        SELECT name, specialization FROM doctors WHERE available = 1
    """).fetchall()
    conn.close()

    return render_template("patients.html", available_doctors=available_doctors)


@app.route("/allocate")
def allocate():
    conn = get_db()
    patient = conn.execute("SELECT * FROM patients ORDER BY id DESC LIMIT 1").fetchone()
    doctors = conn.execute("SELECT * FROM doctors WHERE available = 1").fetchall()
    beds = conn.execute("SELECT * FROM beds WHERE available = 1").fetchall()
    rooms = conn.execute("SELECT * FROM rooms WHERE available = 1").fetchall()
    slots = conn.execute("SELECT * FROM time_slots WHERE available = 1").fetchall()
    conn.close()

    if not patient:
        return redirect(url_for("patients"))

    result = find_allocation(
        dict(patient),
        [dict(d) for d in doctors],
        [dict(b) for b in beds],
        [dict(r) for r in rooms],
        [dict(s) for s in slots]
    )

    if result:
        conn = get_db()
        conn.execute("UPDATE doctors SET available = 0 WHERE id = ?", (result["doctor"]["id"],))
        conn.execute("UPDATE beds SET available = 0 WHERE id = ?", (result["bed"]["id"],))
        conn.execute("UPDATE rooms SET available = 0 WHERE id = ?", (result["room"]["id"],))
        conn.execute("UPDATE time_slots SET available = 0 WHERE id = ?", (result["slot"]["id"],))

        conn.execute("""
            INSERT INTO allocations (patient_name, doctor_id, bed_id, room_id, slot_id)
            VALUES (?, ?, ?, ?, ?)
        """, (patient["name"], result["doctor"]["id"], result["bed"]["id"], result["room"]["id"], result["slot"]["id"]))

        conn.commit()
        conn.close()

    return render_template("result.html", patient=patient, result=result)


@app.route("/resources")
def resources():
    conn = get_db()
    doctors = conn.execute("""
        SELECT d.*, a.patient_name 
        FROM doctors d
        LEFT JOIN allocations a ON d.id = a.doctor_id
    """).fetchall()

    beds = conn.execute("""
        SELECT b.*, a.patient_name 
        FROM beds b
        LEFT JOIN allocations a ON b.id = a.bed_id
    """).fetchall()

    rooms = conn.execute("""
        SELECT r.*, a.patient_name 
        FROM rooms r
        LEFT JOIN allocations a ON r.id = a.room_id
    """).fetchall()

    slots = conn.execute("""
        SELECT s.*, a.patient_name 
        FROM time_slots s
        LEFT JOIN allocations a ON s.id = a.slot_id
    """).fetchall()

    conn.close()

    return render_template("resources.html", doctors=doctors, beds=beds, rooms=rooms, slots=slots)


# ---------------- DYNAMIC ADMIN MANAGEMENT ROUTES ----------------

# 1. Dynamic ga Kottha Resource ni Add Cheyadam (Doctor / Bed / Room / Slot)
@app.route("/admin/add", methods=["POST"])
def add_resource():
    res_type = request.form.get("resource_type")
    conn = get_db()

    if res_type == "doctor":
        name = request.form.get("name")
        specialization = request.form.get("specialization")
        conn.execute("INSERT INTO doctors (name, specialization, available) VALUES (?, ?, 1)", (name, specialization))

    elif res_type == "bed":
        bed_number = request.form.get("bed_number")
        bed_type = request.form.get("bed_type")
        conn.execute("INSERT INTO beds (bed_number, bed_type, available) VALUES (?, ?, 1)", (bed_number, bed_type))

    elif res_type == "room":
        room_number = request.form.get("room_number")
        room_type = request.form.get("room_type")
        conn.execute("INSERT INTO rooms (room_number, room_type, available) VALUES (?, ?, 1)", (room_number, room_type))

    elif res_type == "slot":
        slot = request.form.get("slot")
        conn.execute("INSERT INTO time_slots (slot, available) VALUES (?, 1)", (slot,))

    conn.commit()
    conn.close()
    return redirect(url_for("resources"))


# 2. Dynamic ga Patient ni Discharge / Resource ni Release Cheyadam
@app.route("/release/<res_type>/<int:res_id>")
def release_resource(res_type, res_id):
    conn = get_db()

    if res_type == "doctor":
        conn.execute("UPDATE doctors SET available = 1 WHERE id = ?", (res_id,))
        conn.execute("DELETE FROM allocations WHERE doctor_id = ?", (res_id,))
    elif res_type == "bed":
        conn.execute("UPDATE beds SET available = 1 WHERE id = ?", (res_id,))
        conn.execute("DELETE FROM allocations WHERE bed_id = ?", (res_id,))
    elif res_type == "room":
        conn.execute("UPDATE rooms SET available = 1 WHERE id = ?", (res_id,))
        conn.execute("DELETE FROM allocations WHERE room_id = ?", (res_id,))
    elif res_type == "slot":
        conn.execute("UPDATE time_slots SET available = 1 WHERE id = ?", (res_id,))
        conn.execute("DELETE FROM allocations WHERE slot_id = ?", (res_id,))

    conn.commit()
    conn.close()
    return redirect(url_for("resources"))


# 3. Master Reset
@app.route("/reset")
def reset_resources():
    conn = get_db()
    conn.execute("UPDATE doctors SET available = 1")
    conn.execute("UPDATE beds SET available = 1")
    conn.execute("UPDATE rooms SET available = 1")
    conn.execute("UPDATE time_slots SET available = 1")
    conn.execute("DELETE FROM allocations")
    conn.execute("DELETE FROM patients")
    conn.commit()
    conn.close()
    return redirect(url_for("resources"))


if __name__ == "__main__":
    initialize_database()
    app.run(debug=True)