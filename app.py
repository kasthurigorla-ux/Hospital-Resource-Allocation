from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os
from datetime import datetime, timedelta
from allocation.csp import find_allocation

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_DIR = os.path.join(BASE_DIR, "database")
os.makedirs(DATABASE_DIR, exist_ok=True)
DATABASE = os.path.join(DATABASE_DIR, "hospital.db")


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # Tables creation
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            specialization TEXT NOT NULL,
            available INTEGER DEFAULT 1
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS beds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bed_number TEXT NOT NULL,
            bed_type TEXT NOT NULL,
            available INTEGER DEFAULT 1
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_number TEXT NOT NULL,
            room_type TEXT NOT NULL,
            available INTEGER DEFAULT 1
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS time_slots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slot_time TEXT NOT NULL,
            available INTEGER DEFAULT 1
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER,
            condition TEXT NOT NULL,
            required_bed TEXT NOT NULL,
            priority TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS allocations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_name TEXT NOT NULL,
            doctor_id INTEGER,
            bed_id INTEGER,
            room_id INTEGER,
            slot_id INTEGER,
            allocated_at TEXT
        )
    """)

    # Seed default data if empty
    doc_count = cursor.execute("SELECT COUNT(*) FROM doctors").fetchone()[0]
    if doc_count == 0:
        cursor.executemany("INSERT INTO doctors (name, specialization, available) VALUES (?, ?, 1)", [
            ("Dr. Anitha", "Cardiology"),
            ("Dr. Rahul", "Neurology"),
            ("Dr. Priya", "General"),
            ("Dr. Kumar", "Orthopedics"),
            ("Dr. Sneha", "Pediatrics"),
            ("Dr. Kasthuri", "ENT")
        ])

        cursor.executemany("INSERT INTO beds (bed_number, bed_type, available) VALUES (?, ?, 1)", [
            ("Bed B-101", "General"),
            ("Bed B-102", "General"),
            ("Bed B-103", "General"),
            ("Bed B-104", "ICU"),
            ("Bed B-105", "ICU"),
            ("Bed B-106", "Private")
        ])

        cursor.executemany("INSERT INTO rooms (room_number, room_type, available) VALUES (?, ?, 1)", [
            ("Room R-201", "General"),
            ("Room R-202", "General"),
            ("Room R-203", "ICU"),
            ("Room R-204", "ICU"),
            ("Room R-205", "Operation"),
            ("Room R-206", "Private")
        ])

        cursor.executemany("INSERT INTO time_slots (slot_time, available) VALUES (?, 1)", [
            ("09:00 AM - 10:00 AM",),
            ("10:00 AM - 11:00 AM",),
            ("11:00 AM - 12:00 PM",),
            ("02:00 PM - 03:00 PM",),
            ("03:00 PM - 04:00 PM",)
        ])

    conn.commit()
    conn.close()


def auto_release_expired_resources():
    """Automatically releases resources allocated more than 2 minutes ago"""
    try:
        conn = get_db()
        # 2 minutes time limit (demo kosam)
        cutoff_time = (datetime.now() - timedelta(minutes=2)).strftime("%Y-%m-%d %H:%M:%S")

        expired_allocations = conn.execute("""
            SELECT * FROM allocations WHERE allocated_at IS NOT NULL AND allocated_at <= ?
        """, (cutoff_time,)).fetchall()

        for alloc in expired_allocations:
            if alloc["doctor_id"]:
                conn.execute("UPDATE doctors SET available = 1 WHERE id = ?", (alloc["doctor_id"],))
            if alloc["bed_id"]:
                conn.execute("UPDATE beds SET available = 1 WHERE id = ?", (alloc["bed_id"],))
            if alloc["room_id"]:
                conn.execute("UPDATE rooms SET available = 1 WHERE id = ?", (alloc["room_id"],))
            if alloc["slot_id"]:
                conn.execute("UPDATE time_slots SET available = 1 WHERE id = ?", (alloc["slot_id"],))
            conn.execute("DELETE FROM allocations WHERE id = ?", (alloc["id"],))

        conn.commit()
        conn.close()
    except Exception as e:
        print("Auto-release check notice:", e)


# Run DB initialization
init_db()


@app.route("/")
def index():
    auto_release_expired_resources()
    return render_template("index.html")


@app.route("/patients", methods=["GET", "POST"])
def patients():
    auto_release_expired_resources()
    if request.method == "POST":
        name = request.form.get("name")
        age = request.form.get("age")
        condition = request.form.get("condition")
        required_bed = request.form.get("required_bed")
        priority = request.form.get("priority")

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO patients (name, age, condition, required_bed, priority)
            VALUES (?, ?, ?, ?, ?)
        """, (name, age, condition, required_bed, priority))
        conn.commit()
        conn.close()

        return redirect(url_for("allocate"))

    return render_template("patients.html")


@app.route("/allocate")
def allocate():
    auto_release_expired_resources()
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
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = get_db()
        conn.execute("UPDATE doctors SET available = 0 WHERE id = ?", (result["doctor"]["id"],))
        conn.execute("UPDATE beds SET available = 0 WHERE id = ?", (result["bed"]["id"],))
        conn.execute("UPDATE rooms SET available = 0 WHERE id = ?", (result["room"]["id"],))
        conn.execute("UPDATE time_slots SET available = 0 WHERE id = ?", (result["slot"]["id"],))
        
        conn.execute("""
            INSERT INTO allocations (patient_name, doctor_id, bed_id, room_id, slot_id, allocated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            patient["name"],
            result["doctor"]["id"],
            result["bed"]["id"],
            result["room"]["id"],
            result["slot"]["id"],
            current_time
        ))
        conn.commit()
        conn.close()

    return render_template("result.html", patient=patient, result=result)


@app.route("/resources")
def resources():
    auto_release_expired_resources()
    conn = get_db()
    doctors = conn.execute("""
        SELECT d.*, a.patient_name FROM doctors d
        LEFT JOIN allocations a ON d.id = a.doctor_id
    """).fetchall()

    beds = conn.execute("""
        SELECT b.*, a.patient_name FROM beds b
        LEFT JOIN allocations a ON b.id = a.bed_id
    """).fetchall()

    rooms = conn.execute("""
        SELECT r.*, a.patient_name FROM rooms r
        LEFT JOIN allocations a ON r.id = a.room_id
    """).fetchall()

    slots = conn.execute("""
        SELECT s.*, a.patient_name FROM time_slots s
        LEFT JOIN allocations a ON s.id = a.slot_id
    """).fetchall()
    conn.close()

    return render_template(
        "resources.html",
        doctors=doctors,
        beds=beds,
        rooms=rooms,
        slots=slots
    )


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


@app.route("/reset")
def reset():
    conn = get_db()
    conn.execute("UPDATE doctors SET available = 1")
    conn.execute("UPDATE beds SET available = 1")
    conn.execute("UPDATE rooms SET available = 1")
    conn.execute("UPDATE time_slots SET available = 1")
    conn.execute("DELETE FROM allocations")
    conn.commit()
    conn.close()
    return redirect(url_for("resources"))


if __name__ == "__main__":
    app.run(debug=True)