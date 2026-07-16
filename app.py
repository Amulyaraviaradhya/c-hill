from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
import os
import pandas as pd
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = "visitor_secret_key"

USERNAME = "admin"
PASSWORD = "admin123"

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not found.")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://","postgresql://",1)

def get_connection():
    return psycopg.connect(DATABASE_URL,row_factory=dict_row)

def create_table():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('''
            CREATE TABLE IF NOT EXISTS visitors(
                id SERIAL PRIMARY KEY,
                name VARCHAR(100),
                reference_person VARCHAR(100),
                number_of_people INTEGER,
                vehicle_number VARCHAR(50),
                entry_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
        conn.commit()

create_table()

@app.route("/", methods=["GET","POST"])
def login():
    if request.method=="POST":
        if request.form.get("username")==USERNAME and request.form.get("password")==PASSWORD:
            session["user"]=USERNAME
            return redirect(url_for("form"))
        return render_template("login.html",error="Invalid Username or Password")
    return render_template("login.html")

@app.route("/form", methods=["GET","POST"])
def form():
    if "user" not in session:
        return redirect(url_for("login"))
    if request.method=="POST":
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('''INSERT INTO visitors(name,reference_person,number_of_people,vehicle_number)
                               VALUES(%s,%s,%s,%s)''',
                            (request.form.get("name","").strip(),
                             request.form.get("reference","").strip(),
                             int(request.form.get("people","0")),
                             request.form.get("vehicle","").strip().upper()))
            conn.commit()
        return redirect(url_for("dashboard"))
    return render_template("form.html")

def _rows():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM visitors ORDER BY id DESC')
            rows=cur.fetchall()
    data=[]
    for r in rows:
        data.append({"ID":r["id"],"Name":r["name"],"Reference Person":r["reference_person"],
                     "Number of People":r["number_of_people"],"Vehicle Number":r["vehicle_number"],
                     "Entry Time":r["entry_time"].strftime("%d-%m-%Y %H:%M:%S")})
    return data

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("dashboard.html",data=_rows())

@app.route("/view")
def view():
    return render_template("viewer.html",data=_rows())

@app.route("/api/data")
def api_data():
    return jsonify(_rows())

@app.route("/download")
def download():
    if "user" not in session:
        return redirect(url_for("login"))
    with get_connection() as conn:
        df=pd.read_sql('SELECT name AS "Name",reference_person AS "Reference Person",number_of_people AS "Number of People",vehicle_number AS "Vehicle Number",entry_time AS "Entry Time" FROM visitors ORDER BY id DESC',conn)
    f="responses.xlsx"
    df.to_excel(f,index=False)
    return send_file(f,as_attachment=True)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",5000)),debug=False)
