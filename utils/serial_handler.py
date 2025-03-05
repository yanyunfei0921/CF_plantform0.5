import serial
import threading
import time
import numpy as np
from PIL import Image
import base64
import io
import logging
from threading import Thread, Event

class CameraStreamHandler:
    def __init__(self, port=None, baudrate=None, device_id='camera'):
        self.port = port
        self.baudrate = baudrate
        self.device_id = device_id
        self.is_running = False
        self._stop_event = threading.Event()
        self.serial = None
        self.callback = None
        
    def start(self, callback, mock=False):
        """
        启动相机流
        :param callback: 处理图像的回调函数
        :param mock: 是否使用模拟模式,True为模拟模式,False为实际串口模式
        """
        try:
            self.is_running = True
            self._stop_event.clear()

            if not mock:
                # 实际串口模式
                self.serial = serial.Serial(
                    port=self.port,
                    baudrate=self.baudrate,
                    timeout=1
                )
                # 启动实际串口读取线程
                self.thread = threading.Thread(
                    target=self._read_stream,
                    args=(callback,)
                )
            else:
                # 模拟模式
                self.thread = threading.Thread(
                    target=self._mock_stream,
                    args=(callback,)
                )

            self.thread.start()
            return True

        except Exception as e:
            self.is_running = False
            raise Exception(f"启动失败: {str(e)}")

    def stop(self, mock=False):
        """
        停止相机流
        :param mock: 是否为模拟模式，需要与start时的模式一致
        """
        self.is_running = False
        self._stop_event.set()

        if not mock and self.serial:
            self.serial.close()

        if hasattr(self, 'thread'):
            self.thread.join()

    def _read_stream(self, callback):
        """实际串口读取方法"""
        try:
            while not self._stop_event.is_set():
                if self.is_running and self.serial.is_open:
                    # 这里需要根据实际相机协议修改
                    frame_data = self.serial.read(1024)
                    if frame_data:
                        callback(frame_data, self.device_id)
        except Exception as e:
            logging.error(f"读取串口错误: {str(e)}")
        finally:
            if self.serial and self.serial.is_open:
                self.serial.close()

    def _mock_stream(self, callback):
        """模拟数据流方法"""
        try:
            while not self._stop_event.is_set():
                if self.is_running:
                    # 创建模拟图像
                    img = self._create_test_image()
                    # 转换为字节数据，而不是base64字符串
                    buffered = io.BytesIO()
                    img.save(buffered, format="JPEG")
                    img_bytes = buffered.getvalue()  # 获取字节数据
                    # 调用回调，传入字节数据
                    callback(img_bytes, self.device_id)  # 直接传递字节数据
                    # 控制帧率
                    time.sleep(0.1)
        except Exception as e:
            logging.error(f"模拟数据流错误: {str(e)}")

    def _create_test_image(self, width=640, height=480):
        """创建动态测试图像"""
        t = time.time()
        x = np.linspace(0, 1, width)
        y = np.linspace(0, 1, height)
        X, Y = np.meshgrid(x, y)
        
        # 创建动态波纹效果
        freq = 2 * np.pi
        wave = np.sin(freq * (X + Y + t/2)) * 127 + 128
        
        # 添加移动的圆
        center_x = (np.sin(t) + 1) / 2
        center_y = (np.cos(t) + 1) / 2
        circle = np.sqrt((X - center_x)**2 + (Y - center_y)**2)
        circle = (circle < 0.1) * 255

        # 合并效果
        image_array = np.uint8(wave + circle)
        
        # 创建图像对象
        img = Image.fromarray(image_array)
        
        # 添加时间戳
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        return img 