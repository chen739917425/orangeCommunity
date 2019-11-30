from flask import Flask,Blueprint,render_template
from flask_cors import *
def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_pyfile('config.py', silent=True)#加载配置文件
    CORS(app, supports_credentials=True)#允许跨域
    from . import auth, db, community
    app.register_blueprint(auth.bp)
    app.register_blueprint(community.bp)
    app.teardown_appcontext(db.close_db)
    @app.route('/')
    def index():
        return render_template('auth/index.html')
    @app.route('/community')
    def community():
        return render_template('community/index.html')
    @app.route('/community/profile')
    def profile():
        return render_template('community/profile.html')
    return app