import base64
from flask import Blueprint, jsonify, request
from extensions import socketio
from utils.serial_handler import CameraStreamHandler

image_stream_bp = Blueprint('image_stream', __name__)
current_socket_id = None

def handle_frame(frame_data):
    """处理图像帧"""
    try:
        if current_socket_id:
            # 转换为base64并发送
            frame_base64 = base64.b64encode(frame_data).decode('utf-8')
            socketio.emit('image_frame', {
                'data': frame_base64
            }, namespace='/camera')
            print(f"发送图像成功")
    except Exception as e:
        print(f"发送图像错误: {str(e)}")

@image_stream_bp.route('/api/send_test_image', methods=['POST'])
def send_test_image():
    try:
        camera_handler = CameraStreamHandler()
        camera_handler.start(handle_frame)
        return jsonify({
            'status': 'success',
            'message': '测试图像发送成功'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@socketio.on('connect', namespace='/camera')
def handle_connect():
    global current_socket_id
    current_socket_id = request.sid
    print(f'客户端连接，SID: {current_socket_id}')

@socketio.on('disconnect', namespace='/camera')
def handle_disconnect():
    print('客户端断开连接')
