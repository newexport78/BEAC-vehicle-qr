from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os

app = Flask(__name__)

DB_NAME = "vehicles.db"


# ---------- DATABASE ----------
def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


# ---------- HOME PAGE ----------
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


# ---------- VERIFY VEHICLE ----------
@app.route("/verify", methods=["GET", "POST"])
def verify():
    # Vehicle number can come from:
    # 1. Form POST
    # 2. QR scan / direct URL (?vehicle_no=BP-1-2345)
    vehicle_no = request.form.get("vehicle_no") or request.args.get("vehicle_no")

    if not vehicle_no:
        return redirect(url_for("index"))

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT vehicle_no, expiry_date FROM vehicles WHERE vehicle_no = ?",
        (vehicle_no.upper(),)
    )
    row = cur.fetchone()
    conn.close()

    if not row:
        status = "INVALID"
        expiry = "N/A"
    else:
        expiry = row["expiry_date"]

        # Simple expiry check (YYYY-MM-DD format)
        from datetime import date
        today = date.today().isoformat()

        if expiry >= today:
            status = "VALID"
        else:
            status = "EXPIRED"

    return render_template(
        "verify.html",
        vehicle=vehicle_no.upper(),
        expiry=expiry,
        status=status
    )


# ---------- START APP ----------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)