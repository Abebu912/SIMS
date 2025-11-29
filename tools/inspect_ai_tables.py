import sqlite3, json
conn = sqlite3.connect('db.sqlite3')
cur = conn.cursor()
for t in ['ai_advisor_activitysuggestion','ai_advisor_learningplan','ai_advisor_studentpreference','ai_advisor_aiconversation','ai_advisor_subjectrecommendation']:
    try:
        cur.execute(f"PRAGMA table_info('{t}')")
        cols = cur.fetchall()
        print(t, json.dumps(cols))
    except Exception as e:
        print(t, 'ERROR', str(e))
