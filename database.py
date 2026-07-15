import sqlite3

conn = sqlite3.connect("responses.db")

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS visitors(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    reference_person TEXT,
    number_of_people INTEGER,
    vehicle_number TEXT
)
""")

conn.commit()
conn.close()

print("Database Created")