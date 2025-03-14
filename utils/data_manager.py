import sqlite3
import json
import os
from abc import ABC, abstractmethod

class BaseDataManager(ABC):
    """数据管理基类"""
    def __init__(self, db_name):
        self.db_name = db_name
        self.db_path = self._get_db_path()
        self.init_db()

    def _get_db_path(self):
        db_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static/database')
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)
        return os.path.join(db_dir, f'{self.db_name}.db')

    @abstractmethod
    def init_db(self):
        """初始化数据库表结构"""
        pass

    @abstractmethod
    def get_default_config(self):
        """获取默认配置"""
        pass

    def load_data(self):
        """从数据库加载数据，如果没有则加载默认配置并保存"""
        try:
            data = self._load_from_db()
            if data is None:
                data = self.get_default_config()
                self.save_data(data)
            return {'success': True, 'data': data}
        except Exception as e:
            return {'success': False, 'message': str(e)}

    @abstractmethod
    def _load_from_db(self):
        """从数据库加载数据的具体实现"""
        pass

    @abstractmethod
    def save_data(self, data):
        """保存数据到数据库的具体实现"""
        pass


class SerialSettingsManager(BaseDataManager):
    """串口设置管理器"""
    def __init__(self):
        super().__init__('serial_settings')

    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS serial_settings (
            id INTEGER PRIMARY KEY,
            col_serial_settings TEXT NOT NULL
        )
        ''')
        conn.commit()
        conn.close()

    def get_default_config(self):
        """从JSON文件加载默认配置"""
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                 'static/config/serial_settings.json')
        print(config_path)
        with open(config_path, 'r') as f:
            return json.load(f)['serial_settings']

    def _load_from_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT col_serial_settings FROM serial_settings WHERE id = 1')
        result = cursor.fetchone()
        conn.close()
        return json.loads(result[0]) if result else None

    def save_data(self, data):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('INSERT OR REPLACE INTO serial_settings (id, col_serial_settings) VALUES (1, ?)',
                      (json.dumps(data),))
        conn.commit()
        conn.close()
        return {'success': True} 