import base64
import logging
import cv2
import numpy as np
from flask import Blueprint, jsonify, request, current_app
from extensions import socketio
from utils.serial_handler import CameraStreamHandler
import time

# 创建蓝图
image_stream_bp = Blueprint('image_stream', __name__)

# 全局变量
camera_handler = None
connected_clients = {}  # {socket_id: device_id}

def handle_frame(frame_data, device_id):
    """处理图像帧的回调函数"""
    try:
        # 1. 将字节数据转换为numpy数组
        nparr = np.frombuffer(frame_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # 2. 实时显示图像（调试用）
        cv2.imshow('Camera Debug Window', img)
        cv2.waitKey(1)  # 1ms延迟
        
        # 3. 编码为JPEG并转换为base64
        _, buffer = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 70])
        frame_base64 = base64.b64encode(buffer).decode('utf-8')

        # 4. 发送给匹配设备的所有客户端
        app = current_app._get_current_object()
        with app.app_context():
            for sid, dev_id in connected_clients.items():
                if dev_id == device_id:
                    socketio.emit('image_frame', {
                        'data': frame_base64,
                        'device_id': device_id,
                        'timestamp': time.time()
                    }, namespace='/camera', room=sid)
                    print(f"[DEBUG] 已发送图像到设备 {device_id} (SID: {sid})")
                    
    except Exception as e:
        logging.error(f"处理图像帧错误: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())

@image_stream_bp.route('/api/start_stream', methods=['POST'])
def start_camera():
    global camera_handler
    try:
        data = request.get_json()
        port = data.get('port')
        baudrate = data.get('baudrate')
        mock_mode = data.get('mock', False)
        device_id = data.get('device_id', 'default')

        # 连接校验
        if device_id not in connected_clients.values():
            return jsonify({
                'status': 'error',
                'message': '设备未连接WebSocket'
            }), 400

        if camera_handler:
            camera_handler.stop(mock=mock_mode)
            
        # 传递应用实例到Handler
        app = current_app._get_current_object()
        camera_handler = CameraStreamHandler(
            port=port, 
            baudrate=baudrate,
            device_id=device_id,
            app=app  # 新增关键参数
        )
        camera_handler.start(handle_frame, mock=mock_mode)
        
        return jsonify({
            'status': 'start',  # 与前端期望的status字段匹配
            'message': '相机启动成功'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@image_stream_bp.route('/api/stop_stream', methods=['POST'])
def stop_camera():
    global camera_handler
    try:
        data = request.get_json()
        mock_mode = data.get('mock', False)
        
        if camera_handler:
            camera_handler.stop(mock=mock_mode)
            camera_handler = None
            
        return jsonify({
            'status': 'stop',  # 与前端期望的status字段匹配
            'message': '相机停止成功'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

# Socket.IO事件处理
@socketio.on('connect', namespace='/camera')
def handle_connect():
    device_id = request.args.get('device_id', 'default')
    connected_clients[request.sid] = device_id
    print(f'[连接] 设备ID: {device_id}, SID: {request.sid}')

@socketio.on('disconnect', namespace='/camera')
def handle_disconnect():
    if request.sid in connected_clients:
        del connected_clients[request.sid]
    print(f'[断开] SID: {request.sid}')