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
                port=self.settings['port'],
                # port='COM11',    
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
            # try:
            #     heartbeat_cmd = self.get_heartbeat_command()
            #     self.heartbeat_command_queue.put(heartbeat_cmd)
            #     response = self.heartbeat_response_queue.get(timeout=2)
            #     if not self.verify_heartbeat_response(response):
            #         self.disconnect()
            #         return False
            # except Exception as e:
            #     print(f"第一次心跳检测失败 {self.device_name}: {str(e)}")
            #     self.disconnect()
            #     return False

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
                    heartbeat_command = self.heartbeat_command_queue.get(block=True, timeout=0.1)
                # 其次处理普通命令
                elif not self.normal_command_queue.empty():
                    normal_command = self.normal_command_queue.get(block=True, timeout=0.1)
                    
                # 处理心跳命令
                if heartbeat_command:
                    with self._lock:
                        if self.serial and self.serial.is_open:
                            print(f"Sending heartbeat: {heartbeat_command}")
                            self.serial.write(heartbeat_command)
                            time.sleep(0.1)  # 给设备响应的时间
                            response = b''
                            while self.serial.in_waiting:  # 只要有数据就继续读
                                response += self.serial.read(self.serial.in_waiting)
                            print(f"Heartbeat response: {response}")
                            self.heartbeat_response_queue.put(response)
                
                # 处理普通命令
                elif normal_command:
                    with self._lock:
                        if self.serial and self.serial.is_open:
                            print(f"Sending command: {normal_command}")
                            self.serial.write(normal_command)
                            time.sleep(0.1)  # 给设备响应的时间
                            response = b''
                            # 添加超时和重试机制
                            max_attempts = 5
                            attempt = 0
                            while attempt < max_attempts:
                                attempt += 1
                                
                                # 给设备一点处理时间
                                time.sleep(0.05)
                                
                                # 读取可用数据
                                if self.serial.in_waiting:
                                    response += self.serial.read(self.serial.in_waiting)
                                    # 如果已经接收到有效数据，可以提前结束
                                    if response:
                                        break
                            print(f"Command response (hex): {response.hex() if response else 'Empty'}")
                            self.normal_response_queue.put(response)
                            
                time.sleep(0.01)
            except queue.Empty:
                # 队列为空，继续循环
                continue
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
                    
                # # 发送心跳命令
                # heartbeat_cmd = self.get_heartbeat_command()
                # self.heartbeat_command_queue.put(heartbeat_cmd)
                
                # # 等待响应
                # print(self.heartbeat_command_queue)
                # response = self.heartbeat_response_queue.get(timeout=2)
                # print(f"[{self.device_name}] 收到心跳响应: {response.hex()}")
                # if not self.verify_heartbeat_response(response):
                #     self.disconnect()
                #     break
                    
                time.sleep(10)  # 心跳间隔1秒
                
            except Exception as e:
                print(f"心跳检测失败 {self.device_name}: {str(e)}")
                self.disconnect()
                break

    # 发送普通命令的方法
    def send_command(self, command: bytes) -> bytes:
        """发送命令并等待响应"""
        try:
            print(f"Sending command (bytes): {[hex(b) for b in command]}")
            self.normal_command_queue.put(command)
            
            # 增加超时时间到2秒，并添加异常处理
            try:
                response = self.normal_response_queue.get(timeout=2)
                print(f"Received response (bytes): {[hex(b) for b in response]}")
                return response
            except queue.Empty:
                print("Error: Response timeout")
                return None
                
        except Exception as e:
            print(f"Error in send_command: {str(e)}")
            return None

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
    
    def set_indication_laser_power(self, power: int) -> bool:
        # 设置激光功率，0000-1000，*1000@为最大功率打开
        print(power)
        if(power < 0 or power > 1000):
            print("功率范围错误")
            return False
        else:
            command = f"*{power:04d}@"
            result = self.send_command(command.encode())
            # print(result)
            if(result == command.encode()):
                print("成功")
                return True
            else:
                print("失败")
                return False
            
    def set_visible_light(self, light: int) -> bool:
        # 设置可见光亮度，0000-0100，*0100!为最大亮度打开
        if(light < 0 or light > 100):
            print("亮度范围错误")
            return False
        else:
            command = f"*{light:04d}!"
            result = self.send_command(command.encode())
            if result == command.encode():
                print("成功")
                return True
            else:
                print("失败")
                return False
        

    def set_black_body_temperature(self, temperature: int) -> bool:
        # 设置黑体温度，000000-040000，*040000#为最大温度打开
        if(temperature < 0 or temperature > 40000):
            return False
        else:
            command = f"*{temperature:06d}#"
            response  = self.send_command(command.encode())
            response_str = response.decode()
            print("走到这里了")
            print(response_str)
            if(len(response_str) == 15 and response_str[0] == '*' and response_str[-1] == '#'):
                return True
            else:
                return False
            
    def get_black_body_temperature(self, ctrl_temperature: int) -> float:
        # 获取黑体温度
        command = f"*{ctrl_temperature:06d}#"
        response = self.send_command(command.encode())
        response_str = response.decode()
        if(len(response_str) == 15 and response_str[0] == '*' and response_str[-1] == '#'):
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

class Laser1064nm(BaseDevice):
    def process_command(self, command: bytes) -> bool:
        # 实现激光1064nm的具体命令处理
        pass

    def get_heartbeat_command(self) -> bytes:
        # 返回激光1064nm的心跳命令
        return b'\x03\x03\x00\x00\x00\x01\x84\x0A'
    
    def verify_heartbeat_response(self, response: bytes) -> bool:
        # 验证激光1064nm的心跳响应
        return len(response) >= 5 and response[0] == 0x03

    # 关于激光器的所有设置成功后均有响声提示
    def reset_receive_stack(self) -> bool:
        # 接收堆栈清零，该指令重复发送直至响应或超时
        command = b'\x93'
        
        # 设置超时时间和开始时间
        timeout = 2.0  # 2秒超时
        start_time = time.time()
        
        # 循环发送命令直到收到正确返回值或超时
        while (time.time() - start_time) < timeout:
            response = self.send_command(command)
            
            # 检查返回值是否为0x5d
            if response and len(response) > 0 and response[0] == 0x5d:
                return True
            
            # 等待0.01秒后重试
            time.sleep(0.01)
        
        # 超过2秒未收到预期返回值
        return False

    def set_laser_power(self, power: int) -> bool:
        # 设置激光功率，范围0-100mW
        if power < 0 or power > 100:
            print("激光功率超出范围")
            return False
        else:
            # 命令采用小端，低位在前
            command = b'\x57' + power.to_bytes(2, 'little') + b'\x51'
            response = self.send_command(command)
            if response == b'\x57':
                return True
            else:
                return False
    
    def set_laser_frequency(self, frequency):
        """
        设置激光器重频
        
        Args:
            frequency: 期望设置的频率(Hz)
            
        Returns:
            bool: 操作是否成功
        """
        if frequency < 1 or frequency > 500000:
            print("激光重频超出范围")
            return False
        try:
            # 确定频率代表值和调整后的合法频率
            freq_code = 1  # 默认值
            adjusted_freq = frequency  # 调整后的频率
            
            # 1-50Hz: 代表值与频率相同
            if 1 <= frequency <= 50:
                freq_code = int(frequency)
                adjusted_freq = int(frequency)
            
            # 55-100Hz: 以5Hz为步进，代表值51-60
            elif 51 < frequency <= 100:
                # 找到最接近的5的倍数
                adjusted_freq = round(frequency / 5) * 5
                # 确保在55-100的范围内
                adjusted_freq = max(55, min(100, adjusted_freq))
                # 计算代表值: 51 + (freq - 55) / 5
                freq_code = 51 + (adjusted_freq - 55) // 5
            
            # 150-1000Hz: 以50Hz为步进，代表值61-78
            elif 101 < frequency <= 1000:
                # 找到最接近的50的倍数
                adjusted_freq = round(frequency / 50) * 50
                # 确保在150-1000的范围内
                adjusted_freq = max(150, min(1000, adjusted_freq))
                # 计算代表值: 61 + (freq - 150) / 50
                freq_code = 61 + (adjusted_freq - 150) // 50
            
            # 2000-10000Hz: 以1000Hz为步进，代表值79-87
            elif 1001 < frequency <= 10000:
                # 找到最接近的1000的倍数
                adjusted_freq = round(frequency / 1000) * 1000
                # 确保在2000-10000的范围内
                adjusted_freq = max(2000, min(10000, adjusted_freq))
                # 计算代表值: 79 + (freq - 2000) / 1000
                freq_code = 79 + (adjusted_freq - 2000) // 1000
            
            # 20k-50kHz: 以10kHz为步进，代表值88-91
            elif 10001 < frequency <= 50000:
                # 找到最接近的10000的倍数
                adjusted_freq = round(frequency / 10000) * 10000
                # 确保在20000-50000的范围内
                adjusted_freq = max(20000, min(50000, adjusted_freq))
                # 计算代表值: 88 + (freq - 20000) / 10000
                freq_code = 88 + (adjusted_freq - 20000) // 10000
            
            # 特殊频率
            elif 50001 < frequency <= 75000:  # 接近50kHz
                freq_code = 91
                adjusted_freq = 100000
            elif 75001 < frequency <= 150000:  # 接近100kHz
                freq_code = 92
                adjusted_freq = 100000
            elif 150001 < frequency <= 300000:  # 接近200kHz
                freq_code = 93
                adjusted_freq = 200000
            elif 300001 < frequency <= 450000:  # 接近400kHz
                freq_code = 94
                adjusted_freq = 400000
            elif frequency > 450000:  # 接近500kHz或更高
                freq_code = 95
                adjusted_freq = 500000
            else:  # 频率太低，使用最小值
                freq_code = 1
                adjusted_freq = 1
            
            # 构建命令
            command = b'\x65' + freq_code.to_bytes(2, 'little') + b'\x6a'
            
            # 记录日志
            print(f"设置激光器频率: 输入={frequency}Hz, 调整为={adjusted_freq}Hz, 代表值={freq_code}")
            
            # 发送命令
            response = self.send_command(command)
            if response == b'\x65':
                return True
            else:
                return False
        
        except Exception as e:
            print(f"设置激光器频率失败: {str(e)}")
            return False

    def set_laser_pulse_width(self, pulse_width: int) -> bool:
        # 设置激光脉宽，范围为10-100
        if pulse_width < 10 or pulse_width > 100:   
            print("激光脉宽超出范围")
            return False
        else:
            command = b'\xa5'+pulse_width.to_bytes(2, 'little')+b'\x5a'
            response = self.send_command(command)
            if response == b'\xa5':
                return True
            else:
                return False
    
    def set_driver_board_working_current(self, current: int) -> bool:
        # 设置驱动板工作电流，范围0-60
        if current < 0 or current > 60:
            print("驱动板工作电流超出范围")
            return False
        else:
            command = b'\xa6'+current.to_bytes(2, 'little')+'\x6b'
            response = self.send_command(command)
            if response == b'\xa6':
                return True
            else:
                return False
    
    def get_laser_temperature(self) -> float:
        # 发送获取温度命令
        command = bytes([0x28, 0x00, 0x00, 0x12])
        response = self.send_command(command)
        
        # 处理返回值，将字节数据转换为实际温度
        if response and len(response) >= 2:
            # 按小端序解析温度值: 第一个字节为低位，第二个字节为高位
            temp_low = response[0]  # 例如 0xC6
            temp_high = response[1]  # 例如 0x09
            
            # 组合成16位整数 (高位*256 + 低位)
            temp_raw = (temp_high << 8) | temp_low  # 例如 0x09C6
            
            # 计算实际温度值 (精度0.01°C)
            temperature = temp_raw / 100.0  # 例如 25.02°C
            
            return temperature
        
        # 如果无法解析，返回原始响应
        return None
    
    def set_VOA(self, VOA: int) -> bool:
        # 设置激光器衰减，范围0-500，500为50dB
        if VOA < 0 or VOA > 500:
            print("VOA超出范围")
            return False
        else:
            command = '\x58'+VOA.to_bytes(2, 'little')+'\x51'
            response = self.send_command(command)
            if response == b'\x58':
                return True
            else:
                return False
    

    

class MotorThreeAxisDevice(BaseDevice):
    def _verify_response_format(self, response: bytes) -> bool:
    # 检查最小长度：0xFF + /0 + S + 0x03 + \r\n + 0xFF = 8字节
        if len(response) < 8:
            return False
        
        # 检查起始和结束标记
        if not (response.startswith(b'\xFF') and response.endswith(b'\xFF')):
            return False
            
        # 检查基本格式：/0 + S 在正确位置
        if not (response[1:3] == b'/0' and response[3:4] == b'S'):
            return False
            
        # 检查数据结束标记和换行符
        if not (b'\x03\r\n' in response):
            return False
            
        return True
    
    def _extract_response_data(self, response: bytes) -> str:
        try:
            # 数据在S之后，0x03之前
            start_idx = response.index(b'S') + 1
            end_idx = response.index(b'\x03')
            return response[start_idx:end_idx].decode('ascii')
        except:
            return ""
        
    def process_command(self, command: bytes) -> bool:
        # 实现电机三轴的具体命令处理
        if not command.startswith(b'/1'):
            return False
        response = self.send_command(command)
        return self._verify_response_format(response)

    def get_heartbeat_command(self) -> bytes:
        pass
    
    def verify_heartbeat_response(self, response: bytes) -> bool:
        pass

    def set_horizontal_axis_pos(self, position: int) -> bool:
        # 设置电机水平运动到绝对位置
        command = f"/1aM1A{position}R\r".encode()
        response = self.send_command(command)
        return self._verify_response_format(response)

    def set_vertical_axis_pos(self, position: int) -> bool:
        # 设置电机垂直运动到绝对位置
        command = f"/1aM1A{position}R\r".encode()
        response = self.send_command(command)
        return self._verify_response_format(response)

    def set_target_wheel_pos(self, position: int) -> bool:
        # 设置靶轮运动到绝对位置 (轴3)
        command = f"/1aM3A{position}R\r".encode()
        response = self.send_command(command)
        return self._verify_response_format(response)
    
    def set_horizontal_axis_relative_pos(self, position: int) -> bool:
        # 设置电机水平运动到相对位置
        command = f"/1aM1P{position}R\r".encode()
        response = self.send_command(command)
        return self._verify_response_format(response)

    def set_vertical_axis_relative_pos(self, position: int) -> bool:
        # 设置电机垂直运动到相对位置
        command = f"/1aM2P{position}R\r".encode()
        response = self.send_command(command)
        return self._verify_response_format(response)
    
    def set_target_wheel_relative_pos(self, position: int) -> bool:
        # 设置靶轮运动到相对位置 (轴3)
        command = f"/1aM3P{position}R\r".encode()
        response = self.send_command(command)
        return self._verify_response_format(response)
    
    def light_source_positioning(self) -> bool:
        # 复合光源移动到焦平面中心
        horizontal_pos = 
        self.set_horizontal_axis_pos()

    def get_horizontal_axis_pos(self) -> int:
        # 获取电机水平运动位置
        command = b"/1aM1?\r"
        response = self.send_command(command)
        if not self._verify_response_format(response):
            return -1
        
        data = self._extract_response_data(response)
        try:
            return int(data)
        except:
            return -1

    def get_vertical_axis_pos(self) -> int:
        # 获取电机垂直运动位置
        command = b"/1aM2?\r"
        response = self.send_command(command)
        if not self._verify_response_format(response):
            return -1
            
        data = self._extract_response_data(response)
        try:
            return int(data)
        except:
            return -1 
    
    def get_target_wheel_pos(self) -> int:
        # 获取靶轮当前位置 (轴3)
        command = b"/1aM3?\r"
        response = self.send_command(command)
        if not self._verify_response_format(response):
            return -1
        
        data = self._extract_response_data(response)
        try:
            return int(data)
        except:
            return -1


# 设备管理器
class DeviceManager:
    def __init__(self):
        self.devices: Dict[str, BaseDevice] = {}

    def add_device(self, device_name: str, settings: Dict[str, Any]) -> bool:
        """添加并初始化设备"""
        device_type = settings.get('device_type', '')
        print(device_type)
        if device_type == 'light_source':
            device = LightSourceDevice(device_name, settings)
        elif device_type == 'ccd_camera':
            device = CCDCameraDevice(device_name, settings)
        elif device_type == 'motor_three_axis':
            device = MotorThreeAxisDevice(device_name, settings)
        elif device_type == 'laser_1064nm':
            device = Laser1064nm(device_name, settings)
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