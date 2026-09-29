import os
import sqlite3

from config.settings import get_settings

print(f"Working Directory: {os.getcwd()}")
settings = get_settings()
print(f"Settings DB Path: {settings.database_url}")

db_path = "projectmind.db"
if not os.path.exists(db_path):
    print(f"{db_path} does not exist.")
else:
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM employees")
    count = c.fetchone()[0]
    print(f"Total Employees: {count}")

    c.execute("SELECT id, name FROM employees LIMIT 20")
    print("First 20 Employees:")
    for row in c.fetchall():
        print(f"  {row[0]}: {row[1]}")

    c.execute(
        'SELECT id, name FROM employees WHERE name IN ("Dustin Nelson", "Donald Lewis", "Susan Rivas", "Jeffrey Campbell")'
    )
    names = c.fetchall()
    print("Specific Employees found:", names)

    c.execute('SELECT COUNT(*) FROM employees WHERE name LIKE "%Sharma%"')
    sharmas = c.fetchone()[0]
    print(f"Sharmas found: {sharmas}")
