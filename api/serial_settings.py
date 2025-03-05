from flask import Blueprint, jsonify, request
import sqlite3
import json
import os

# 创建蓝图
serial_settings_bp = Blueprint('serial_settings', __name__)

# 获取数据库路径的辅助函数
def get_db_path():
    db_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static/database')
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)
    return os.path.join(db_dir, 'serial_settings.db')

# 获取串口设置
@serial_settings_bp.route('/api/serial_settings', methods=['GET'])
def get_serial_settings():
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT settings FROM serial_settings WHERE id = 1')
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return jsonify({
                'success': True,
                'settings': json.loads(result[0])
            })
        else:
            return jsonify({
                'success': False,
                'message': '未找到串口配置'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })

# 保存串口设置
@serial_settings_bp.route('/api/serial_settings', methods=['POST'])
def save_serial_settings():
    try:
        settings = request.json.get('settings')
        if not settings:
            return jsonify({
                'success': False,
                'message': '串口设置数据不能为空'
            })
        
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM serial_settings WHERE id = 1')
        if cursor.fetchone():
            cursor.execute('UPDATE serial_settings SET settings = ? WHERE id = 1', 
                          (json.dumps(settings),))
        else:
            cursor.execute('INSERT INTO serial_settings (id, settings) VALUES (1, ?)', 
                          (json.dumps(settings),))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }) 