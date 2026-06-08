from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, session
import sqlite3
import uuid
from datetime import datetime, date
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'certsys-secret-2026-xK9mP3qL')

DB_PATH = os.environ.get('DB_PATH', 'certificates.db')

# ── ADMIN CREDENTIALS ──
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'CertAdmin2026!')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS certificates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uuid TEXT UNIQUE NOT NULL,
            deliverable_id TEXT NOT NULL,
            id_barcode TEXT NOT NULL,
            company_name TEXT NOT NULL,
            person_name TEXT NOT NULL,
            certificate_type TEXT NOT NULL,
            model TEXT NOT NULL,
            issued_on TEXT NOT NULL,
            valid_until TEXT NOT NULL,
            training_location TEXT NOT NULL,
            trainer TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Migrate existing DB: add new columns if missing
    existing = [row[1] for row in conn.execute("PRAGMA table_info(certificates)").fetchall()]
    for col, default in [
        ('deliverable_id', "''"),
        ('id_barcode', "''"),
        ('model', "'N/A'"),
    ]:
        if col not in existing:
            conn.execute(f"ALTER TABLE certificates ADD COLUMN {col} TEXT NOT NULL DEFAULT {default}")
    conn.commit()
    conn.close()

def get_status(issued_on_str, valid_until_str):
    try:
        valid_until = datetime.strptime(valid_until_str, "%Y-%m-%d").date()
        return "EXPIRED" if date.today() > valid_until else "VALID"
    except:
        return "VALID"

def fmt_date(d):
    try:
        return datetime.strptime(d, "%Y-%m-%d").strftime("%d/%m/%Y")
    except:
        return d

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# ── AUTH ROUTES ─────────────────────────────────────

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('admin_form'))
        flash("Wrong username or password.", "error")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('login'))

# ── ADMIN ROUTES (protected) ─────────────────────────

@app.route("/")
@login_required
def index():
    return redirect(url_for('admin_form'))

@app.route("/admin", methods=["GET"])
@login_required
def admin_form():
    return render_template("form.html")

@app.route("/submit", methods=["POST"])
@login_required
def submit():
    deliverable_id    = request.form.get("deliverable_id", "").strip()
    id_barcode        = request.form.get("id_barcode", "").strip()
    company_name      = request.form.get("company_name", "").strip()
    person_name       = request.form.get("person_name", "").strip()
    certificate_type  = request.form.get("certificate_type", "").strip()
    model             = request.form.get("model", "").strip()
    issued_on         = request.form.get("issued_on", "").strip()
    valid_until       = request.form.get("valid_until", "").strip()
    training_location = request.form.get("training_location", "").strip()
    trainer           = request.form.get("trainer", "").strip()

    if not all([deliverable_id, id_barcode, company_name, person_name,
                certificate_type, issued_on, valid_until, training_location, trainer]):
        flash("All fields are required — no field may be left empty.", "error")
        return redirect(url_for('admin_form'))

    cert_uuid = str(uuid.uuid4())
    conn = get_db()
    conn.execute("""
        INSERT INTO certificates
          (uuid, deliverable_id, id_barcode, company_name, person_name,
           certificate_type, model, issued_on, valid_until, training_location, trainer)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (cert_uuid, deliverable_id, id_barcode, company_name, person_name,
          certificate_type, model, issued_on, valid_until, training_location, trainer))
    conn.commit()
    conn.close()
    return redirect(url_for('view_certificate', cert_uuid=cert_uuid))

@app.route("/dashboard")
@login_required
def dashboard():
    conn = get_db()
    certs = conn.execute("SELECT * FROM certificates ORDER BY created_at DESC").fetchall()
    conn.close()
    rows = []
    for c in certs:
        status = get_status(c["issued_on"], c["valid_until"])
        rows.append({**dict(c), "status": status})
    return render_template("dashboard.html", certs=rows)

@app.route("/dashboard/delete/<cert_uuid>", methods=["POST"])
@login_required
def delete_certificate(cert_uuid):
    conn = get_db()
    conn.execute("DELETE FROM certificates WHERE uuid = ?", (cert_uuid,))
    conn.commit()
    conn.close()
    flash("Certificate deleted.", "success")
    return redirect(url_for('dashboard'))

# ── PUBLIC ROUTES (no login needed) ─────────────────

@app.route("/certificate/<cert_uuid>")
def view_certificate(cert_uuid):
    conn = get_db()
    cert = conn.execute("SELECT * FROM certificates WHERE uuid = ?", (cert_uuid,)).fetchone()
    conn.close()
    if not cert:
        return render_template("certificate.html", cert=None, status="NOT FOUND")
    status = get_status(cert["issued_on"], cert["valid_until"])
    cert_data = {
        "uuid":              cert["uuid"],
        "deliverable_id":    cert["deliverable_id"],
        "id_barcode":        cert["id_barcode"],
        "company_name":      cert["company_name"],
        "person_name":       cert["person_name"],
        "certificate_type":  cert["certificate_type"],
        "model":             cert["model"],
        "issued_on":         fmt_date(cert["issued_on"]),
        "valid_until":       fmt_date(cert["valid_until"]),
        "training_location": cert["training_location"],
        "trainer":           cert["trainer"],
        "created_at":        cert["created_at"],
    }
    return render_template("certificate.html", cert=cert_data, status=status)

@app.route("/api/verify/<cert_uuid>")
def api_verify(cert_uuid):
    conn = get_db()
    cert = conn.execute("SELECT * FROM certificates WHERE uuid = ?", (cert_uuid,)).fetchone()
    conn.close()
    if not cert:
        return jsonify({"status": "NOT FOUND"}), 404
    status = get_status(cert["issued_on"], cert["valid_until"])
    return jsonify({
        "status": status,
        "deliverable_id": cert["deliverable_id"],
        "id_barcode": cert["id_barcode"],
        "name": cert["person_name"],
        "company": cert["company_name"],
        "type": cert["certificate_type"],
        "model": cert["model"],
        "issued_on": cert["issued_on"],
        "valid_until": cert["valid_until"],
        "trainer": cert["trainer"],
        "location": cert["training_location"],
    })

if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
