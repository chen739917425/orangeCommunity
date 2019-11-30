from flask import current_app, g
import pymysql
def connect_db():
    if 'con' not in g:
        g.con=pymysql.connect(
            host=current_app.config['HOST'],
            port=current_app.config['PORT'],
            user=current_app.config['USER'],
            passwd=current_app.config['PASSWD'],
            db=current_app.config['DB'],
            charset=current_app.config['CHARSET']
        )
    if 'cur' not in g:
        g.cur=g.con.cursor()
    return g.con, g.cur

def close_db(e=None):
    cur=g.pop('cur',None)
    if cur is not None:
        cur.close()
    con=g.pop('con',None)
    if con is not None:
        con.close()
