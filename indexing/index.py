# def db_connector():
#     import sqlite3
#     return sqlite3.connect(':memory:')

# def db_cursor(conn):
#     return conn.cursor()

# conn = db_connector()

# cursor = db_cursor(conn)


import sqlite3
import time

def measure_exec_time(called_func, *args, **kwargs):
    start_time = time.time()
    called_func(*args, **kwargs) 
    return time.time() - start_time

def query_executor(query, params=()):
    cursor.execute(query, params)
    return cursor.fetchall()

conn = sqlite3.connect(':memory:')
cursor = conn.cursor()

cursor.execute('''CREATE TABLE numbers (
               id INTEGER PRIMARY KEY,
               value INTEGER)
''')

num_rows = 100000
cursor.executemany('INSERT INTO numbers (value) VALUES (?)', [(i,) for i in range(num_rows)])
conn.commit()

query_string = "SELECT * FROM numbers WHERE value = ?"
query_params = (99999,)


non_indexed_time = measure_exec_time(query_executor, query_string, query_params)

cursor.execute('CREATE INDEX idx_value ON numbers(value)')
conn.commit()


indexed_time = measure_exec_time(query_executor, query_string, query_params)

print(f"Without index: {non_indexed_time:.6f} seconds")
print(f"With index:    {indexed_time:.6f} seconds")

conn.close()