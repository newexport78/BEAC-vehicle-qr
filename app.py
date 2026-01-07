from flask import Flask, render_template, request, redirect, url_for, session, abort
import sqlite3
import qrcode
import os
from datetime import date, datetime
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
app.secret_key = "beac-secret-key"

# ✅ Fix Render proxy / HTTPS issues
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "vehicles.db")
QR_FOLDER = os.path.join(BASE_DIR, "static", "qr")

os.makedirs(QR_FOLDER, exist_ok=True)

# ---------------- DB ----------------
def get_db():
    return sqlite3.connect(DB_PATH)

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["username"] == "admin" and request.form["password"] == "admin":
            session["user"] = "admin"
            return redirect(url_for("dashboard"))
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ---------------- HOME ----------------
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        vehicle_no = request.form["vehicle_no"].upper()
        valid_date = request.form["valid_date"]

        today = date.today().isoformat()
        if valid_date < today:
            return "Past date not allowed", 400

        conn = get_db()
        cur = conn.cursor()

        cur.execute("""
            SELECT * FROM vehicles
            WHERE vehicle_no = ? AND valid_date = ?
        """, (vehicle_no, today))

        if cur.fetchone():
            return "QR already generated today", 400

        cur.execute("""
            INSERT INTO vehicles (vehicle_no, valid_date, created_at)
            VALUES (?, ?, ?)
        """, (vehicle_no, valid_date, datetime.now().isoformat()))
        conn.commit()
        conn.close()

        # ✅ Correct public verify URL
        verify_url = url_for(
            "verify",
            vehicle_no=vehicle_no,
            _external=True,
            _scheme="https"
        )

        qr = qrcode.make(verify_url)
        qr_path = os.path.join(QR_FOLDER, f"{vehicle_no}.png")
        qr.save(qr_path)

        return render_template(
            "index.html",
            qr_image=f"/static/qr/{vehicle_no}.png",
            verify_url=verify_url
        )

    return render_template("index.html")

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT vehicle_no, valid_date FROM vehicles ORDER BY id DESC")
    data = cur.fetchall()
    conn.close()

    return render_template("dashboard.html", vehicles=data)

# ---------------- VERIFY (THIS WAS MISSING ❗) ----------------
@app.route("/verify/<vehicle_no>")
def verify(vehicle_no):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT valid_date FROM vehicles
        WHERE vehicle_no = ?
        ORDER BY id DESC LIMIT 1
    """, (vehicle_no,))
    row = cur.fetchone()
    conn.close()

    if not row:
        abort(404)

    valid_date = row[0]
    today = date.today().isoformat()

    status = "VALID" if today <= valid_date else "EXPIRED"

    return render_template(
        "verify.html",
        vehicle_no=vehicle_no,
        valid_date=valid_date,
        status=status
    )

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run()