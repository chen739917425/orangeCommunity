import pymysql
con=pymysql.connect(
    host='127.0.0.1',
    port=3306,
    user='root',
    passwd='orange',
    db='orange_community',
    charset='utf8'
)
cur=con.cursor()
#创建用户表
user_table='''CREATE TABLE user(
        id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(20) NOT NULL UNIQUE, 
        psw VARCHAR(100) NOT NULL,
        profile_pic VARCHAR(80),
        email VARCHAR(20),
        phone VARCHAR(20)
    )'''
try:
    cur.execute(user_table)
    con.commit()
except Exception as e:
    print(e)
    con.rollback()
#创建话题表
blog_table='''CREATE TABLE blog(
        id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
        userid INT NOT NULL,
        college VARCHAR(20),
        topic VARCHAR(20) NOT NULL,
        type VARCHAR(10),
        content VARCHAR(500) NOT NULL,
        ptime TIMESTAMP NOT NULL,
        FOREIGN KEY(userid) REFERENCES user(id)
    )'''
try:
    cur.execute(blog_table)
    con.commit()
except Exception as e:
    print(e)
    con.rollback()
#创建评论表
comment_table='''CREATE TABLE comment(
        id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
        userid INT NOT NULL,
        blogid INT NOT NULL,
        content VARCHAR(500) NOT NULL,
        ctime TIMESTAMP NOT NULL,
        upvote INT NOT NULL DEFAULT 0,
        FOREIGN KEY(userid) REFERENCES user(id),
        FOREIGN KEY(blogid) REFERENCES blog(id)
    )'''
try:
    cur.execute(comment_table)
    con.commit()
except Exception as e:
    print(e)
    con.rollback()
#创建关注关系表
follow_table='''CREATE TABLE follow(
        id INT NOT NULL,
        followid INT NOT NULL,
        ftime TIMESTAMP NOT NULL,
        PRIMARY KEY(id,followid),
        FOREIGN KEY(id) REFERENCES user(id),
        FOREIGN KEY(followid) REFERENCES blog(id)
    )'''
try:
    cur.execute(follow_table)
    con.commit()
except Exception as e:
    print(e)
    con.rollback()
cur.close()
con.close()