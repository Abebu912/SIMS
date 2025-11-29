import sqlite3

DB_PATH = 'db.sqlite3'

def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='django_migrations'")
    exists = bool(cur.fetchall())
    print('django_migrations exists:', exists)
    if not exists:
        conn.close()
        return
    cur.execute("SELECT id, app, name, applied FROM django_migrations WHERE app='subjects' ORDER BY id")
    rows = cur.fetchall()
    print('subjects migrations recorded in django_migrations:')
    for r in rows:
        print(r)
    conn.close()

if __name__ == '__main__':
    main()
