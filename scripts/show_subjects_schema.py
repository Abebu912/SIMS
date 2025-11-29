import sqlite3

DB_PATH = 'db.sqlite3'

def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("PRAGMA table_info('subjects_subject')")
    rows = cur.fetchall()
    print('subjects_subject schema:')
    for r in rows:
        print(r)
    conn.close()

if __name__ == '__main__':
    main()
