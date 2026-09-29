"""Audit the actual data in the DB to understand the current matching pipeline."""

import sqlite3

conn = sqlite3.connect("projectmind.db")
c = conn.cursor()

# Check employee_skills table
c.execute("SELECT COUNT(*) FROM employee_skills")
print(f"employee_skills rows: {c.fetchone()[0]}")

# Check how current_tech_stack was imported - the domain_expertise field
c.execute("SELECT name, domain_expertise FROM employees LIMIT 5")
print("\nSample domain_expertise (actual current_tech_stack stored here):")
for r in c.fetchall():
    print(f"  {r[0]}: {r[1]}")

# Check assignment manager_notes (tech history stored here)
c.execute("SELECT employee_id, role_on_project, manager_notes FROM assignments LIMIT 3")
print("\nSample assignment manager_notes:")
for r in c.fetchall():
    print(f"  emp={r[0]}, role={r[1]}: {r[2][:200]}")

# See if any skills were registered at all
c.execute("SELECT id, name, category FROM skills LIMIT 10")
print("\nSkills table:")
for r in c.fetchall():
    print(f"  {r}")

# Check what the candidate_filter does for a fintech query
c.execute("""
    SELECT e.id, e.name, e.domain_expertise, e.is_available
    FROM employees e
    WHERE e.is_available = 1 AND e.availability_percentage >= 30
    AND LOWER(e.domain_expertise) LIKE '%fintech%'
    LIMIT 5
""")
print("\nEmployees with fintech in domain_expertise:")
for r in c.fetchall():
    print(f"  {r[0]}: {r[1]} | domain_expertise: {r[2]}")
