from flask import Flask, render_template, request
from datetime import datetime
import sqlite3
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

DB_NAME = "vehicles.db"

# ---------------- HOME PAGE ----------------
@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")

# ---------------- VERIFY VEHICLE ----------------
@app.route("/verify", methods=["GET", "POST"])
def verify():
    vehicle_no = request.values.get("vehicle_no")

    if not vehicle_no:
        return "Vehicle number missing", 400

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute(
        "SELECT expiry_date FROM vehicles WHERE vehicle_no = ?",
        (vehicle_no,)
    )
    row = cur.fetchone()
    conn.close()

    if not row:
        status = "INVALID"
        expiry = "N/A"
    else:
        expiry = row[0]
        expiry_date = datetime.strptime(expiry, "%Y-%m-%d").date()
        today = datetime.today().date()

        if expiry_date >= today:
            status = "VALID"
        else:
            status = "EXPIRED"

    return render_template(
        "verify.html",
        vehicle=vehicle_no,
        expiry=expiry,
        status=status
    )

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)