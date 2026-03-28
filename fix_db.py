import sqlite3

conn = sqlite3.connect('db.sqlite3')
c = conn.cursor()

try:
    c.execute("ALTER TABLE users_userprofile ADD COLUMN member_since date;")
    conn.commit()
    print("Column member_since added successfully.")
except sqlite3.OperationalError as e:
    print("Error:", e)

conn.close()
