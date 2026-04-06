# def db_connector():
#     import sqlite3
#     return sqlite3.connect(':memory:')

# def db_cursor(conn):
#     return conn.cursor()

# conn = db_connector()

# cursor = db_cursor(conn)


from sqlite3 import connect
import time

def measure_exec_time(called_func, *args, **kwargs):
    start_time = time.perf_counter()
    called_func(*args, **kwargs) 
    return time.perf_counter() - start_time



def query_exec(query, *args):
    return cursor.execute(query, *args)

def fetchall_exec(cursor):
    return cursor.fetchall()

def connection():
    return connect(':memory:')

def crsr(conn):
    return conn.cursor()

def commiter():
    conn.commit()


conn = connection()

cursor = crsr(conn)

def query_executor(query, *args):
    query_exec(query, *args)
    fetchall_exec(cursor)



query_exec('''CREATE TABLE numbers (
               id INTEGER PRIMARY KEY,
               value INTEGER)
''')

num_rows = 100000
cursor.executemany('INSERT INTO numbers (value) VALUES (?)', [(i,) for i in range(num_rows)])
commiter()

query_string = "SELECT * FROM numbers WHERE value = ?"
query_params = (99999,)

non_indexed_time = measure_exec_time(query_executor, query_string, query_params)



query_exec('CREATE INDEX idx_value ON numbers(value)')
commiter()


indexed_time = measure_exec_time(query_executor, query_string, query_params)

print(f"Without index: {non_indexed_time:.6f} seconds")
print(f"With index:    {indexed_time:.6f} seconds")

conn.close()