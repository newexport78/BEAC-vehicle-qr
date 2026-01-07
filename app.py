from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
import sqlite3
import os
import qrcode
from datetime import datetime, date

# =========================
# APP CONFIG
# =========================
app = Flask(__name__)
app.secret_key = "beac_secret"

DB = "vehicles.db"
QR_FOLDER = "static/qr"

os.makedirs(QR_FOLDER, exist_ok=True)

# =========================
# DATABASE INIT
# =========================
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS vehicles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle TEXT,
            visit_date TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# =========================
# LOGIN
# =========================
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == "admin" and password == "admin":
            session["user"] = username
            return redirect("/dashboard")
        else:
            flash("Invalid credentials")

    return render_template("index.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# =========================
# DASHBOARD
# =========================
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")

    today = date.today().isoformat()

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM vehicles WHERE visit_date = ?", (today,))
    today_count = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM vehicles")
    total_count = c.fetchone()[0]

    conn.close()

    return render_template(
        "dashboard.html",
        today_count=today_count,
        total_count=total_count,
        today=today
    )

# =========================
# GENERATE QR
# =========================
@app.route("/generate", methods=["POST"])
def generate_qr():
    if "user" not in session:
        return redirect("/")

    vehicle = request.form.get("vehicle").strip().upper()
    visit_date = request.form.get("visit_date")

    today = date.today().isoformat()

    # ❌ BLOCK PAST DATE
    if visit_date < today:
        flash("Past dates are not allowed")
        return redirect("/dashboard")

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    # ❌ BLOCK SAME VEHICLE SAME DAY
    c.execute(
        "SELECT * FROM vehicles WHERE vehicle = ? AND visit_date = ?",
        (vehicle, visit_date)
    )
    if c.fetchone():
        conn.close()
        flash("QR already generated for this vehicle today")
        return redirect("/dashboard")

    # =========================
    # ✅ FIX: DYNAMIC BASE URL
    # =========================
    base_url = request.host_url.rstrip("/")
    qr_url = f"{base_url}/verify/{vehicle}/{visit_date}"

    qr_img = qrcode.make(qr_url)
    filename = f"{vehicle}_{visit_date}.png"
    filepath = os.path.join(QR_FOLDER, filename)
    qr_img.save(filepath)

    c.execute(
        "INSERT INTO vehicles (vehicle, visit_date, created_at) VALUES (?, ?, ?)",
        (vehicle, visit_date, datetime.now().isoformat())
    )

    conn.commit()
    conn.close()

    flash("QR generated successfully")
    return render_template(
        "qr.html",
        qr_image=f"qr/{filename}",
        qr_url=qr_url
    )

# =========================
# VERIFY QR
# =========================
@app.route("/verify/<vehicle>/<visit_date>")
def verify(vehicle, visit_date):
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute(
        "SELECT * FROM vehicles WHERE vehicle = ? AND visit_date = ?",
        (vehicle.upper(), visit_date)
    )
    record = c.fetchone()
    conn.close()

    if record:
        return render_template(
            "verify.html",
            status="VALID",
            vehicle=vehicle,
            visit_date=visit_date
        )
    else:
        return render_template(
            "verify.html",
            status="INVALID",
            vehicle=vehicle,
            visit_date=visit_date
        )

# =========================
# RUN
# =========================
if __name__ == "__main__":
    app.run(debug=True)