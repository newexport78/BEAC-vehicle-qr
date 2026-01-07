from flask import Flask, render_template, request, redirect, session
import sqlite3
import qrcode
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "beac_secret"

# ======================
# CONFIG
# ======================
DB = "vehicles.db"
QR_FOLDER = "static/qr"
SERVER_IP = "192.168.1.2"   # change if IP changes
PORT = 8000

USERNAME = "admin"
PASSWORD = "1234"

os.makedirs(QR_FOLDER, exist_ok=True)

# ======================
# DATABASE INIT
# ======================
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS vehicles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle TEXT,
            expiry TEXT,
            created TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ======================
# LOGIN
# ======================
@app.route("/", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        if request.form["username"] == USERNAME and request.form["password"] == PASSWORD:
            session.clear()
            session["logged_in"] = True
            return redirect("/dashboard")
        else:
            error = "Invalid username or password"
    return render_template("login.html", error=error)

# ======================
# LOGOUT
# ======================
@app.route("/logout", methods=["GET", "POST"])
def logout():
    session.clear()
    return redirect("/")

# ======================
# DASHBOARD
# ======================
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if not session.get("logged_in"):
        return redirect("/")

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    message = None
    qr_img = None

    today_str = datetime.now().strftime("%Y-%m-%d")
    today_date = datetime.now().date()

    # ----------------------
    # REGISTER VEHICLE (DAILY RULE)
    # ----------------------
    if request.method == "POST":
        vehicle = request.form["vehicle"].lower()
        expiry = request.form["expiry"]

        expiry_date = datetime.strptime(expiry, "%Y-%m-%d").date()

        # ❌ Block past expiry
        if expiry_date < today_date:
            message = "❌ Past expiry dates are not allowed"

        else:
            # ❌ Block same vehicle on same day
            c.execute(
                "SELECT COUNT(*) FROM vehicles WHERE vehicle=? AND created=?",
                (vehicle, today_str)
            )
            already_today = c.fetchone()[0]

            if already_today > 0:
                message = "❌ This vehicle already generated a QR today"
            else:
                c.execute(
                    "INSERT INTO vehicles (vehicle, expiry, created) VALUES (?, ?, ?)",
                    (vehicle, expiry, today_str)
                )
                conn.commit()

                qr_data = f"http://{SERVER_IP}:{PORT}/verify/{vehicle}"
                img = qrcode.make(qr_data)

                img_path = f"{QR_FOLDER}/{vehicle}_{today_str}.png"
                img.save(img_path)

                qr_img = img_path
                message = "✅ QR generated successfully"

    # ----------------------
    # 📊 STATISTICS
    # ----------------------
    total = c.execute("SELECT COUNT(*) FROM vehicles").fetchone()[0]

    today_count = c.execute(
        "SELECT COUNT(*) FROM vehicles WHERE created = ?",
        (today_str,)
    ).fetchone()[0]

    week_count = c.execute(
        "SELECT COUNT(*) FROM vehicles WHERE date(created) >= date('now','-7 day')"
    ).fetchone()[0]

    month_count = c.execute(
        "SELECT COUNT(*) FROM vehicles WHERE date(created) >= date('now','start of month')"
    ).fetchone()[0]

    conn.close()

    return render_template(
        "dashboard.html",
        qr_img=qr_img,
        message=message,
        total=total,
        today_count=today_count,
        week_count=week_count,
        month_count=month_count,
        today=today_str
    )

# ======================
# VERIFY VEHICLE
# ======================
@app.route("/verify/<vehicle>")
def verify(vehicle):
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    # Get latest entry for vehicle
    c.execute(
        "SELECT expiry FROM vehicles WHERE vehicle=? ORDER BY created DESC LIMIT 1",
        (vehicle.lower(),)
    )
    row = c.fetchone()
    conn.close()

    if row:
        expiry_date = datetime.strptime(row[0], "%Y-%m-%d").date()
        today = datetime.now().date()
        status = "VALID" if expiry_date >= today else "EXPIRED"
        expiry = expiry_date
    else:
        status = "INVALID VEHICLE"
        expiry = "Not Found"

    return render_template(
        "verify.html",
        vehicle=vehicle,
        expiry=expiry,
        status=status
    )

# ======================
# RUN SERVER
# ======================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
