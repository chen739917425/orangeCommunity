import re,os,sys,random,string,copy,json,pymysql
from pymysql.cursors import DictCursor
from flask import Blueprint,g,redirect, render_template,escape,url_for,request,Response
from flask_uploads import configure_uploads,UploadSet
from werkzeug.security import generate_password_hash,check_password_hash
from . import db, JWT
bp = Blueprint('community', __name__, url_prefix='/community')
@bp.route('/')
def community():
    return render_template('community/index.html')
@bp.route('/profile')
def profile():
    return render_template('community/profile.html')
@bp.route('/blog')
def blog():
    con,cur=db.connect_db(DictCursor)
    sql='''
        SELECT blog.*,user.username,user.profile_pic
        FROM blog INNER JOIN user ON blog.userid=user.id 
        ORDER BY blog.ptime DESC LIMIT 100
    '''
    cur.execute(sql)
    res=cur.fetchall()
    for i in res:
        i['ptime']=i['ptime'].strftime('%Y-%m-%d %H:%M:%S')
    resp={'data':res}
    return Response(json.dumps(resp),mimetype='application/json')
@bp.route('/blog/<userid>')
def user_blog(userid):
    return render_template('community/profile.html')