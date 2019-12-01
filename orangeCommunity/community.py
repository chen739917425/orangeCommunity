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
@bp.route('/person')
def person():
    return render_template('community/person.html')
#GET:获取用户个人信息
@bp.route('/profile')
def profile():
    if request.method=='GET':
        userid=request.args.get('id')
        con,cur=db.connect_db(DictCursor)
        sql='SELECT * FROM user WHERE user.id = %s'
        pram=(userid,)
        cur.execute(sql,pram)
        res=cur.fetchone()
        resp={'data':res}
        return Response(json.dumps(resp),mimetype='application/json')
#GET:查询用户的关注 POST:添加用户的关注
@bp.route('/following',methods=['GET','POST'])
def following():
    if request.method=='GET':
        userid=request.args.get('id')
        con,cur=db.connect_db(DictCursor)
        sql='''
            SELECT follow.userid,user.username,user.profile_pic
            FROM follow INNER JOIN user ON follow.userid = user.id
            WHERE follow.followerid = %s
        '''
        pram=(userid,)
        cur.execute(sql,pram)
        res=cur.fetchall()
        resp={'data':res}
        return Response(json.dumps(resp),mimetype='application/json')
    elif request.method=='POST':
        resp={'status':2000,'err':None}
        token=request.headers.get('ORGtoken')
        print(token)
        payload=JWT.verify_token(token)
        print(payload)
        if not payload:
            resp['status']=1005
            resp['err']='身份验证失效'
        else:
            data=request.get_data(as_text=True)
            data=json.loads(data)
            userid=data['userid']
            followid=data['followid']
            if str(payload['id'])!=userid:
                resp['status']=1005
                resp['err']='会话已失效'
            else:                
                con,cur=db.connect_db(DictCursor)
                sql='''
                    INSERT INTO follow (userid,followerid,ftime)
                    VALUES (%s, %s, CURRENT_TIMESTAMP)
                '''
                pram=(followid,userid)
                try:
                    cur.execute(sql,pram)
                    con.commit()
                except Exception as e:
                    print(e)
                    con.rollback()
                    resp['status']=1000
                    resp['err']='未知错误，请重试'
        return Response(json.dumps(resp),mimetype='application/json')          
#GET:查询用户的被关注
@bp.route('/follower')
def follower():
    if request.method=='GET':
        userid=request.args.get('id')
        con,cur=db.connect_db(DictCursor)
        sql='''
            SELECT follow.followerid,user.username,user.profile_pic
            FROM follow INNER JOIN user ON follow.followerid = user.id
            WHERE follow.userid = %s
        '''
        pram=(userid,)
        cur.execute(sql,pram)
        res=cur.fetchall()
        resp={'data':res}
        return Response(json.dumps(resp),mimetype='application/json')    
#GET:获取所有用户的博客动态
@bp.route('/all_blog')
def all_blog():
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
#GET:获取用户个人的博客动态
@bp.route('/person_blog')
def person_blog():
    if request.method=='GET':
        userid=request.args.get('id')
        con,cur=db.connect_db(DictCursor)
        sql='''
            SELECT blog.*
            FROM blog INNER JOIN user ON blog.userid=user.id
            WHERE user.id = %s
        '''
        pram=(userid,)
        cur.execute(sql,pram)
        res=cur.fetchall()
        for i in res:
            i['ptime']=i['ptime'].strftime('%Y-%m-%d %H:%M:%S')
        resp={'data':res}
        return Response(json.dumps(resp),mimetype='application/json')