from flask import Blueprint, jsonify, request
from utils.data_manager import SerialSettingsManager

data_bp = Blueprint('data', __name__)

serial_manager = SerialSettingsManager()

@data_bp.route('/api/serial_settings', methods=['GET'])
def get_serial_settings():
    return jsonify(serial_manager.load_data())

@data_bp.route('/api/serial_settings', methods=['POST'])
def save_serial_settings():
    try:
        settings = request.json.get('serial_settings')
        if not settings:
            return jsonify({'success': False, 'message': '串口设置数据不能为空'})
        return jsonify(serial_manager.save_data(settings))
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}) 