import re,os,sys,random,string,copy,json,pymysql
from flask import Blueprint,g,redirect, render_template,escape,url_for,request,Response

from werkzeug.security import generate_password_hash,check_password_hash
from . import db, JWT

bp = Blueprint('auth', __name__, url_prefix='/auth')
#验证登陆态
@bp.route('/verify',methods=['POST'])
def verify():
    if request.method=='POST':
        data=request.get_data(as_text=True)
        data=json.loads(data)
        userid=data['userid']
        token=request.headers.get('ORGtoken')
        payload=JWT.verify_token(token)
        resp={'status':2000,'data':None}
        if not payload:
            resp['status']=1005
            return Response(json.dumps(resp),mimetype='application/json')
        if userid!=str(payload['id']):
            resp['status']=1005
            return Response(json.dumps(resp),mimetype='application/json')
        con,cur=db.connect_db()
        sql='SELECT username,profile_pic FROM user WHERE id = %s'
        pram=(userid,)
        cur.execute(sql,pram)
        res=cur.fetchone()
        resp['data']={'username':res[0],'profile_pic':res[1]}
        return Response(json.dumps(resp),mimetype='application/json')

@bp.route('/register',methods=['POST'])
def register():
    if (request.method=='POST'):
        data=request.get_data(as_text=True)
        data=json.loads(data)
        username=data['username']
        psw=data['psw']
        email=data['email']
        phone=data['phone']
        resp={'status':2000,'err':None}
        if not username:
            resp['status']=1001
            resp['err']='用户名不能为空'
        elif not psw:
            resp['status']=1002
            resp['err']='密码不能为空'
        if resp['status']!=2000:
            return Response(json.dumps(resp),mimetype='application/json')
        con,cur=db.connect_db()
        sql='SELECT COUNT(*) FROM user WHERE username = %s'
        pram=(username,)
        cur.execute(sql,pram)
        res=cur.fetchone()
        if res[0]:
            resp['status']=1003
            resp['err']='用户名已存在'
        else:
            psw=generate_password_hash(psw)
            sql='INSERT INTO user (username,psw,email,phone) VALUES (%s,%s,%s,%s)'
            pram=(username,psw,email,phone)
            try:
                cur.execute(sql,pram)
                con.commit()
            except Exception as e:
                print(e)
                con.rollback()
                resp['status']=1000
                resp['err']='服务器内部错误，请重试'
        return Response(json.dumps(resp),mimetype='application/json')
@bp.route('/login',methods=['POST'])
def login():
    if request.method=='POST':
        data=request.get_data(as_text=True)
        data=json.loads(data)
        username=data['username']
        psw=data['psw']
        resp={'status':2000,'err':None,'data':None}
        con,cur=db.connect_db()
        sql='SELECT id, psw FROM user WHERE username = %s'
        pram=(username,)
        res=cur.execute(sql,pram)
        if not res:
            resp['status']=1004
            resp['err']='用户名或密码有误'
            return Response(json.dumps(resp),mimetype='application/json')
        res=cur.fetchone()
        if not check_password_hash(res[1],psw):
            resp['status']=1004
            resp['err']='用户名或密码有误'
            return Response(json.dumps(resp),mimetype='application/json')
        token=JWT.generate_token({'id':res[0]},2*3600).decode('ascii')
        resp['data']={'id':res[0],'token':token}
        return Response(json.dumps(resp),mimetype='application/json')
