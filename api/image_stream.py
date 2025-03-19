from flask import Blueprint, request, jsonify
from extensions import socketio
from utils.camera_stream import CameraManager

# 创建蓝图
image_stream_bp = Blueprint('image_stream', __name__)

# 创建相机管理器实例
camera_manager = CameraManager()

# SocketIO 事件处理
@socketio.on('connect', namespace='/camera')
def handle_connect():
    print("客户端已连接")

@socketio.on('disconnect', namespace='/camera')
def handle_disconnect():
    print("客户端已断开")
    # 断开连接时停止所有相机
    for camera_id in list(camera_manager.cameras.keys()):
        camera_manager.get_camera(camera_id).stop_continuous_capture()

@socketio.on('start_stream', namespace='/camera')
def handle_start_stream(data):
    camera_id = data.get('camera_id', 'pod')  # 默认使用 pod 相机
    
    def emit_frame_callback(frame_data, cam_id):
        try:
            socketio.emit(f'camera_{cam_id}_frame', frame_data, namespace='/camera')
        except Exception as e:
            print(f"发送图像错误: {str(e)}")
    
    camera = camera_manager.get_camera(camera_id)
    camera.start_continuous_capture(emit_frame_callback)
    return {'success': True, 'message': f'开始 {camera_id} 相机流'}

@socketio.on('stop_stream', namespace='/camera')
def handle_stop_stream(data):
    camera_id = data.get('camera_id', 'pod')
    camera = camera_manager.get_camera(camera_id)
    camera.stop_continuous_capture()
    return {'success': True, 'message': f'停止 {camera_id} 相机流'}

@socketio.on('set_algorithm', namespace='/camera')
def handle_set_algorithm(data):
    camera_id = data.get('camera_id', 'pod')
    algorithm = data.get('algorithm')
    
    if algorithm:
        camera = camera_manager.get_camera(camera_id)
        camera.set_algorithm(algorithm)
        return {'success': True, 'message': f'设置 {camera_id} 相机算法为 {algorithm}'}
    return {'success': False, 'message': '缺少必要参数'}

@socketio.on('set_centroid_display', namespace='/camera')
def handle_set_centroid_display(data):
    camera_id = data.get('camera_id', 'pod')
    enabled = data.get('enabled', True)
    
    camera = camera_manager.get_camera(camera_id)
    camera.enable_centroid_detection(enabled)
    return {'success': True, 'message': f'设置 {camera_id} 相机质心显示为 {enabled}'}

@socketio.on('set_crosshair_display', namespace='/camera')
def handle_set_crosshair_display(data):
    camera_id = data.get('camera_id', 'pod')
    enabled = data.get('enabled', True)
    
    camera = camera_manager.get_camera(camera_id)
    camera.enable_crosshair(enabled)
    return {'success': True, 'message': f'设置 {camera_id} 相机十字线显示为 {enabled}'}

# RESTful API 路由
@image_stream_bp.route('/api/cameras', methods=['GET'])
def get_cameras():
    camera_list = list(camera_manager.cameras.keys())
    return jsonify({'success': True, 'data': camera_list})

@image_stream_bp.route('/api/camera/<camera_id>/settings', methods=['GET'])
def get_camera_settings(camera_id):
    camera = camera_manager.get_camera(camera_id)
    settings = {
        'algorithm': camera.algorithm_type,
        'draw_centroid': camera.draw_centroid,
        'draw_crosshair': camera.draw_crosshair
    }
    return jsonify({'success': True, 'data': settings})