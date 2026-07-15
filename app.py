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

import mysql.connector
import pandas as pd
import os

app = Flask(__name__)
app.secret_key = "visitor_secret_key"

# =====================================
# LOGIN CREDENTIALS
# =====================================

USERNAME = "admin"
PASSWORD = "admin123"

# =====================================
# MYSQL DATABASE
# =====================================

DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "root123"
DB_NAME = "chill_db"

# =====================================
# DATABASE CONNECTION
# =====================================

def get_connection():

    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )

# =====================================
# CREATE TABLE
# =====================================

def create_table():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""

        CREATE TABLE IF NOT EXISTS visitors(

            id INT AUTO_INCREMENT PRIMARY KEY,

            name VARCHAR(100),

            reference_person VARCHAR(100),

            number_of_people INT,

            vehicle_number VARCHAR(50),

            entry_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )

    """)

    conn.commit()

    cursor.close()

    conn.close()

create_table()

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

            conn = get_connection()

            cursor = conn.cursor()

            cursor.execute("""

                INSERT INTO visitors
                (
                    name,
                    reference_person,
                    number_of_people,
                    vehicle_number
                )

                VALUES
                (%s,%s,%s,%s)

            """,
            (
                name,
                reference,
                int(people),
                vehicle
            ))

            conn.commit()

            cursor.close()

            conn.close()

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

        conn = get_connection()

        cursor = conn.cursor(dictionary=True)

        cursor.execute("""

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

        rows = cursor.fetchall()

        cursor.close()
        conn.close()

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

        conn = get_connection()

        cursor = conn.cursor(dictionary=True)

        cursor.execute("""

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

        rows = cursor.fetchall()

        cursor.close()
        conn.close()

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


# =====================================
# EXPORT TO EXCEL
# =====================================

@app.route("/export")
def export():

    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_connection()

    query = """

        SELECT

            id,
            name,
            reference_person,
            number_of_people,
            vehicle_number,
            entry_time

        FROM visitors

        ORDER BY id DESC

    """

    df = pd.read_sql(query, conn)

    conn.close()

    file_name = "Visitor_Report.xlsx"

    df.to_excel(file_name, index=False)

    return send_file(
        file_name,
        as_attachment=True
    )


# =====================================
# API FOR AUTO REFRESH
# =====================================

@app.route("/api/visitors")
def api_visitors():

    conn = get_connection()

    cursor = conn.cursor(dictionary=True)

    cursor.execute("""

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

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    for row in rows:

        row["entry_time"] = row["entry_time"].strftime("%d-%m-%Y %H:%M:%S")

    return jsonify(rows)


# =====================================
# LOGOUT
# =====================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))



# =====================================
# RUN APPLICATION
# =====================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )