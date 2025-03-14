from abc import ABC, abstractmethod
import threading
import serial
import time
import queue
from typing import Dict, Any

class BaseDevice(ABC):
    def __init__(self, device_name: str, settings: Dict[str, Any]):
        self.device_name = device_name
        self.settings = settings
        self.serial = None
        self.is_connected = False
        self.should_stop = False
        self.comm_thread = None
        self.heartbeat_thread = None
        # 分开心跳和普通命令的队列
        self.heartbeat_command_queue = queue.Queue()
        self.heartbeat_response_queue = queue.Queue()
        self.normal_command_queue = queue.Queue()
        self.normal_response_queue = queue.Queue()
        
        self._lock = threading.Lock()

    @abstractmethod
    def process_command(self, command: bytes) -> bool:
        """处理具体设备的命令"""
        pass

    @abstractmethod
    def get_heartbeat_command(self) -> bytes:
        """获取心跳包命令"""
        pass

    @abstractmethod
    def verify_heartbeat_response(self, response: bytes) -> bool:
        """验证心跳包响应"""
        pass

    def connect(self) -> bool:
        """连接设备"""
        try:
            self.serial = serial.Serial(
                # port=self.settings['port'],
                port='COM11',    
                baudrate=int(self.settings['baudrate']),
                bytesize=int(self.settings['databits']),
                stopbits=float(self.settings['stopbits']),
                parity=serial.PARITY_NONE if self.settings['parity'].lower() == 'none' else self.settings['parity'],
                timeout=float(self.settings['timeout'])
            )
            self.is_connected = True
            self.should_stop = False
            
            # 启动通信线程
            self.comm_thread = threading.Thread(target=self._communication_loop)
            self.comm_thread.daemon = True
            self.comm_thread.start()

            # 第一次心跳检测后连接成功
            time.sleep(5)
            print("开始第一次心跳检测")
            try:
                heartbeat_cmd = self.get_heartbeat_command()
                self.heartbeat_command_queue.put(heartbeat_cmd)
                response = self.heartbeat_response_queue.get(timeout=2)
                if not self.verify_heartbeat_response(response):
                    self.disconnect()
                    return False
            except Exception as e:
                print(f"第一次心跳检测失败 {self.device_name}: {str(e)}")
                self.disconnect()
                return False

            # 启动心跳线程
            self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop)
            self.heartbeat_thread.daemon = True
            self.heartbeat_thread.start()

            return True
        except Exception as e:
            print(f"连接设备 {self.device_name} 失败: {str(e)}")
            self.is_connected = False
            return False

    def disconnect(self):
        """断开设备连接"""
        print(f"准备断开设备 {self.device_name} 连接")
        
        # 先设置标志位
        self.should_stop = True
        self.is_connected = False
        
        # 直接关闭串口，不等待锁
        if self.serial:
            try:
                self.serial.close()
                print(f"串口已关闭")
            except Exception as e:
                print(f"关闭串口时出错: {str(e)}")

    def _communication_loop(self):
        """通信线程主循环"""
        while not self.should_stop:
            try:
                heartbeat_command = None
                normal_command = None
                
                # 优先处理心跳命令，不持有锁
                if not self.heartbeat_command_queue.empty():
                    heartbeat_command = self.heartbeat_command_queue.get(block=False)
                # 其次处理普通命令
                elif not self.normal_command_queue.empty():
                    normal_command = self.normal_command_queue.get(block=False)
                    
                # 处理心跳命令
                if heartbeat_command:
                    with self._lock:
                        if self.serial and self.serial.is_open:
                            self.serial.write(heartbeat_command)
                            response = self.serial.readline()
                            self.heartbeat_response_queue.put(response)
                
                # 处理普通命令
                elif normal_command:
                    with self._lock:
                        if self.serial and self.serial.is_open:
                            self.serial.write(normal_command)
                            response = self.serial.readline()
                            self.normal_response_queue.put(response)
                            
                time.sleep(0.01)
            except queue.Empty:
                # 队列为空，继续循环
                pass
            except Exception as e:
                print(f"通信错误 {self.device_name}: {str(e)}")
                self.is_connected = False
                break

    def _heartbeat_loop(self):
        """心跳检测线程主循环"""
        while not self.should_stop:
            try:
                if not self.is_connected:
                    time.sleep(0.1)
                    continue
                    
                # 清空响应队列，避免处理旧响应
                while not self.heartbeat_response_queue.empty():
                    try:
                        self.heartbeat_response_queue.get(block=False)
                    except queue.Empty:
                        break
                    
                # 发送心跳命令
                heartbeat_cmd = self.get_heartbeat_command()
                self.heartbeat_command_queue.put(heartbeat_cmd)
                
                # 等待响应
                print(self.heartbeat_command_queue)
                response = self.heartbeat_response_queue.get(timeout=2)
                print(f"[{self.device_name}] 收到心跳响应: {response.hex()}")
                if not self.verify_heartbeat_response(response):
                    self.disconnect()
                    break
                    
                time.sleep(10)  # 心跳间隔1秒
                
            except Exception as e:
                print(f"心跳检测失败 {self.device_name}: {str(e)}")
                self.disconnect()
                break

    # 发送普通命令的方法
    def send_command(self, command: bytes) -> bytes:
        """发送命令并等待响应"""
        self.normal_command_queue.put(command)
        return self.normal_response_queue.get(timeout=2)

# 具体设备实现
class LightSourceDevice(BaseDevice):
    def process_command(self, command: bytes) -> bool:
        # 实现光源设备的具体命令处理
        pass

    def get_heartbeat_command(self) -> bytes:
        # 返回光源设备的心跳命令
        return b'\x01\x03\x00\x00\x00\x01\x84\x0A'

    def verify_heartbeat_response(self, response: bytes) -> bool:
        # 验证光源设备的心跳响应
        return len(response) >= 5 and response[0] == 0x01
    
    def set_laser_power(self, power: int) -> bool:
        # 设置激光功率，0000-1000，*1000!为最大功率打开
        if(power < 0 or power > 1000):
            return False
        else:
            command = f"*{power:04d}!"
            if(self.send_command(command.endcode()) == b"*1000!"):
                return True
            else:
                return False
            
    def set_visible_light(self, light: int) -> bool:
        # 设置可见光亮度，0000-0500，*0500@为最大亮度打开
        if(light < 0 or light > 500):
            return False
        else:
            command = f"*{light:04d}@"
            return self.send_command(command.endcode()) == b"*0500@"
        

    def set_black_body_temperature(self, temperature: int) -> bool:
        # 设置黑体温度，000000-040000，*040000#为最大温度打开
        if(temperature < 0 or temperature > 40000):
            return False
        else:
            command = f"*{temperature:06d}#"
            response  = self.send_command(command.endcode())
            response_str = response.decode()
            if(len(response_str == 15 and response_str[0] == '*' and response_str[-1] == '#')):
                return True
            else:
                return False
            
    def get_black_body_temperature(self, ctrl_temperature: int) -> float:
        # 获取黑体温度
        command = f"*{ctrl_temperature:06d}#"
        response = self.send_command(command.endcode())
        response_str = response.decode()
        if(len(response_str == 15 and response_str[0] == '*' and response_str[-1] == '#')):
            if(response_str[8] == "H"):
                real_temperature = int(response_str[9:15])/1000
            elif(response_str[8] == "L"):
                real_temperature = -int(response_str[9:15])/1000
            else:
                return False
        return real_temperature



class CCDCameraDevice(BaseDevice):
    def process_command(self, command: bytes) -> bool:
        # 实现CCD相机的具体命令处理
        pass

    def get_heartbeat_command(self) -> bytes:
        # 返回CCD相机的心跳命令
        return b'\x02\x03\x00\x00\x00\x01\x84\x0A'

    def verify_heartbeat_response(self, response: bytes) -> bool:
        # 验证CCD相机的心跳响应
        return len(response) >= 5 and response[0] == 0x02

# 设备管理器
class DeviceManager:
    def __init__(self):
        self.devices: Dict[str, BaseDevice] = {}

    def add_device(self, device_name: str, settings: Dict[str, Any]) -> bool:
        """添加并初始化设备"""
        device_type = settings.get('device_type', '')
        if device_type == 'light_source':
            device = LightSourceDevice(device_name, settings)
        elif device_type == 'ccd_camera':
            device = CCDCameraDevice(device_name, settings)
        else:
            return False

        self.devices[device_name] = device
        return True

    def connect_device(self, device_name: str) -> bool:
        """连接指定设备"""
        if device_name in self.devices:
            return self.devices[device_name].connect()
        return False

    def disconnect_device(self, device_name: str):
        """断开指定设备"""
        if device_name in self.devices:
            self.devices[device_name].disconnect()

    def get_device_status(self, device_name: str) -> bool:
        """获取设备连接状态"""
        if device_name in self.devices:
            return self.devices[device_name].is_connected
        return False

    def get_all_devices_status(self) -> Dict[str, bool]:
        """获取所有设备的状态"""
        return {name: device.is_connected 
                for name, device in self.devices.items()}