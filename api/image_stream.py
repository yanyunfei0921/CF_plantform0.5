import base64
import logging
import cv2
import numpy as np
from flask import Blueprint, jsonify, request
from extensions import socketio
from utils.serial_handler import CameraStreamHandler
import time

# 创建蓝图
image_stream_bp = Blueprint('image_stream', __name__)

# 全局变量
camera_handler = None
current_socket_id = None

def handle_frame(frame_data, device_id):
    """处理图像帧的回调函数"""
    try:
        # 1. 将字节数据转换为numpy数组
        nparr = np.frombuffer(frame_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # 2. 实时显示图像
        cv2.imshow('Camera Debug Window', img)
        cv2.waitKey(1)  # 1ms延迟，不阻塞
        
        # 3. 发送数据
        frame_base64 = base64.b64encode(frame_data).decode('utf-8')
        # print(f"准备发送base64数据, 长度: {len(frame_base64)}")
        # print(f"准备发送图像，当前 socket_id: {current_socket_id}")
        if current_socket_id:
            socketio.emit('image_frame', {
                'data': frame_base64, 
                'device_id': device_id,
            }, namespace='/camera')
        
        # print("图像数据发送完成")
        
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
        device_id = data.get('device_id', 'camera')

        if camera_handler:
            camera_handler.stop(mock=mock_mode)
            
        camera_handler = CameraStreamHandler(
            port=port, 
            baudrate=baudrate,
            device_id=device_id
        )
        camera_handler.start(handle_frame, mock=mock_mode)
        
        mode_str = "模拟" if mock_mode else "实际"
        return jsonify({
            'status': 'success',
            'message': f'{mode_str}相机启动成功'
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
            camera_handler = None  # 清理实例
            
        return jsonify({
            'status': 'success',
            'message': '相机停止成功'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

@socketio.on('connect', namespace='/camera')
def handle_connect():
    global current_socket_id
    current_socket_id = request.sid
    print(f'客户端连接，当前 SID: {current_socket_id}')

@socketio.on('test_connection', namespace='/camera')
def handle_test_connection(data):
    print(f"收到测试连接消息，当前 SID: {request.sid}")
    # 验证 current_socket_id 是否与 request.sid 匹配
    print(f"存储的 current_socket_id: {current_socket_id}")
    
    # 发送测试响应
    socketio.emit('test_response', {
        'message': 'test ok',
        'server_sid': request.sid
    }, namespace='/camera')

@socketio.on('disconnect', namespace='/camera')
def handle_disconnect():
    print('[WebSocket] 客户端断开连接, SID:', request.sid)
