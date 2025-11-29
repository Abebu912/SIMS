import sqlite3
import sys

DB_PATH = 'db.sqlite3'

def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    try:
        # Ensure column doesn't already exist
        cur.execute("PRAGMA table_info('subjects_subject')")
        cols = [r[1] for r in cur.fetchall()]
        if 'assigned_by_registrar' in cols:
            print('Column already exists: assigned_by_registrar')
            return 0

        # Add the boolean column as integer with default 0 (False)
        cur.execute("ALTER TABLE subjects_subject ADD COLUMN assigned_by_registrar INTEGER NOT NULL DEFAULT 0")
        conn.commit()
        print('Added column assigned_by_registrar to subjects_subject')
        return 0
    except sqlite3.OperationalError as e:
        print('OperationalError:', e)
        return 2
    except Exception as e:
        print('Error:', e)
        return 3
    finally:
        conn.close()

if __name__ == '__main__':
    sys.exit(main())
