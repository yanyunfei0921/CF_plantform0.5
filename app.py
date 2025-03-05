from flask import Flask, render_template, request
from utils.db import init_db
from api.serial_settings import serial_settings_bp
from api.image_stream import image_stream_bp
from extensions import socketio
import eventlet

app = Flask(__name__, static_folder="static", template_folder="templates")
socketio.init_app(app)  # 初始化socketio

# 设置 Jinja2 模板变量分隔符
app.jinja_env.variable_start_string = "**DIM LIGHT**"
app.jinja_env.variable_end_string = "**DIM LIGHT**"

# 注册蓝图
app.register_blueprint(serial_settings_bp)
app.register_blueprint(image_stream_bp)

# 初始化数据库
init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.after_request
def add_no_cache_header(response):
    if request.path.startswith('/static/'):
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
    return response

if __name__ == '__main__':
    socketio.run(app, debug=True)