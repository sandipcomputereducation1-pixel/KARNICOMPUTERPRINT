import os
import socket
import sqlite3
import uuid
import secrets
import subprocess
from pathlib import Path
from datetime import datetime
from functools import wraps

import qrcode
from flask import (
    Flask, request, redirect, url_for, render_template,
    send_from_directory, flash, abort, session
)
from werkzeug.utils import secure_filename

BASE = Path(__file__).resolve().parent
UPLOADS = BASE / "uploads"
TEMPLATES = BASE / "templates"
DB_PATH = BASE / "orders.db"
UPLOADS.mkdir(exist_ok=True)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-before-public-use")
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024  # 25 MB per upload

SHOP_NAME = "Shree Karni Computer"
SHOP_ADDRESS = "Bhagat Singh Choraha, Dalot, Pratapgarh, Rajasthan"
SHOP_PHONE = "7891411425 / 7339871128"
UPI_ID = "7891411425@ptyes"
ADMIN_PIN = os.environ.get("ADMIN_PIN", "1234")  # change this before use

ALLOWED_EXTENSIONS = {"pdf", "jpg", "jpeg", "png"}
PRINT_TYPES = {
    "A4 Black & White": 5,
    "A4 Colour": 15,
    "Photo 4x6": 20,
    "PVC Card": 50,
    "Other": 0,
}

def db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    with db() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_code TEXT UNIQUE NOT NULL,
                customer_name TEXT NOT NULL,
                mobile TEXT NOT NULL,
                print_type TEXT NOT NULL,
                copies INTEGER NOT NULL,
                payment_mode TEXT NOT NULL,
                amount REAL NOT NULL,
                payment_status TEXT NOT NULL DEFAULT 'Pending',
                order_status TEXT NOT NULL DEFAULT 'New',
                filename TEXT NOT NULL,
                original_filename TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except OSError:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("admin_login"))
        return fn(*args, **kwargs)
    return wrapper

@app.route("/")
def home():
    # Put your complete existing HTML file at templates/index.html.
    index = TEMPLATES / "index.html"
    if index.exists() and index.stat().st_size > 100:
        return render_template("index.html")
    return render_template("setup_home.html", shop=SHOP_NAME, address=SHOP_ADDRESS, phone=SHOP_PHONE)

@app.route("/order", methods=["GET", "POST"])
def customer_order():
    if request.method == "POST":
        name = request.form.get("customer_name", "").strip()
        mobile = request.form.get("mobile", "").strip()
        print_type = request.form.get("print_type", "")
        copies = request.form.get("copies", "1")
        payment_mode = request.form.get("payment_mode", "")
        file = request.files.get("document")

        if not name or not mobile or len(mobile) < 10:
            flash("कृपया नाम और सही मोबाइल नंबर भरें।", "error")
            return redirect(url_for("customer_order"))
        if print_type not in PRINT_TYPES:
            flash("कृपया सही प्रिंट प्रकार चुनें।", "error")
            return redirect(url_for("customer_order"))
        try:
            copies = max(1, min(100, int(copies)))
        except ValueError:
            copies = 1
        if payment_mode not in {"UPI", "Cash"}:
            flash("UPI या Cash में से भुगतान तरीका चुनें।", "error")
            return redirect(url_for("customer_order"))
        if not file or not file.filename or not allowed_file(file.filename):
            flash("केवल PDF, JPG, JPEG या PNG फाइल अपलोड करें।", "error")
            return redirect(url_for("customer_order"))

        original = secure_filename(file.filename)
        ext = original.rsplit(".", 1)[1].lower()
        stored = f"{uuid.uuid4().hex}.{ext}"
        file.save(UPLOADS / stored)
        amount = PRINT_TYPES[print_type] * copies
        code = "SK" + datetime.now().strftime("%y%m%d") + secrets.token_hex(2).upper()

        with db() as con:
            con.execute("""
                INSERT INTO orders
                (order_code, customer_name, mobile, print_type, copies,
                 payment_mode, amount, filename, original_filename, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (code, name, mobile, print_type, copies, payment_mode,
                  amount, stored, original, datetime.now().strftime("%d-%m-%Y %I:%M %p")))

        return render_template("order_success.html", code=code, amount=amount,
                               payment_mode=payment_mode, upi=UPI_ID, shop=SHOP_NAME)
    return render_template("customer_order.html", shop=SHOP_NAME, address=SHOP_ADDRESS,
                           phone=SHOP_PHONE, print_types=PRINT_TYPES, upi=UPI_ID)

@app.route("/qr")
def qr_page():
    url = f"http://{local_ip()}:5000/order"
    img = qrcode.make(url)
    path = BASE / "static" / "customer_order_qr.png"
    img.save(path)
    return render_template("qr.html", url=url)

@app.route("/qr-image")
def qr_image():
    return send_from_directory(BASE / "static", "customer_order_qr.png")

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if request.form.get("pin") == ADMIN_PIN:
            session["admin"] = True
            return redirect(url_for("admin_dashboard"))
        flash("गलत Admin PIN।", "error")
    return render_template("admin_login.html")

@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))

@app.route("/admin")
@admin_required
def admin_dashboard():
    with db() as con:
        orders = con.execute("SELECT * FROM orders ORDER BY id DESC").fetchall()
    return render_template("admin.html", orders=orders, shop=SHOP_NAME)

@app.route("/admin/file/<int:order_id>")
@admin_required
def admin_file(order_id):
    with db() as con:
        order = con.execute("SELECT filename, original_filename FROM orders WHERE id=?", (order_id,)).fetchone()
    if not order:
        abort(404)
    return send_from_directory(UPLOADS, order["filename"], as_attachment=True,
                               download_name=order["original_filename"])

@app.route("/admin/status/<int:order_id>", methods=["POST"])
@admin_required
def update_status(order_id):
    status = request.form.get("status", "New")
    if status not in {"New", "Accepted", "Printing", "Completed", "Cancelled"}:
        abort(400)
    with db() as con:
        con.execute("UPDATE orders SET order_status=? WHERE id=?", (status, order_id))
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/payment/<int:order_id>", methods=["POST"])
@admin_required
def update_payment(order_id):
    status = request.form.get("payment_status", "Pending")
    if status not in {"Pending", "Paid"}:
        abort(400)
    with db() as con:
        con.execute("UPDATE orders SET payment_status=? WHERE id=?", (status, order_id))
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/print/<int:order_id>", methods=["POST"])
@admin_required
def print_order(order_id):
    # Windows: sends the downloaded file to its registered default application.
    with db() as con:
        order = con.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
    if not order:
        abort(404)
    path = str(UPLOADS / order["filename"])
    if os.name != "nt":
        flash("ऑटो प्रिंट सुविधा Windows PC पर ही चलेगी।", "error")
        return redirect(url_for("admin_dashboard"))
    try:
        os.startfile(path, "print")
        with db() as con:
            con.execute("UPDATE orders SET order_status='Printing' WHERE id=?", (order_id,))
        flash("फाइल Windows के Default Print App को भेज दी गई। प्रिंटर डायलॉग में सेटिंग जाँचें।", "success")
    except Exception as exc:
        flash(f"Print शुरू नहीं हुआ: {exc}", "error")
    return redirect(url_for("admin_dashboard"))

@app.errorhandler(413)
def too_large(_):
    return "फाइल 25 MB से बड़ी है। कृपया छोटी फाइल अपलोड करें।", 413

if __name__ == "__main__":
    init_db()
    print("\\nShree Karni Computer Print by QR")
    print(f"Computer URL: http://127.0.0.1:5000")
    print(f"Mobile URL (same hotspot): http://{local_ip()}:5000/order")
    print("QR page: http://127.0.0.1:5000/qr")
    print("Admin: http://127.0.0.1:5000/admin  | Default PIN: 1234 (change it)")
    app.run(host="0.0.0.0", port=5000, debug=False)
