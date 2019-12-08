import re,os,sys,random,string,copy,json,pymysql
from pymysql.cursors import DictCursor
from flask import current_app,Blueprint,g,redirect, render_template,escape,url_for,request,Response
from flask_uploads import configure_uploads,UploadSet
from werkzeug.security import generate_password_hash,check_password_hash
from . import db, JWT
bp = Blueprint('community', __name__, url_prefix='/community')

#验证token
def check_token(userid,token):
    payload=JWT.verify_token(token)
    if not payload:
        return False
    if userid!=str(payload['id']):
        return False
    return True

#定向社区首页
@bp.route('/')
def community():
    return render_template('community/index.html')

#定向社区个人页
@bp.route('/person')
def person():
    return render_template('community/person.html')

#定向博客发布页
@bp.route('/poster')
def poster():
    return render_template('community/poster.html')

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

#POST:上传头像
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg'}
@bp.route('/profile_pic',methods=['POST'])
def profile_pic():
    if request.method=='POST':
        resp={'status':2000,'err':None}
        token=request.headers.get('ORGtoken')
        userid=request.args.get('id')
        if not check_token(userid,token):
            resp['status']=1005
            resp['err']='身份验证失效，请重新登录'
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
                resp['err']='服务器内部错误'
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
        data=request.get_data(as_text=True)
        data=json.loads(data)
        userid=data['userid']
        followid=data['followid']
        if not check_token(userid,token):
            resp['status']=1005
            resp['err']='身份验证失效，请重新登录'
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
                resp['err']='服务器内部错误，请重试'
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
    if request.method=='GET':
        typ=request.args.get('type')
        college=request.args.get('college')
        order=request.args.get('order')
        con,cur=db.connect_db(DictCursor)
        sql='SELECT blog.*,user.username,user.profile_pic '
        if order=='comment':
            sql+='''
                FROM blog INNER JOIN user ON blog.userid=user.id 
                LEFT OUTER JOIN comment ON blog.id=comment.blogid
                WHERE 1 
            '''        
        else:
            sql+=' FROM blog INNER JOIN user ON blog.userid=user.id WHERE 1 '
        pram=[]
        if college!='all':
            sql+=" and (blog.college = %s OR blog.college = 'all') "
            pram.append(college)
        if typ!='all':
            sql+=' and blog.type = %s '
            pram.append(typ)
        if order=='comment':
            sql+='''
                GROUP BY blog.id
                ORDER BY COUNT(comment.id) DESC
            '''        
        else:
            sql+=' ORDER BY blog.ptime DESC '
        pram=tuple(pram)
        cur.execute(sql,pram)
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
        data=request.get_data(as_text=True)
        data=json.loads(data)
        userid=data['userid']
        topic=data['topic']
        content=data['content']
        college=data['college']
        typ=data['type']
        if not check_token(userid,token):
            resp['status']=1005
            resp['err']='身份验证失效,请重新登录'
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
                resp['err']='服务器内部错误，请重试'
        return Response(json.dumps(resp),mimetype='application/json') 

#GET:获取用户所有关注人的博客
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

#GET:获取博客的评论 POST:添加博客的评论
@bp.route('/blog_comment',methods=['GET','POST'])
def blog_comment():
    if request.method=='GET':
        blogid=request.args.get('id')
        con,cur=db.connect_db(DictCursor)
        sql='''
            SELECT * FROM comment 
            WHERE blogid = %s
            ORDER BY ctime DESC
        '''
        pram=(blogid,)
        cur.execute(sql,pram)
        res=cur.fetchall()
        for i in res:
            i['ctime']=i['ctime'].strftime('%Y-%m-%d %H:%M:%S')
        resp={'data':res}
        return Response(json.dumps(resp),mimetype='application/json')
    elif request.method=='POST':
        resp={'status':2000,'err':None}
        token=request.headers.get('ORGtoken')
        data=request.get_data(as_text=True)
        data=json.loads(data)
        userid=data['userid']
        blogid=data['blogid']
        content=data['content']
        if not check_token(userid,token):
            resp['status']=1005
            resp['err']='身份验证失效，请重新登录'
            return Response(json.dumps(resp),mimetype='application/json')
        con,cur=db.connect_db(DictCursor)
        sql='''
            INSERT INTO comment (userid,blogid,content,ctime)
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
        '''
        pram=(userid,blogid,content)
        try:
            cur.execute(sql,pram)
            con.commit()
        except Exception as e:
            print(e)
            con.rollback()
            resp['status']=1000
            resp['err']='服务器内部错误'
        return Response(json.dumps(resp),mimetype='application/json')

#GET:获取用户的评论
@bp.route('/user_comment')
def user_comment():
    if request.method=='GET':
        userid=request.args.get('id')
        con,cur=db.connect_db(DictCursor)
        sql='SELECT * FROM comment WHERE userid = %s'
        pram=(userid,)
        cur.execute(sql,pram)
        res=cur.fetchall()
        for i in res:
            i['ctime']=i['ctime'].strftime('%Y-%m-%d %H:%M:%S')
        resp={'data':res}
        return Response(json.dumps(resp),mimetype='application/json')
