import os
import sqlite3
os.chdir(r'C:\Users\User\Desktop\Python Study Tracker')
conn = sqlite3.connect('studytracker.db')
cur = conn.cursor()
cur.execute('PRAGMA table_info(tasks)')
print('schema:')
for row in cur.fetchall():
    print(row)
cur.execute('SELECT * FROM tasks ORDER BY id DESC LIMIT 1')
print('latest row:')
print(cur.fetchone())
conn.close()
