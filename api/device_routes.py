from flask import Blueprint, request, jsonify, current_app
from utils.device_manager import DeviceManager, LightSourceDevice
from time import sleep

# 创建蓝图
device_bp = Blueprint('device', __name__)

def get_device_manager():
    if not hasattr(current_app, 'device_manager'):
        current_app.device_manager = DeviceManager()
    return current_app.device_manager

@device_bp.route('/api/connect_device', methods=['POST'])
def connect_device():
    try:
        data = request.json
        device_name = data['device_name']
        settings = data['settings']
        print(device_name)
        print(settings)
        # 如果设备不存在，先添加设备
        device_manager = get_device_manager()
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
        device_manager = get_device_manager()
        device_manager.disconnect_device(device_name)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@device_bp.route('/api/devices_status', methods=['GET'])
def get_devices_status():
    try:
        device_manager = get_device_manager()
        status = device_manager.get_all_devices_status()
        return jsonify({'success': True, 'data': status})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@device_bp.route('/api/device_status/<device_name>', methods=['GET'])
def get_device_status(device_name):
    try:
        device_manager = get_device_manager()
        status = device_manager.get_device_status(device_name)
        return jsonify({'success': True, 'data': {'is_connected': status}})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@device_bp.route('/api/control_composite_device', methods=['POST'])
def control_composite_device():
    device_manager = get_device_manager()
    data = request.json
    device_type = data.get('device_type')
    value = data.get('value', 0)
    
    try:
        # 检查复合光源设备是否存在且已连接（这里有个bug）
        if 'light_source' not in device_manager.devices:
            return jsonify(success=False, message="复合光源设备未添加")
        
        light_source = device_manager.devices['light_source']
        # motor_three_axis = device_manager.devices['motor_three_axis']
        if not light_source.is_connected:
            return jsonify(success=False, message="复合光源设备未连接")

        if device_type == 'indicationLaser':
            # motor_three_axis.set_motor_position(value)
            success = light_source.set_indication_laser_power(value)
        elif device_type == 'blackBody':
            success = light_source.set_black_body_temperature(value)
        elif device_type == 'visibleLight':
            success = light_source.set_visible_light(value)
        else:
            return jsonify(success=False, message="未知设备类型")
        
        return jsonify(success=success, message="操作成功")
            
    except Exception as e:
        print(f"控制复合光源设备出错: {str(e)}")
        # 不要在异常处理中改变设备状态
        return jsonify(success=False, message=f"操作异常: {str(e)}")
    
@device_bp.route('/api/control_laser_1064nm', methods=['POST'])
def control_laser_1064nm():
    device_manager = get_device_manager()
    data = request.json
    power = data.get('power', 0)
    frequency = data.get('frequency', 0)
    pulse_width = data.get('pulse_width', 0)
    operation_type = data.get('operation_type', 'toggle')
    try:
        laser_1064nm = device_manager.devices['laser_1064nm']
        if not laser_1064nm.is_connected:
            return jsonify(success=False, message="激光器未连接")
        if operation_type == 'toggle':
            laser_1064nm.reset_receive_stack()
            sleep(0.1)
            laser_1064nm.set_laser_power(power)
            sleep(0.1)
            laser_1064nm.set_laser_frequency(frequency)
            sleep(0.1)
            laser_1064nm.set_laser_pulse_width(pulse_width)
            return jsonify(success=True, message="操作成功")
        elif operation_type == 'power':
            laser_1064nm.set_laser_power(power)
            return jsonify(success=True, message="操作成功")
        elif operation_type == 'frequency':
            laser_1064nm.set_laser_frequency(frequency)
            return jsonify(success=True, message="操作成功")
        elif operation_type == 'pulse_width':
            laser_1064nm.set_laser_pulse_width(pulse_width)
        return jsonify(success=True, message="操作成功")
    except Exception as e: 
        return jsonify(success=False, message=f"操作异常: {str(e)}")
        
@device_bp.route('/api/get_laser_temperature', methods=['GET'])
def get_laser_temperature():
    device_manager = get_device_manager()
    laser_1064nm = device_manager.devices['laser_1064nm']
    if not laser_1064nm.is_connected:
        return jsonify(success=False, message="激光器未连接")
    temperature = laser_1064nm.get_laser_temperature()
    return jsonify(success=True, message="操作成功", temperature=temperature)

