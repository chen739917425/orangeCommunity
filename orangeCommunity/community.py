import re,os,sys,random,string,copy,json,pymysql
from flask import Blueprint,g,redirect, render_template,escape,url_for,request,Response
from flask_uploads import configure_uploads,UploadSet
from werkzeug.security import generate_password_hash,check_password_hash
from . import db, JWT
bp = Blueprint('community', __name__, url_prefix='/community')
@bp.route('/')
def index():
    return render_template('community/index.html')