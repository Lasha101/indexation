import sqlite3  
import time

def measure_exec_time(called_func, *args, **kwargs):
    start_time = time.perf_counter()
    called_func(*args, **kwargs) 
    return time.perf_counter() - start_time



class DbManager:
    def __init__(self, db_path=':memory:'):
        self.db_path = db_path
        self.connection = None
        self.cursor = None

    def __enter__(self):
        self.connection = sqlite3.connect(self.db_path)
        self.cursor = self.connection.cursor()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.connection:
            if exc_type is None:
                self.connection.commit()
            if self.cursor:
                self.cursor.close()
            self.connection.close()

    def execute(self, query, params=()):
        if self.cursor is None:
            raise RuntimeError("Database not connected. Use within a 'with' block.")
        self.cursor.execute(query, params)
        if self.cursor.description is not None:
            return self.cursor.fetchall()
        return None
    
    def executemany(self, query, seq_of_parameters):
        if self.cursor is None:
            raise RuntimeError("Database not connected. Use within a 'with' block.")
        self.cursor.executemany(query, seq_of_parameters)


with DbManager(':memory:') as db:
    db.execute('CREATE TABLE numbers (id INTEGER PRIMARY KEY, VALUE INTEGER)')
    db.executemany('INSERT INTO numbers (value) VALUES (?)', [(i,) for i in range(100000)])
    
    query_string = 'SELECT * FROM numbers WHERE value = ?'
    query_params = (99999,)

    non_indexed_time = measure_exec_time(db.execute, query_string, query_params)

    db.execute('CREATE INDEX idx_value ON numbers (value)')

    indexed_time = measure_exec_time(db.execute, query_string, query_params)

    print(f"Without index: {non_indexed_time:.6f} seconds")
    print(f"With index:    {indexed_time:.6f} seconds")






    

