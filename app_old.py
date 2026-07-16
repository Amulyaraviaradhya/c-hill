from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    jsonify,
    send_file
)

import os
import pandas as pd
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

# =====================================
# LOAD ENVIRONMENT VARIABLES
# =====================================

load_dotenv()

print("Current Folder:", os.getcwd())
print("DATABASE_URL =", os.getenv("DATABASE_URL"))

app = Flask(__name__)
app.secret_key = "visitor_secret_key"

# =====================================
# LOGIN CREDENTIALS
# =====================================

USERNAME = "admin"
PASSWORD = "admin123"

# =====================================
# DATABASE URL
# =====================================

DATABASE_URL = os.getenv("DATABASE_URL")

# If running locally and DATABASE_URL isn't set,
# you can temporarily paste your PostgreSQL URL below.
#
# Example:
#
# DATABASE_URL = "postgresql://user:password@host/database"
#
# Uncomment the next line and paste your URL only if
# you want to test locally.

# DATABASE_URL = "PASTE_YOUR_DATABASE_URL_HERE"

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL not found.\n"
        "Create a .env file locally or configure "
        "DATABASE_URL in Render."
    )

# Render sometimes uses postgres://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgres://",
        "postgresql://",
        1
    )

# =====================================
# DATABASE CONNECTION
# =====================================

def get_connection():

    return psycopg.connect(
        DATABASE_URL,
        row_factory=dict_row
    )

# =====================================
# CREATE TABLE
# =====================================

def create_table():

    print("Connecting to PostgreSQL...")

    with get_connection() as conn:

        print("Connected successfully!")

        with conn.cursor() as cur:

            print("Creating table...")

            cur.execute("""
                CREATE TABLE IF NOT EXISTS visitors(
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100),
                    reference_person VARCHAR(100),
                    number_of_people INTEGER,
                    vehicle_number VARCHAR(50),
                    entry_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

        conn.commit()

    print("Table checked successfully.")

# =====================================
# LOGIN
# =====================================

@app.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        if username == USERNAME and password == PASSWORD:

            session["user"] = username

            return redirect(url_for("form"))

        return render_template(
            "login.html",
            error="Invalid Username or Password"
        )

    return render_template("login.html")
	
# =====================================
# VISITOR ENTRY FORM
# =====================================

@app.route("/form", methods=["GET", "POST"])
def form():

    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        reference = request.form.get("reference", "").strip()
        people = request.form.get("people", "").strip()
        vehicle = request.form.get("vehicle", "").strip().upper()

        try:

            with get_connection() as conn:

                with conn.cursor() as cur:

                    cur.execute("""

                        INSERT INTO visitors
                        (
                            name,
                            reference_person,
                            number_of_people,
                            vehicle_number
                        )

                        VALUES
                        (%s, %s, %s, %s)

                    """,
                    (
                        name,
                        reference,
                        int(people),
                        vehicle
                    ))

                conn.commit()

            return redirect(url_for("dashboard"))

        except Exception as e:

            return f"Database Error:<br><br>{e}"

    return render_template("form.html")


# =====================================
# ADMIN DASHBOARD
# =====================================

@app.route("/dashboard")
def dashboard():

    if "user" not in session:
        return redirect(url_for("login"))

    try:

        with get_connection() as conn:

            with conn.cursor() as cur:

                cur.execute("""

                    SELECT

                        id,
                        name,
                        reference_person,
                        number_of_people,
                        vehicle_number,
                        entry_time

                    FROM visitors

                    ORDER BY id DESC

                """)

                rows = cur.fetchall()

        data = []

        for row in rows:

            data.append({

                "ID": row["id"],

                "Name": row["name"],

                "Reference Person": row["reference_person"],

                "Number of People": row["number_of_people"],

                "Vehicle Number": row["vehicle_number"],

                "Entry Time": row["entry_time"].strftime("%d-%m-%Y %H:%M:%S")

            })

        return render_template(
            "dashboard.html",
            data=data
        )

    except Exception as e:

        return f"Database Error:<br><br>{e}"


# =====================================
# PUBLIC VIEWER
# =====================================

@app.route("/view")
def view():

    try:

        with get_connection() as conn:

            with conn.cursor() as cur:

                cur.execute("""

                    SELECT

                        id,
                        name,
                        reference_person,
                        number_of_people,
                        vehicle_number,
                        entry_time

                    FROM visitors

                    ORDER BY id DESC

                """)

                rows = cur.fetchall()

        data = []

        for row in rows:

            data.append({

                "ID": row["id"],

                "Name": row["name"],

                "Reference Person": row["reference_person"],

                "Number of People": row["number_of_people"],

                "Vehicle Number": row["vehicle_number"],

                "Entry Time": row["entry_time"].strftime("%d-%m-%Y %H:%M:%S")

            })

        return render_template(
            "viewer.html",
            data=data
        )

    except Exception as e:

        return f"Database Error:<br><br>{e}"