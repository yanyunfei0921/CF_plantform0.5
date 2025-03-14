import numpy as np
from scipy.optimize import curve_fit
from scipy.ndimage import center_of_mass
import cv2

class SpotCentroid:
    """光斑质心定位算法类"""
    
    def __init__(self, method='gaussian', gaussian_filter=False, median_filter=False, 
                 gaussian_kernel=3, median_kernel=3):
        """
        初始化
        :param method: 算法选择 ['gaussian', 'contour', 'gray', 'weighted']
        :param gaussian_filter: 是否使用高斯滤波，默认False
        :param median_filter: 是否使用中值滤波，默认False
        :param gaussian_kernel: 高斯滤波核大小，默认3
        :param median_kernel: 中值滤波核大小，默认3
        """
        self.method = method
        self.gaussian_filter = gaussian_filter
        self.median_filter = median_filter
        self.gaussian_kernel = gaussian_kernel if gaussian_kernel % 2 == 1 else gaussian_kernel + 1
        self.median_kernel = median_kernel if median_kernel % 2 == 1 else median_kernel + 1
        
        self.methods = {
            'gaussian': self._gaussian_fit,
            'contour': self._ellipse_fit,
            'gray': self._centroid,
            'weighted': self._weighted_centroid
        }

    def locate(self, image):
        """
        定位光斑质心
        :param image: 输入图像 (numpy array)
        :return: (x, y) 质心坐标，图像学坐标系
        """
        if self.method not in self.methods:
            raise ValueError(f"不支持的算法: {self.method}")
            
        # 图像预处理
        img = self._preprocess(image)
        
        # 调用对应的算法
        return self.methods[self.method](img)

    def _preprocess(self, image):
        """
        图像预处理
        - 灰度化
        - 可选高斯滤波
        - 可选中值滤波
        - 阈值分割
        """
        # 转换为灰度图
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
            
        # 高斯滤波去噪（可选）
        if self.gaussian_filter:
            gray = cv2.GaussianBlur(gray, (self.gaussian_kernel, self.gaussian_kernel), 0)
            
        # 中值滤波去噪（可选）
        if self.median_filter:
            gray = cv2.medianBlur(gray, self.median_kernel)
        
        # Otsu阈值分割
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        return thresh

    def _gaussian_fit(self, image):
        """
        高斯拟合法
        基于二维高斯函数拟合光斑分布
        """
        y, x = np.nonzero(image)
        z = image[y, x]
        
        def gaussian_2d(X, amplitude, x0, y0, sigma_x, sigma_y):
            x, y = X
            return amplitude * np.exp(-((x-x0)**2/(2*sigma_x**2) + (y-y0)**2/(2*sigma_y**2)))
        
        try:
            popt, _ = curve_fit(gaussian_2d, (x, y), z, p0=[np.max(z), np.mean(x), np.mean(y), 1, 1])
            return popt[1], popt[2]  # 返回x0, y0
        except:
            return self._centroid(image)  # 拟合失败时使用灰度重心法

    def _ellipse_fit(self, image):
        """
        椭圆拟合法
        使用OpenCV的椭圆拟合
        """
        contours, _ = cv2.findContours(image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None
            
        # 选择最大的轮廓
        largest_contour = max(contours, key=cv2.contourArea)
        
        if len(largest_contour) < 5:  # 椭圆拟合需要至少5个点
            return self._centroid(image)
            
        try:
            (x, y), (MA, ma), angle = cv2.fitEllipse(largest_contour)
            return x, y
        except:
            return self._centroid(image)

    def _centroid(self, image):
        """
        灰度重心法
        使用scipy的center_of_mass函数
        """
        cy, cx = center_of_mass(image)
        return cx, cy

    def _weighted_centroid(self, image):
        """
        加权灰度重心法
        考虑像素灰度值的权重
        """
        total_intensity = np.sum(image)
        if total_intensity == 0:
            return None
            
        h, w = image.shape
        y_coords, x_coords = np.mgrid[0:h, 0:w]
        
        cx = np.sum(x_coords * image) / total_intensity
        cy = np.sum(y_coords * image) / total_intensity
        
        return cx, cy 

    def locate_with_details(self, image, threshold_value=50):
        """
        定位光斑并返回详细信息
        :param image: 输入图像
        :param threshold_value: 阈值，用于分割光斑
        :return: 字典，包含质心坐标、光斑半径和轮廓
        """
        result = {
            'centroid': None,
            'radius': 10,  # 默认半径
            'contour': None,
            'success': False,
            'algorithm': self.method  # 添加使用的算法
        }
        
        # 获取质心
        centroid = self.locate(image)
        if centroid is None:
            return result
            
        cx, cy = centroid
        result['centroid'] = (cx, cy)
        result['success'] = True
        
        # 提取光斑轮廓
        _, thresh = cv2.threshold(image, threshold_value, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            contour = max(contours, key=cv2.contourArea)
            result['contour'] = contour
            (x, y), r = cv2.minEnclosingCircle(contour)
            result['radius'] = float(r)
            
        return result
        
    def draw_spot_centroid(self, image, details=None):
        """
        在图像上绘制光斑质心和区域圆圈
        :param image: BGR图像
        :param details: 质心详情，如果为None则自动计算
        :return: 处理后的图像和详细信息
        """
        if len(image.shape) == 2:
            # 如果是灰度图，转换为BGR
            frame = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        else:
            frame = image.copy()
            
        # 如果没有提供details，则计算
        if details is None:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if len(frame.shape) == 3 else frame
            details = self.locate_with_details(gray)
            
        if not details['success']:
            return frame, details
            
        cx, cy = details['centroid']
        radius = details['radius']
        
        # 绘制光斑区域圆圈
        cv2.circle(frame, (int(cx), int(cy)), int(radius), (0, 255, 0), 2)
        # 绘制质心位置小点
        cv2.circle(frame, (int(cx), int(cy)), 3, (0, 0, 255), -1)
        
        return frame, details

    def draw_crosshair(self, image):
        """
        在图像中心绘制十字线，将图像分为四等分
        :param image: BGR图像
        :return: 绘制了十字线的图像
        """
        if len(image.shape) == 2:
            # 如果是灰度图，转换为BGR
            frame = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        else:
            frame = image.copy()
            
        h, w = frame.shape[:2]
        center_x, center_y = w // 2, h // 2
        
        # 绘制水平线
        cv2.line(frame, (0, center_y), (w, center_y), (255, 0, 0), 1)
        # 绘制垂直线
        cv2.line(frame, (center_x, 0), (center_x, h), (255, 0, 0), 1)
        
        return frame 