import sqlite3
conn=sqlite3.connect('db.sqlite3')
cur=conn.cursor()
for t in ['notifications_announcement','notifications_notification']:
    try:
        cur.execute(f"PRAGMA table_info('{t}')")
        print(t, cur.fetchall())
    except Exception as e:
        print(t, 'ERROR', e)
