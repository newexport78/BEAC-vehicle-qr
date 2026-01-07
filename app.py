from flask import Flask, render_template, request, redirect, url_for, session, abort
import sqlite3
import qrcode
import os
from datetime import date, datetime
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
app.secret_key = "beac_secret"

# ✅ REQUIRED FOR RENDER (HTTPS / PROXY)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# ---------------- CONFIG ----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "vehicles.db")
QR_FOLDER = os.path.join(BASE_DIR, "static", "qr")

os.makedirs(QR_FOLDER, exist_ok=True)

# ---------------- DATABASE ----------------
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ---------------- ROUTES ----------------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if not session.get("logged_in"):
        return redirect(url_for("home"))

    msg = None

    if request.method == "POST":
        vehicle_no = request.form["vehicle_no"].strip().upper()
        valid_date = request.form["valid_date"]

        today = date.today().isoformat()

        if valid_date < today:
            msg = "❌ Past dates are not allowed"
        else:
            db = get_db()
            cur = db.cursor()

            # ❌ prevent same vehicle same day
            cur.execute(
                "SELECT * FROM vehicles WHERE vehicle_no=? AND valid_date=?",
                (vehicle_no, valid_date),
            )
            if cur.fetchone():
                msg = "❌ QR already generated for this vehicle today"
            else:
                # ✅ insert
                cur.execute(
                    "INSERT INTO vehicles (vehicle_no, valid_date) VALUES (?, ?)",
                    (vehicle_no, valid_date),
                )
                db.commit()

                # ✅ ABSOLUTE VERIFY URL (IMPORTANT)
                verify_url = url_for(
                    "verify", vehicle_no=vehicle_no, _external=True
                )

                qr_img = qrcode.make(verify_url)
                qr_path = os.path.join(QR_FOLDER, f"{vehicle_no}.png")
                qr_img.save(qr_path)

                return redirect(url_for("dashboard"))

    return render_template("dashboard.html", msg=msg)

@app.route("/verify/<vehicle_no>")
def verify(vehicle_no):
    db = get_db()
    cur = db.cursor()

    cur.execute(
        "SELECT * FROM vehicles WHERE vehicle_no=? ORDER BY id DESC LIMIT 1",
        (vehicle_no.upper(),),
    )
    row = cur.fetchone()

    if not row:
        abort(404)

    valid_date = row["valid_date"]
    today = date.today().isoformat()

    status = "✅ VALID" if today <= valid_date else "❌ EXPIRED"

    return render_template(
        "verify.html",
        vehicle_no=vehicle_no,
        valid_date=valid_date,
        status=status,
        today=today,
    )

# ---------------- LOGIN (SIMPLE) ----------------
@app.route("/login", methods=["POST"])
def login():
    session["logged_in"] = True
    return redirect(url_for("dashboard"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)