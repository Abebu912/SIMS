import sqlite3, sys
conn=sqlite3.connect('db.sqlite3')
cur=conn.cursor()
apps = ['payments_payment','payments_paymentrecord','ai_advisor_aiconversation','ai_advisor_activitysuggestion','notifications_announcement']
for t in apps:
    try:
        cur.execute(f"PRAGMA table_info('{t}')")
        cols = cur.fetchall()
        print(t, cols)
    except Exception as e:
        print(t, 'ERROR', e)
