from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import qrcode
import os
from datetime import datetime
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

DB = "vehicles.db"
QR_FOLDER = "static/qr"

os.makedirs(QR_FOLDER, exist_ok=True)

# ---------------- HOME PAGE ----------------
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        return redirect("/dashboard")
    return render_template("index.html")

# ---------------- DASHBOARD ----------------
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    msg = None

    if request.method == "POST":
        vehicle_no = request.form["vehicle_no"]
        valid_date = request.form["valid_date"]

        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute(
            "INSERT INTO vehicles (vehicle_no, valid_date) VALUES (?, ?)",
            (vehicle_no, valid_date)
        )
        conn.commit()
        conn.close()

        qr_url = f"https://beac-vehicle-qr.onrender.com/verify/{vehicle_no}"
        qr_img = qrcode.make(qr_url)
        qr_path = os.path.join(QR_FOLDER, f"{vehicle_no}.png")
        qr_img.save(qr_path)

        msg = "QR Generated Successfully"

    return render_template("dashboard.html", msg=msg, os=os)

# ---------------- VERIFY QR ----------------
@app.route("/verify/<vehicle_no>", methods=["GET"])
def verify(vehicle_no):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT valid_date FROM vehicles WHERE vehicle_no=?", (vehicle_no,))
    row = c.fetchone()
    conn.close()

    if not row:
        return render_template("verify.html", status="INVALID", vehicle=vehicle_no)

    valid_date = datetime.strptime(row[0], "%Y-%m-%d").date()
    today = datetime.today().date()

    status = "VALID ✅" if valid_date >= today else "EXPIRED ❌"

    return render_template(
        "verify.html",
        vehicle=vehicle_no,
        valid_date=valid_date,
        status=status
    )

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run()