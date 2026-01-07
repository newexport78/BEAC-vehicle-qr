from flask import Flask, render_template, request, redirect, url_for, abort
import sqlite3
import os
from datetime import datetime
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)

# Required for Render / reverse proxy
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "vehicles.db")


# ---------------- DATABASE HELPER ----------------
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ---------------- HOME PAGE ----------------
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


# ---------------- HANDLE FORM SUBMIT ----------------
# This avoids "Method Not Allowed"
@app.route("/verify", methods=["POST"])
def verify_post():
    vehicle_no = request.form.get("vehicle_no", "").strip()

    if not vehicle_no:
        abort(400)

    return redirect(url_for("verify", vehicle_no=vehicle_no))


# ---------------- VERIFY VEHICLE (QR + MANUAL) ----------------
@app.route("/verify/<vehicle_no>", methods=["GET"])
def verify(vehicle_no):
    conn = get_db_connection()
    vehicle = conn.execute(
        "SELECT * FROM vehicles WHERE vehicle_no = ?",
        (vehicle_no,)
    ).fetchone()
    conn.close()

    if vehicle is None:
        return render_template(
            "verify.html",
            vehicle_no=vehicle_no,
            status="NOT FOUND",
            valid=False
        )

    expiry_date = datetime.strptime(vehicle["expiry_date"], "%Y-%m-%d").date()
    today = datetime.today().date()

    is_valid = today <= expiry_date

    return render_template(
        "verify.html",
        vehicle_no=vehicle["vehicle_no"],
        owner=vehicle["owner"],
        expiry_date=vehicle["expiry_date"],
        status="VALID" if is_valid else "EXPIRED",
        valid=is_valid
    )


# ---------------- DASHBOARD (OPTIONAL) ----------------
@app.route("/dashboard", methods=["GET"])
def dashboard():
    conn = get_db_connection()
    vehicles = conn.execute("SELECT * FROM vehicles").fetchall()
    conn.close()

    return render_template("dashboard.html", vehicles=vehicles)


# ---------------- RUN APP ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)