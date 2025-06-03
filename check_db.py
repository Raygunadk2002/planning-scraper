#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('planning_applications.db')
cursor = conn.cursor()

cursor.execute('SELECT COUNT(*) FROM planning_applications')
count = cursor.fetchone()[0]
print(f'Applications in database: {count}')

if count > 0:
    cursor.execute('SELECT project_id, borough, detected_keywords FROM planning_applications LIMIT 5')
    print('\nSample applications:')
    for row in cursor.fetchall():
        print(f'  {row[0]} ({row[1]}): {row[2]}')

conn.close() 