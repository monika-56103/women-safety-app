from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "monika_secret_key_123"

# ----------------------
# Database Connection
# ----------------------
def get_db():
    conn = sqlite3.connect("users.db")
    conn.row_factory = sqlite3.Row
    return conn

# ----------------------
# Create Tables
# ----------------------
def create_table():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            mobile TEXT UNIQUE NOT NULL,
            contact1 TEXT NOT NULL,
            contact2 TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sos_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            latitude TEXT,
            longitude TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()

# ----------------------
# Home Route
# ----------------------
@app.route("/")
def home():
    return render_template("login.html")

# ----------------------
# Register
# ----------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        mobile = request.form["mobile"]
        contact1 = request.form["contact1"]
        contact2 = request.form["contact2"]

        conn = get_db()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO users (name, mobile, contact1, contact2) VALUES (?, ?, ?, ?)",
                (name, mobile, contact1, contact2)
            )
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return "⚠ Mobile number already registered!"

        conn.close()
        return redirect("/")

    return render_template("register.html")

# ----------------------
# Login Route (FIXED)
# ----------------------
@app.route("/login", methods=["POST"])
def login():
    mobile = request.form["mobile"]

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE mobile=?", (mobile,))
    user = cursor.fetchone()
    conn.close()

    if user:
        session["user_id"] = user["id"]
        session["name"] = user["name"]
        return redirect("/dashboard")
    else:
        return "❌ Mobile number not found!"

# ----------------------
# Dashboard Route (ADDED BACK)
# ----------------------
@app.route("/dashboard")
def dashboard():
    if "user_id" in session:
        return render_template("dashboard.html", name=session["name"])
    else:
        return redirect("/")

# ----------------------
# Save SOS
# ----------------------
@app.route("/save_sos", methods=["POST"])
def save_sos():
    if "user_id" not in session:
        return "Unauthorized", 401

    latitude = request.form["latitude"]
    longitude = request.form["longitude"]
    user_id = session["user_id"]

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO sos_alerts (user_id, latitude, longitude) VALUES (?, ?, ?)",
        (user_id, latitude, longitude)
    )

    conn.commit()
    conn.close()

    return "SOS Saved Successfully"

# ----------------------
# History Route
# ----------------------
@app.route("/history")
def history():
    if "user_id" not in session:
        return redirect("/")

    user_id = session["user_id"]

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM sos_alerts WHERE user_id=? ORDER BY timestamp DESC",
        (user_id,)
    )
    alerts = cursor.fetchall()
    conn.close()

    return render_template("history.html", alerts=alerts)

# ----------------------
# Logout
# ----------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ----------------------
# Run App
# ----------------------
if __name__ == "__main__":
    create_table()
    app.run(debug=True)
