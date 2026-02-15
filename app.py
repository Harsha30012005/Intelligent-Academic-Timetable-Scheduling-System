from flask import Flask, render_template, request, send_file, redirect
import pandas as pd
import io
from reportlab.platypus import SimpleDocTemplate, Table
from reportlab.lib.pagesizes import A4

from engine import generate_timetable

app = Flask(__name__)

latest_timetable = None
latest_rooms = None
latest_result = {}
SLOTS_PER_DAY = 5   # Keep consistent everywhere


# ----------------------------
# LANDING PAGE
# ----------------------------

@app.route("/")
def home():
    return render_template("landing.html")


# ----------------------------
# DASHBOARD PAGE
# ----------------------------

@app.route("/dashboard")
def dashboard():

    if not latest_result:
        return render_template(
            "dashboard.html",
            timetable=None,
            warnings=None
        )

    return render_template(
        "dashboard.html",
        timetable=latest_result.get("timetable"),
        metrics=latest_result.get("metrics"),
        teacher_summary=latest_result.get("teacher_summary"),
        room_summary=latest_result.get("room_summary"),
        day_summary=latest_result.get("day_summary"),
        coverage=latest_result.get("coverage"),
        warnings=latest_result.get("warnings"),
        slots_per_day=latest_result.get("slots_per_day", 5)
    )



# ----------------------------
# ANALYTICS PAGE
# ----------------------------

@app.route("/analytics")
def analytics():

    if not latest_result:
        return render_template("analytics.html")

    return render_template(
        "analytics.html",
        teacher_summary=latest_result["teacher_summary"],
        room_summary=latest_result["room_summary"],
        day_summary=latest_result["day_summary"]
    )


# ----------------------------
# COVERAGE PAGE
# ----------------------------

@app.route("/coverage")
def coverage_page():

    if not latest_result:
        return render_template("coverage.html")

    return render_template(
        "coverage.html",
        coverage=latest_result["coverage"]
    )


# ----------------------------
# GENERATE TIMETABLE
# ----------------------------

@app.route("/generate", methods=["POST"])
def generate():

    global latest_timetable, latest_rooms, latest_result

    # Load CSV files
    courses_df = pd.read_csv(request.files["courses"])
    rooms_df = pd.read_csv(request.files["rooms"])
    unavailability_df = pd.read_csv(request.files["unavailability"])

    # Format Courses
    courses = []
    for _, row in courses_df.iterrows():
        courses.append({
            "code": row["course"],
            "teacher": row["teacher"],
            "hours": int(row["hours"]),
            "batch": row["batch"],
            "type": row["type"]
        })

    # Format Rooms
    rooms = {}
    for _, row in rooms_df.iterrows():
        rooms[row["room"]] = {
            "type": row["type"]
        }

    # Format Teacher Unavailability
    teacher_unavailability = {}
    for _, row in unavailability_df.iterrows():
        teacher_unavailability.setdefault(row["teacher"], []).append(
            (row["day"], int(row["slot"]))
        )

    data = {
        "courses": courses,
        "rooms": rooms,
        "teacher_unavailability": teacher_unavailability
    }

    # Optimization Weights
    weights = {
        "day_balance": int(request.form["day_balance"]),
        "teacher_balance": int(request.form["teacher_balance"]),
        "room_balance": int(request.form["room_balance"])
    }

    timetable, metrics, teacher_summary, room_summary, day_summary, coverage, warnings = \
        generate_timetable(data, weights, mode="hybrid")

    latest_timetable = timetable
    latest_rooms = rooms

    latest_result = {              # ✅ this now updates global
        "timetable": timetable,
        "metrics": metrics,
        "teacher_summary": teacher_summary,
        "room_summary": room_summary,
        "day_summary": day_summary,
        "coverage": coverage,
        "warnings": warnings,
        "slots_per_day": 5
    }

    return redirect("/dashboard")


# ----------------------------
# EXCEL DOWNLOAD
# ----------------------------

@app.route("/download_excel")
def download_excel():

    if latest_timetable is None:
        return "Generate timetable first."

    data = []

    for day, slots in latest_timetable.items():
        row = {"Day": day}

        for slot in range(1, SLOTS_PER_DAY + 1):
            cell = []
            for room, course in slots[slot].items():
                if course:
                    cell.append(f"{room}: {course['code']}")

            row[f"Slot {slot}"] = " | ".join(cell)

        data.append(row)

    df = pd.DataFrame(data)

    output = io.BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)

    return send_file(
        output,
        download_name="timetable.xlsx",
        as_attachment=True
    )


# ----------------------------
# PDF DOWNLOAD
# ----------------------------

@app.route("/download_pdf")
def download_pdf():

    if latest_timetable is None:
        return "Generate timetable first."

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)

    header = ["Day"] + [f"Slot{i}" for i in range(1, SLOTS_PER_DAY + 1)]
    table_data = [header]

    for day, slots in latest_timetable.items():
        row = [day]

        for slot in range(1, SLOTS_PER_DAY + 1):
            cell = []
            for room, course in slots[slot].items():
                if course:
                    cell.append(f"{room}:{course['code']}")

            row.append("\n".join(cell))

        table_data.append(row)

    table = Table(table_data)
    doc.build([table])
    buffer.seek(0)

    return send_file(
        buffer,
        download_name="timetable.pdf",
        as_attachment=True
    )


if __name__ == "__main__":
    app.run(debug=True)
