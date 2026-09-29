import sqlite3

conn = sqlite3.connect("hindsight_local.db")
c = conn.cursor()

c.execute(
    "SELECT memory_id, domain, memory_type, content FROM memories WHERE LOWER(domain) = 'fintech' LIMIT 5"
)
print("First 5 Fintech memories:")
for r in c.fetchall():
    print(r)

c.execute("SELECT memory_type, COUNT(*) FROM memories GROUP BY memory_type")
print("\nMemory Types Breakdown:")
for r in c.fetchall():
    print(r)
