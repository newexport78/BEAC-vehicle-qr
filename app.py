from flask import Flask, render_template, request
import sqlite3
from datetime import datetime

app = Flask(__name__)
DB_NAME = "vehicles.db"

def get_vehicle(vehicle_no):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        "SELECT vehicle_no, expiry_date FROM vehicles WHERE vehicle_no = ?",
        (vehicle_no,)
    )
    row = cur.fetchone()
    conn.close()
    return row

# HOME PAGE
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        return verify()
    return render_template("index.html")

# VERIFY PAGE (GET + POST SAFE)
@app.route("/verify", methods=["GET", "POST"])
def verify():
    vehicle_no = request.values.get("vehicle_no")

    if not vehicle_no:
        return render_template(
            "verify.html",
            vehicle="N/A",
            expiry="N/A",
            status="INVALID"
        )

    record = get_vehicle(vehicle_no)

    if not record:
        return render_template(
            "verify.html",
            vehicle=vehicle_no,
            expiry="N/A",
            status="INVALID"
        )

    expiry_date = datetime.strptime(record[1], "%Y-%m-%d").date()
    today = datetime.today().date()

    status = "VALID" if expiry_date >= today else "EXPIRED"

    return render_template(
        "verify.html",
        vehicle=record[0],
        expiry=record[1],
        status=status
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)