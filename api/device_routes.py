from flask import Blueprint, request, jsonify
from utils.device_manager import DeviceManager, LightSourceDevice

# 创建蓝图
device_bp = Blueprint('device', __name__)

# 创建设备管理器实例
device_manager = DeviceManager()

@device_bp.route('/api/connect_device', methods=['POST'])
def connect_device():
    try:
        data = request.json
        device_name = data['device_name']
        settings = data['settings']
        
        # 如果设备不存在，先添加设备
        if device_name not in device_manager.devices:
            if not device_manager.add_device(device_name, settings):
                return jsonify({'success': False, 'message': '不支持的设备类型'})
        
        # 连接设备
        success = device_manager.connect_device(device_name)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@device_bp.route('/api/disconnect_device', methods=['POST'])
def disconnect_device():
    try:
        device_name = request.json['device_name']
        device_manager.disconnect_device(device_name)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@device_bp.route('/api/devices_status', methods=['GET'])
def get_devices_status():
    try:
        status = device_manager.get_all_devices_status()
        return jsonify({'success': True, 'data': status})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@device_bp.route('/api/device_status/<device_name>', methods=['GET'])
def get_device_status(device_name):
    try:
        status = device_manager.get_device_status(device_name)
        return jsonify({'success': True, 'data': {'is_connected': status}})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@device_bp.route('/api/set_laser_power', methods=['POST'])
def set_laser_power():
    try:
        data = request.json
        power = data.get('power', 0)
        
        # 获取光源设备
        light_source = None
        for device in device_manager.devices.values():
            if isinstance(device, LightSourceDevice):
                light_source = device
                break
        
        if not light_source:
            return jsonify({'success': False, 'message': '未找到光源设备'})
            
        if not light_source.is_connected:
            return jsonify({'success': False, 'message': '光源设备未连接'})
        
        # 设置激光功率
        success = light_source.set_laser_power(power)
        
        return jsonify({
            'success': success,
            'message': '设置成功' if success else '设置失败'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})