from flask import Flask, request, jsonify, render_template
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import csv
import urllib.parse as urlparse

app = Flask(__name__)

# -----------------------------
# DATABASE CONNECTION
# -----------------------------
# Get Render DATABASE_URL from environment
DATABASE_URL = os.environ.get("DATABASE_URL")

def get_conn():
    url=urlparse.urlparse(DATABASE_URL)
    return psycopg2.connect(
        dbname=url.path[1:],
        user=url.username,
        password=url.password,
        host=url.hostname,
        port=url.port,
        sslmode="require",
        cursor_factory=RealDictCursor
        )

# -----------------------------
# INITIALIZE DATABASE
# -----------------------------
def init_db():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS guests (
            unique_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            checked_in BOOLEAN DEFAULT FALSE
        )
    """)
    conn.commit()
    conn.close()

init_db()

# -----------------------------
# IMPORT CSV TO DATABASE
# -----------------------------
CSV_FILE = "guests_with_ids.csv"

def import_csv_to_db():
    conn = get_conn()
    cursor = conn.cursor()
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                cursor.execute("""
                    INSERT INTO guests (unique_id, name, checked_in)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (unique_id) DO NOTHING
                """, (row["unique_id"], row["name"], row.get("checked_in")=="YES"))
        conn.commit()
    conn.close()

import_csv_to_db()

# -----------------------------
# SCANNER PAGE
# -----------------------------
@app.route('/')
def scanner_page():
    return render_template('scanner.html')


# -----------------------------
# CHECK-IN ROUTE
# -----------------------------
@app.route('/checkin', methods=['POST'])
def checkin():
    data = request.get_json()
    if not data or "id" not in data:
        return jsonify({"status": "error", "message": "No ID provided"}), 400

    scanned_id = data["id"]

    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT name, checked_in FROM guests WHERE unique_id = %s", (scanned_id,))
    guest = cursor.fetchone()

    if not guest:
        conn.close()
        return jsonify({"status": "error", "message": "Guest not found"})

    if guest["checked_in"]:
        conn.close()
        return jsonify({"status": "already", "name": guest["name"]})

    cursor.execute("UPDATE guests SET checked_in = TRUE WHERE unique_id = %s", (scanned_id,))
    conn.commit()
    conn.close()

    return jsonify({"status": "success", "name": guest["name"]})


# -----------------------------
# GET ALL GUESTS
# -----------------------------
@app.route('/guests', methods=['GET'])
def get_guests():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT unique_id, name, checked_in FROM guests ORDER BY name")
    rows = cursor.fetchall()
    conn.close()

    return jsonify([
        {"id": row["unique_id"], "name": row["name"], "checked_in": row["checked_in"]}
        for row in rows
    ])


# -----------------------------
# RUN APP
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)