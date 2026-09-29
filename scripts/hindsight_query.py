import os
import sqlite3

db_path = "hindsight_local.db"
if not os.path.exists(db_path):
    print(f"{db_path} does not exist.")
else:
    print(f"{db_path} size: {os.path.getsize(db_path)} bytes")

conn = sqlite3.connect(db_path)
c = conn.cursor()

c.execute("SELECT COUNT(*) FROM memories")
count = c.fetchone()[0]
print(f"Total Memories: {count}")

c.execute("SELECT memory_id, memory_type, domain, project_title, metadata FROM memories LIMIT 3")
for r in c.fetchall():
    print(r)

c.execute("""
SELECT COUNT(*) FROM memories 
WHERE (LOWER(content) LIKE '%python%' OR LOWER(summary) LIKE '%python%') 
  AND LOWER(domain) LIKE '%fintech%'
""")
python_fintech_count = c.fetchone()[0]
print(f"Memories with python and fintech: {python_fintech_count}")

c.execute("SELECT DISTINCT domain FROM memories")
domains = [r[0] for r in c.fetchall()]
print(f"Domains in memories: {domains}")

c.execute(
    "SELECT memory_id, domain, content, summary FROM memories ORDER BY created_at DESC LIMIT 500"
)
rows = c.fetchall()
fintech_count = sum(1 for r in rows if "fintech" in r[1].lower())
python_count = sum(1 for r in rows if "python" in r[2].lower() or "python" in r[3].lower())
print(f"In last 500 memories: fintech={fintech_count}, python={python_count}")
