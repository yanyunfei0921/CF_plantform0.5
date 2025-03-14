import threading
import time
import numpy as np
import cv2
import base64
from utils.spot_centroid import SpotCentroid

class CameraStreamHandler:
    def __init__(self, camera_id="default"):
        self.camera_id = camera_id
        self.is_running = False
        self.capture_thread = None
        # 图像参数
        self.width = 1280
        self.height = 1024
        # 光斑参数
        self.sigma = 30
        self.amplitude = 200
        self.center_x = self.width // 2
        self.center_y = self.height // 2
        self.time = 0
        self.noise_level = 5
        
        # 质心算法参数
        self.algorithm_type = "weighted"  # 默认加权质心法
        self.draw_centroid = True  # 是否绘制质心，默认绘制
        self.draw_crosshair = True  # 是否绘制十字线，默认绘制
        
        # 创建质心定位对象
        self.centroid_detector = SpotCentroid(method=self.algorithm_type)
        
    def set_algorithm(self, algorithm_type):
        """设置质心计算算法"""
        # 直接使用前端传来的算法名称
        self.algorithm_type = algorithm_type
        self.centroid_detector = SpotCentroid(method=algorithm_type)
        print(f"质心算法设置为: {algorithm_type}")
        
    def enable_centroid_detection(self, enable=True):
        """启用或禁用质心绘制"""
        self.draw_centroid = enable
        print(f"质心绘制: {'启用' if enable else '禁用'}")

    def enable_crosshair(self, enable=True):
        """启用或禁用中心十字线绘制"""
        self.draw_crosshair = enable
        print(f"中心十字线绘制: {'启用' if enable else '禁用'}")

    def get_frame(self):
        """生成带有移动高斯光斑的图像帧，后续需换成串口通信获得的图像"""
        try:
            # 生成坐标网格
            x = np.linspace(0, self.width-1, self.width)
            y = np.linspace(0, self.height-1, self.height)
            X, Y = np.meshgrid(x, y)

            # 计算光斑中心位置
            radius = 20
            self.time += 0.1
            dx = radius * np.cos(self.time)
            dy = radius * np.sin(self.time)
            center_x = self.center_x + dx
            center_y = self.center_y + dy

            # 生成高斯光斑
            gaussian = self.amplitude * np.exp(
                -((X - center_x) ** 2 + (Y - center_y) ** 2) / (2 * self.sigma ** 2)
            )

            # 添加背景噪声
            noise = np.random.normal(0, self.noise_level, (self.height, self.width))
            frame = gaussian + noise

            # 将值限制在0-255范围内并转换为8位无符号整数
            gray_frame = np.clip(frame, 0, 255).astype(np.uint8)
            
            # 转换为BGR以便绘图
            frame = cv2.cvtColor(gray_frame, cv2.COLOR_GRAY2BGR)
            
            # 初始化质心数据
            centroid_data = {
                'success': False,
                'algorithm': self.algorithm_type
            }
            
            # 始终进行质心检测获取数据
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            details = self.centroid_detector.locate_with_details(gray)
            
            # 如果启用了质心绘制，在图像上绘制标记
            if self.draw_centroid:
                frame, _ = self.centroid_detector.draw_spot_centroid(frame, details)
            
            # 如果启用了十字线绘制，在图像上绘制中心十字
            if self.draw_crosshair:
                frame = self.centroid_detector.draw_crosshair(frame)
            
            # 准备发送到前端的质心数据
            if details['success']:
                centroid_data = {
                    'success': True,
                    'x': details['centroid'][0],
                    'y': details['centroid'][1],
                    'radius': details['radius'],
                    'algorithm': self.algorithm_type
                }
            
            # 编码为jpg格式
            _, buffer = cv2.imencode('.jpg', frame)
            # 转换为base64字符串
            frame_base64 = base64.b64encode(buffer).decode('utf-8')
            
            # 返回图像数据和质心数据
            return {
                'data': frame_base64,
                'centroid': centroid_data
            }

        except Exception as e:
            print(f"生成帧时出错: {str(e)}")
            return None
        
    def start_continuous_capture(self, emit_callback):
        self.is_running = True
        self.capture_thread = threading.Thread(target=self._capture_loop, args=(emit_callback,))
        self.capture_thread.daemon = True
        self.capture_thread.start()

    def stop_continuous_capture(self):
        self.is_running = False
        if self.capture_thread:
            self.capture_thread.join(timeout=1.0)  # 添加超时避免阻塞

    def _capture_loop(self, emit_callback):
        """只负责图像捕获的循环"""
        while self.is_running:
            frame_data = self.get_frame()
            if frame_data is not None:
                emit_callback(frame_data, self.camera_id)  # 传递相机ID
            time.sleep(0.033)  # 约30fps


# 相机管理器类
class CameraManager:
    def __init__(self):
        self.cameras = {}  # 存储多个相机处理器
    
    def add_camera(self, camera_id):
        """添加一个相机到管理器"""
        if camera_id not in self.cameras:
            self.cameras[camera_id] = CameraStreamHandler(camera_id)
        return self.cameras[camera_id]
    
    def get_camera(self, camera_id):
        """获取指定相机处理器"""
        if camera_id not in self.cameras:
            self.add_camera(camera_id)
        return self.cameras[camera_id]
    
    def remove_camera(self, camera_id):
        """移除相机处理器"""
        if camera_id in self.cameras:
            camera = self.cameras[camera_id]
            camera.stop_continuous_capture()    # 停止向前端发送图像
            del self.cameras[camera_id]
    