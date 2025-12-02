import sqlite3, os, sys

DB = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'db.sqlite3')
if not os.path.exists(DB):
    print('DB not found:', DB)
    sys.exit(1)
con = sqlite3.connect(DB)
cur = con.cursor()
try:
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cur.fetchall()]
    print('Tables:', tables)
    if 'ranks_grade' in tables:
        cur.execute('PRAGMA table_info(ranks_grade)')
        cols = [c[1] for c in cur.fetchall()]
        print('ranks_grade columns:', cols)
        cur.execute('SELECT id, student_id, subject_id, score, quiz_score, mid_score, assignment_score, final_exam_score, remarks FROM ranks_grade ORDER BY id DESC LIMIT 50')
        rows = cur.fetchall()
        print('Latest ranks_grade rows (id, student_id, subject_id, score, quiz, mid, assignment, final, remarks):')
        for r in rows:
            print(r)
    else:
        print('ranks_grade table not found')
finally:
    con.close()
