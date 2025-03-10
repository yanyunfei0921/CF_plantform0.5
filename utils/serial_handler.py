import numpy as np
from PIL import Image
import io

class CameraStreamHandler:
    def __init__(self):
        self.is_running = False
        
    def start(self, callback):
        """只发送一张静态测试图像"""
        try:
            # 创建测试图像
            img = self._create_test_image()
            # 转换为字节数据
            buffered = io.BytesIO()
            img.save(buffered, format="JPEG")
            img_bytes = buffered.getvalue()
            # 调用回调发送图像
            callback(img_bytes)
            return True
        except Exception as e:
            raise Exception(f"发送图像失败: {str(e)}")

    def _create_test_image(self, width=640, height=480):
        """创建一个简单的测试图像"""
        # 创建渐变图像
        x = np.linspace(0, 1, width)
        y = np.linspace(0, 1, height)
        X, Y = np.meshgrid(x, y)
        image_array = np.uint8(255 * (X + Y) / 2)
        return Image.fromarray(image_array) 