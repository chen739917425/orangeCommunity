import re,os,sys,random,string,copy,json,pymysql
from pymysql.cursors import DictCursor
from flask import current_app,Blueprint,g,redirect, render_template,escape,url_for,request,Response
from flask_uploads import configure_uploads,UploadSet
from werkzeug.security import generate_password_hash,check_password_hash
from . import db, JWT
bp = Blueprint('community', __name__, url_prefix='/community')
@bp.route('/',methods=['GET','POST'])
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
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg'}
@bp.route('/profile_pic',methods=['POST'])
def profile_pic():
    if request.method=='POST':
        resp={'status':2000,'err':None}
        token=request.headers.get('ORGtoken')
        payload=JWT.verify_token(token)
        if not payload:
            resp['status']=1005
            resp['err']='身份验证失效'
        userid=request.args.get('id')
        if userid!=str(payload['id']):
            resp['status']=1005
            resp['err']='身份验证失效'
            return Response(json.dumps(resp),mimetype='application/json');
        if 'file' not in request.files:
            resp['status']=1006
            resp['err']='未上传文件'
            return Response(json.dumps(resp),mimetype='application/json');
        file = request.files['file']
        if file.filename == '':
            resp['status']=1007
            resp['err']='未选择文件'
            return Response(json.dumps(resp),mimetype='application/json');
        if file and allowed_file(file.filename):
            basedir = os.path.abspath(os.path.dirname(__file__))
            filename = userid+'.'+file.filename.rsplit('.', 1)[1].lower()
            file_url=os.path.join(current_app.config['UPLOAD_FOLDER'],filename)
            file_path=os.path.join(basedir,file_url)
            file.save(file_path)
            con,cur=db.connect_db(DictCursor)
            sql='''
                UPDATE user
                SET profile_pic = %s
                WHERE id = %s
            '''
            pram=(file_url,userid)
            try:
                cur.execute(sql,pram)
                con.commit()
            except Exception as e:
                print(e)
                con.rollback()
                resp['status']=1000
                resp['err']='未知错误'
        else:
            resp['status']=1008
            resp['err']='图片不合法，仅支持jpg, jpeg, png'             
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
        payload=JWT.verify_token(token)
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
                resp['err']='身份验证失效'
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
#GET:获取所有用户的博客
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
#GET:获取用户个人的博客 POST:发布用户的博客
@bp.route('/person_blog',methods=['GET','POST'])
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
    elif request.method=='POST':
        resp={'status':2000,'err':None}
        token=request.headers.get('ORGtoken')
        payload=JWT.verify_token(token)
        if not payload:
            resp['status']=1005
            resp['err']='身份验证失效'
        else:
            data=request.get_data(as_text=True)
            data=json.loads(data)
            userid=data['userid']
            topic=data['topic']
            content=data['content']
            college=data['college']
            typ=data['type']
            if str(payload['id'])!=userid:
                resp['status']=1005
                resp['err']='身份验证失效'
            else:                
                con,cur=db.connect_db(DictCursor)
                sql='''
                    INSERT INTO blog (userid,topic,content,type,college,ptime)
                    VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                '''
                pram=(userid,topic,content,typ,college)
                try:
                    cur.execute(sql,pram)
                    con.commit()
                except Exception as e:
                    print(e)
                    con.rollback()
                    resp['status']=1000
                    resp['err']='未知错误，请重试'
        return Response(json.dumps(resp),mimetype='application/json') 
#GET:获取用户关注人的博客
@bp.route('/follow_blog')
def follow_blog():
    if request.method=='GET':
        userid=request.args.get('id')
        con,cur=db.connect_db(DictCursor)
        sql='''
            SELECT blog.*
            FROM blog INNER JOIN follow ON follow.userid = blog.userid
            WHERE follow.followerid = %s
            ORDER BY ptime DESC LIMIT 50
        '''
        pram=(userid,)
        cur.execute(sql,pram)
        res=cur.fetchall()
        for i in res:
            i['ptime']=i['ptime'].strftime('%Y-%m-%d %H:%M:%S')
        resp={'data':res}
        return Response(json.dumps(resp),mimetype='application/json')
