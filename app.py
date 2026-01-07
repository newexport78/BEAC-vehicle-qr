from flask import Flask, render_template, request, redirect, url_for, abort
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.middleware.proxy_fix import ProxyFix
import os

app = Flask(__name__)

# =============================
# Render / HTTPS Fix
# =============================
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# =============================
# Database config
# =============================
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(BASE_DIR, "vehicles.db")

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + db_path
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# =============================
# Database Model
# =============================
class Vehicle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vehicle_no = db.Column(db.String(50), unique=True, nullable=False)
    owner = db.Column(db.String(100))
    validity = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# =============================
# HOME PAGE (THIS WAS MISSING)
# =============================
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        vehicle_no = request.form.get("vehicle_no", "").strip().upper()
        if not vehicle_no:
            return render_template("home.html", error="Enter vehicle number")
        return redirect(url_for("verify", vehicle_no=vehicle_no))

    return render_template("home.html")

# =============================
# VERIFY PAGE (QR + MANUAL)
# =============================
@app.route("/verify/<vehicle_no>")
def verify(vehicle_no):
    vehicle_no = vehicle_no.strip().upper()
    vehicle = Vehicle.query.filter_by(vehicle_no=vehicle_no).first()

    if not vehicle:
        return render_template(
            "verify.html",
            status="INVALID",
            vehicle_no=vehicle_no
        )

    return render_template(
        "verify.html",
        status="VALID",
        vehicle_no=vehicle.vehicle_no,
        owner=vehicle.owner,
        validity=vehicle.validity,
        created_at=vehicle.created_at.strftime("%d-%m-%Y")
    )

# =============================
# SAFETY
# =============================
@app.errorhandler(400)
@app.errorhandler(404)
def bad_request(e):
    return redirect(url_for("home"))

# =============================
# MAIN
# =============================
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)