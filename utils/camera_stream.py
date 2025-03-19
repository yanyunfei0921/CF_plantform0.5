import sys
import os   
from . import mvsdk

import threading
import time
import numpy as np
import cv2
import base64
import platform
from utils.spot_centroid import SpotCentroid

class CameraDevice:
    """实际相机设备控制类"""
    def __init__(self, device_info):
        self.DevInfo = device_info
        self.hCamera = 0
        self.cap = None
        self.pFrameBuffer = 0
        self.friendly_name = device_info.GetFriendlyName()

    def open(self):
        """打开相机连接"""
        if self.hCamera > 0:
            return True

        # 打开相机
        try:
            self.hCamera = mvsdk.CameraInit(self.DevInfo, -1, -1)
        except mvsdk.CameraException as e:
            print(f"CameraInit Failed({e.error_code}): {e.message}")
            return False

        # 获取相机特性描述
        self.cap = mvsdk.CameraGetCapability(self.hCamera)

        # 判断是黑白相机还是彩色相机
        monoCamera = (self.cap.sIspCapacity.bMonoSensor != 0)

        # 设置输出格式
        if monoCamera:
            mvsdk.CameraSetIspOutFormat(self.hCamera, mvsdk.CAMERA_MEDIA_TYPE_MONO8)
        else:
            mvsdk.CameraSetIspOutFormat(self.hCamera, mvsdk.CAMERA_MEDIA_TYPE_BGR8)

        # 计算RGB buffer所需大小
        FrameBufferSize = self.cap.sResolutionRange.iWidthMax * self.cap.sResolutionRange.iHeightMax * (1 if monoCamera else 3)

        # 分配RGB buffer
        self.pFrameBuffer = mvsdk.CameraAlignMalloc(FrameBufferSize, 16)

        # 设置连续采集模式
        mvsdk.CameraSetTriggerMode(self.hCamera, 0)

        # 设置曝光模式和时间
        mvsdk.CameraSetAeState(self.hCamera, 0)
        mvsdk.CameraSetExposureTime(self.hCamera, 30 * 1000)  # 30ms

        # 开始取图
        mvsdk.CameraPlay(self.hCamera)
        
        return True

    def close(self):
        """关闭相机连接"""
        if self.hCamera > 0:
            mvsdk.CameraUnInit(self.hCamera)
            self.hCamera = 0

        if self.pFrameBuffer:
            mvsdk.CameraAlignFree(self.pFrameBuffer)
            self.pFrameBuffer = 0

    def grab_frame(self):
        """获取一帧图像"""
        if self.hCamera <= 0:
            return None
            
        try:
            # 从相机取一帧图片
            pRawData, FrameHead = mvsdk.CameraGetImageBuffer(self.hCamera, 200)
            mvsdk.CameraImageProcess(self.hCamera, pRawData, self.pFrameBuffer, FrameHead)
            mvsdk.CameraReleaseImageBuffer(self.hCamera, pRawData)

            # Windows下需要翻转图像
            if platform.system() == "Windows":
                mvsdk.CameraFlipFrameBuffer(self.pFrameBuffer, FrameHead, 1)
            
            # 转换为numpy数组
            frame_data = (mvsdk.c_ubyte * FrameHead.uBytes).from_address(self.pFrameBuffer)
            frame = np.frombuffer(frame_data, dtype=np.uint8)
            frame = frame.reshape((FrameHead.iHeight, FrameHead.iWidth, 
                                   1 if FrameHead.uiMediaType == mvsdk.CAMERA_MEDIA_TYPE_MONO8 else 3))
            
            # 如果是单通道图像，转换为三通道
            if len(frame.shape) == 2 or frame.shape[2] == 1:
                frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
                
            return frame
        except mvsdk.CameraException as e:
            if e.error_code != mvsdk.CAMERA_STATUS_TIME_OUT:
                print(f"CameraGetImageBuffer failed({e.error_code}): {e.message}")
            return None


class CameraStreamHandler:
    def __init__(self, camera_id="default"):
        self.camera_id = camera_id
        self.is_running = False
        self.capture_thread = None
        self.camera_device = None  # 实际相机设备对象
        
        # 图像参数
        self.width = 1280
        self.height = 1024
        
        # 质心算法参数
        self.algorithm_type = "weighted"  # 默认加权质心法
        self.draw_centroid = True  # 是否绘制质心，默认绘制
        self.draw_crosshair = True  # 是否绘制十字线，默认绘制
        
        # 创建质心定位对象
        self.centroid_detector = SpotCentroid(method=self.algorithm_type)
        
    def connect_camera(self, device_index):
        """连接到指定索引的相机"""
        # 枚举所有相机
        DevList = mvsdk.CameraEnumerateDevice()
        if len(DevList) <= device_index:
            print(f"没有找到索引为 {device_index} 的相机")
            return False
            
        # 创建相机设备并连接
        self.camera_device = CameraDevice(DevList[device_index])
        return self.camera_device.open()
        
    def disconnect_camera(self):
        """断开相机连接"""
        if self.camera_device:
            self.camera_device.close()
            self.camera_device = None
        
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
        """获取一帧图像并进行处理"""
        try:
            # 如果相机未连接，返回空
            if not self.camera_device:
                return None
                
            # 从相机获取帧
            frame = self.camera_device.grab_frame()
            
            if frame is None:
                return None
                
            # 更新图像尺寸
            self.height, self.width = frame.shape[:2]
            
            # 初始化质心数据
            centroid_data = {
                'success': False,
                'algorithm': self.algorithm_type
            }
            
            # 进行质心检测
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
            print(f"处理帧时出错: {str(e)}")
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
        """图像捕获循环"""
        while self.is_running:
            frame_data = self.get_frame()
            if frame_data is not None:
                emit_callback(frame_data, self.camera_id)
            time.sleep(0.033)  # 约30fps


# 相机管理器类
class CameraManager:
    def __init__(self):
        self.cameras = {}  # 存储多个相机处理器
        self.device_list = self._enumerate_cameras()  # 枚举可用相机
        
    def _enumerate_cameras(self):
        """枚举所有可用的相机"""
        try:
            return mvsdk.CameraEnumerateDevice()
        except:
            print("枚举相机失败")
            return []
    
    def get_camera_list(self):
        """获取可用相机列表"""
        camera_info = []
        for i, dev in enumerate(self.device_list):
            camera_info.append({
                'index': i,
                'name': dev.GetFriendlyName(),
                'port': dev.GetPortType()
            })
        return camera_info
    
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
            camera.disconnect_camera()          # 断开相机连接
            del self.cameras[camera_id]
    
    def connect_camera(self, camera_id, device_index):
        """连接指定的相机"""
        camera = self.get_camera(camera_id)
        return camera.connect_camera(device_index)
    
    def disconnect_camera(self, camera_id):
        """断开指定的相机"""
        if camera_id in self.cameras:
            self.cameras[camera_id].disconnect_camera()
    