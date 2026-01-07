from flask import Flask, render_template, request, redirect, session, flash
from werkzeug.middleware.proxy_fix import ProxyFix
import sqlite3
import os
import qrcode
from datetime import datetime, date

# =========================
# APP CONFIG
# =========================
app = Flask(__name__)
app.secret_key = "beac_secret"

# 🔥 REQUIRED FOR RENDER
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

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
        if request.form["username"] == "admin" and request.form["password"] == "admin":
            session["user"] = "admin"
            return redirect("/dashboard")
        flash("Invalid login")
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
    conn.close()

    return render_template("dashboard.html", today=today, today_count=today_count)

# =========================
# GENERATE QR
# =========================
@app.route("/generate", methods=["POST"])
def generate_qr():
    if "user" not in session:
        return redirect("/")

    vehicle = request.form["vehicle"].upper().strip()
    visit_date = request.form["visit_date"]
    today = date.today().isoformat()

    if visit_date < today:
        flash("Past dates not allowed")
        return redirect("/dashboard")

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute(
        "SELECT * FROM vehicles WHERE vehicle=? AND visit_date=?",
        (vehicle, visit_date)
    )
    if c.fetchone():
        flash("QR already exists for today")
        conn.close()
        return redirect("/dashboard")

    # ✅ FULL HTTPS SAFE URL
    qr_url = f"{request.url_root.rstrip('/')}/verify/{vehicle}/{visit_date}"

    img = qrcode.make(qr_url)
    filename = f"{vehicle}_{visit_date}.png"
    img.save(os.path.join(QR_FOLDER, filename))

    c.execute(
        "INSERT INTO vehicles (vehicle, visit_date, created_at) VALUES (?, ?, ?)",
        (vehicle, visit_date, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

    return render_template("qr.html", qr_image=f"qr/{filename}", qr_url=qr_url)

# =========================
# VERIFY QR
# =========================
@app.route("/verify/<vehicle>/<visit_date>")
def verify(vehicle, visit_date):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute(
        "SELECT * FROM vehicles WHERE vehicle=? AND visit_date=?",
        (vehicle.upper(), visit_date)
    )
    row = c.fetchone()
    conn.close()

    if row:
        return render_template(
            "verify.html",
            status="VALID",
            vehicle=vehicle,
            visit_date=visit_date
        )

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
    app.run()