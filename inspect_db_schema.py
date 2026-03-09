
import sqlite3
import os

db_path = "data/babelcomics.db"

if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("--- Table Schema ---")
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='comicbooks_info_covers'")
schema = cursor.fetchone()
if schema:
    print(schema[0])
else:
    print("Table not found!")

print("\n--- SQLite Sequence ---")
try:
    cursor.execute("SELECT * FROM sqlite_sequence WHERE name='comicbooks_info_covers'")
    seq = cursor.fetchone()
    if seq:
        print(f"Current sequence for comicbooks_info_covers: {seq}")
    else:
        print("No sequence found for comicbooks_info_covers (might mean it's empty or hasn't auto-incremented yet)")
except sqlite3.OperationalError:
    print("sqlite_sequence table does not exist or error accessing it.")

print("\n--- Max ID ---")
cursor.execute("SELECT MAX(id_cover) FROM comicbooks_info_covers")
max_id = cursor.fetchone()[0]
print(f"Max id_cover in table: {max_id}")


print("\n--- Check for Issue 10600 ---")
cursor.execute("SELECT * FROM comicbooks_info WHERE id_comicbook_info=10600")
issue = cursor.fetchone()
if issue:
    print(f"Issue 10600 found: {issue}")
else:
    print("Issue 10600 NOT found")

print("\n--- Check Covers for Issue 10600 ---")
cursor.execute("SELECT * FROM comicbooks_info_covers WHERE id_comicbook_info=10600")
covers = cursor.fetchall()
if covers:
    print(f"Found {len(covers)} covers for issue 10600:")
    for cover in covers:
        print(cover)
else:
    print("No covers found for issue 10600")
