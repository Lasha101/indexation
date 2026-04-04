SQLite Indexing Benchmark

A lightweight Python script to demonstrate the massive performance impact of database indexing. This project compares the lookup time for a specific value in a table of 100,000 records, both before and after applying a B-Tree index.

Overview

In database management, an index facilitates the transition from a sequential Full Table Scan, which requires checking every row in a table, to an Index Seek, which performs a targeted lookup using a specialized data structure to locate specific records directly.

This script:

Creates an in-memory SQLite database.

Populates it with 100,000 rows.

Measures the time to find the last record using a linear scan.

Creates an index on the value column.

Measures the time again to showcase the optimization.

Features

Zero Dependencies: Uses only the Python Standard Library (sqlite3, time).

In-Memory Performance: Runs entirely in RAM for clean, ephemeral testing.

Pure Logic: A crystal-clear example of O(N) vs O(logN) search complexity.

Usage

Ensure you have Python 3.x installed. Clone this repository and run the script:

Bash

python index.py
Sample Output
Results will vary based on your hardware, but the ratio is usually staggering:

Without index: 0.004512 seconds

With index: 0.000048 seconds

Note: In larger production datasets, the "Without Index" time grows linearly with the number of rows, while the "With Index" time remains nearly instantaneous.
