import sqlite3
import time 

conn = sqlite3.connect(':memory:')
cursor = conn.cursor()

cursor.execute('''CREATE TABLE numbers (
               id INTEGER PRIMARY KEY,
               value INTEGER)
''')

num_rows = 100000
cursor.executemany('INSERT INTO numbers (value) VALUES (?)', [(i,) for i in range(num_rows)])
conn.commit()

def measure_query_time(query, params=None):
    start_time = time.time()
    cursor.execute(query, params or ())
    cursor.fetchall()
    return time.time() - start_time

non_indexed_time = measure_query_time("SELECT * FROM numbers WHERE value = ?", (99999,))

cursor.execute('CREATE INDEX idx_value ON numbers(value)')
conn.commit()

indexed_time = measure_query_time("SELECT * FROM numbers WHERE value = ?", (99999,))

print(f"Without index: {non_indexed_time:.6f} seconds")
print(f"With index: {indexed_time:.6f} seconds")

conn.close()