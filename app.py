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

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/verify", methods=["POST"])
def verify():
    vehicle_no = request.form.get("vehicle_no")

    if not vehicle_no:
        return "Vehicle number missing", 400

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

    if expiry_date >= today:
        status = "VALID"
    else:
        status = "EXPIRED"

    return render_template(
        "verify.html",
        vehicle=record[0],
        expiry=record[1],
        status=status
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)