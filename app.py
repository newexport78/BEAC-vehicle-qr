from flask import Flask, render_template, request, redirect, url_for
from werkzeug.middleware.proxy_fix import ProxyFix
import sqlite3

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

DB = "vehicles.db"

# ---------- DATABASE ----------
def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

# ---------- HOME PAGE ----------
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        vehicle_no = request.form.get("vehicle_no")
        if vehicle_no:
            return redirect(url_for("verify", vehicle_no=vehicle_no))
    return render_template("index.html")

# ---------- VERIFY PAGE ----------
@app.route("/verify/<vehicle_no>")
def verify(vehicle_no):
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM vehicles WHERE vehicle_no = ?", (vehicle_no,))
    vehicle = cur.fetchone()
    db.close()

    return render_template(
        "verify.html",
        vehicle=vehicle,
        vehicle_no=vehicle_no
    )

# ---------- DASHBOARD ----------
@app.route("/dashboard")
def dashboard():
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM vehicles ORDER BY id DESC")
    vehicles = cur.fetchall()
    db.close()
    return render_template("dashboard.html", vehicles=vehicles)

# ---------- START ----------
if __name__ == "__main__":
    app.run(debug=True)