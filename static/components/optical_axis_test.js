if(!Vue.options.components['optical_axis_test']){
    Vue.component('optical_axis_test',{
        template: '#optical_axis_test-template',
        data(){
            return {
                // 测试步骤控制
                active: 1,
                loading: false,
                
                // Socket连接
                socket: null,
                
                // 相机管理
                cameras: {
                    pod: { 
                        currentFrame: null, //当前帧
                        isStreaming: false, //是否正在传输
                        centroidData: {
                            success: false,
                            x: 0,
                            y: 0,
                            radius: 0,
                            algorithm: 'weighted'
                        },
                        imageInfo: {
                            width: 0,
                            height: 0
                        },
                        drawSettings: {
                            drawCentroid: true,
                            drawCrosshair: true
                        }
                    },
                    system: { 
                        currentFrame: null, 
                        isStreaming: false, 
                        centroidData: {
                            success: false,
                            x: 0,
                            y: 0,
                            radius: 0,
                            algorithm: 'weighted'
                        },
                        imageInfo: {
                            width: 0,
                            height: 0
                        },
                        drawSettings: {
                            drawCentroid: true,
                            drawCrosshair: true
                        }
                    },
                    detection: { 
                        currentFrame: null, 
                        isStreaming: false, 
                        centroidData: {
                            success: false,
                            x: 0,
                            y: 0,
                            radius: 0,
                            algorithm: 'weighted'
                        },
                        imageInfo: {
                            width: 0,
                            height: 0
                        },
                        drawSettings: {
                            drawCentroid: false,
                            drawCrosshair: false
                        }
                    }
                },
                
                // 质心算法描述
                algorithmDescriptions: {
                    weighted: {
                        title: '加权质心法',
                        description: '使用像素灰度值作为权重计算质心，适用于光斑强度分布较为均匀的情况。'
                    },
                    gray: {
                        title: '灰度质心法',
                        description: '使用灰度质心法计算光斑质心，适用于光斑强度分布较为均匀的情况。'
                    },
                    gaussian: {
                        title: '高斯拟合法',
                        description: '使用二维高斯函数拟合光斑分布并计算中心，适用于近似高斯分布的光斑。'
                    },
                    contour: {
                        title: '椭圆拟合法',
                        description: '基于光斑轮廓提取并计算几何中心，适用于光斑边缘清晰的情况。'
                    }
                },
                
                // 指示激光器控制
                indicationLaser :{
                    isLaserOn: false,
                    laserPower: 0,
                },

                // 可见光控制
                visibleLight: {
                    isVisibleLightOn: false,
                    visibleLightPower: 0
                },
                
                // 红外黑体控制
                infraredBlackBody: {
                    isInfraredBlackBodyOn: false,
                    temperature: 0
                },

                // 1064nm激光器控制
                // 这个激光器逻辑比较特别，需要延时模块硬件触发，暂时不管它的通信和控制
                swirLaser :{
                    isLaserOn: false,
                    laserPower: 0
                },
                
                // 基准光轴(transmit,receive)(ir,visible,laser)
                referenceAxis: {
                    type: 'transmit', // 发射光轴或接收光轴
                    spectrum: 'ir' // 红外或可见光或激光
                },

                // 靶标(cross,star,four,usaf)
                target: 'cross' // 默认十字靶标
            }
        },
        methods: {
            // ========== 流程控制方法 ==========
            nextStep() {
                if(this.active < 6){
                    this.active++;
                } else {
                    this.$message.success('光轴一致性测试已完成');
                }
            },
            
            previousStep() {
                if(this.active == 6){
                    this.$message.success('光轴一致性测试已完成');
                } else if(this.active > 1){
                    this.active--;
                } else {
                    this.$message.warning('已经是第一步了');
                }
            },

            // ========== Socket 连接管理 ==========
            initSocket() {
                return new Promise((resolve, reject) => {
                    if (this.socket && this.socket.connected) {
                        resolve(); // 如果socket已存在且已连接，直接返回
                        return;
                    }
                    if (this.socket) {
                        this.socket.disconnect(); // 如果socket存在但未连接，断开重连
                    }
                    this.socket = io('/camera');
                    this.socket.on('connect', () => {
                        console.log("WebSocket连接成功");
                        resolve();
                    });
                    
                    // 设置各相机的帧接收事件
                    this.socket.on('camera_pod_frame', (data) => {
                        if (data && data.data) {
                            this.cameras.pod.currentFrame = 'data:image/jpeg;base64,' + data.data;
                            
                            // 更新质心数据
                            if (data.centroid) {
                                this.cameras.pod.centroidData = data.centroid;
                            }
                            
                            // 更新图像信息
                            this.updateImageInfo('pod', this.cameras.pod.currentFrame);
                        }
                    });
                    
                    this.socket.on('camera_system_frame', (data) => {
                        if (data && data.data) {
                            this.cameras.system.currentFrame = 'data:image/jpeg;base64,' + data.data;
                            if (data.centroid) {
                                this.cameras.system.centroidData = data.centroid;
                            }
                            this.updateImageInfo('system', this.cameras.system.currentFrame);
                        }
                    });
                    
                    this.socket.on('camera_detection_frame', (data) => {
                    if (data && data.data) {
                            this.cameras.detection.currentFrame = 'data:image/jpeg;base64,' + data.data;
                            if (data.centroid) {
                                this.cameras.detection.centroidData = data.centroid;
                            }
                            this.updateImageInfo('detection', this.cameras.detection.currentFrame);
                        }
                    });
                    
                    this.socket.on('error', (error) => {
                        console.error("Socket错误:", error);
                        reject(error);
                    });
                    
                    // 设置超时
                    setTimeout(() => {
                        if (!this.socket.connected) {
                            reject(new Error('连接超时'));
                        }
                    }, 5000);
                });
            },
            
            // ========== 相机控制方法 ==========
            toggleCameraStream(cameraId) {
                if (!this.cameras[cameraId]) {
                    this.$message.error(`未找到相机: ${cameraId}`);
                    return;
                }
                
                if (!this.cameras[cameraId].isStreaming) {
                    this.startCameraStream(cameraId);
                } else {
                    this.stopCameraStream(cameraId);
                }
            },
            
            async startCameraStream(cameraId) {
                try {
                    this.loading = true;
                    // 总是在开启相机时初始化socket
                    await this.initSocket();
                    
                    this.socket.emit('start_stream', { camera_id: cameraId }, (response) => {
                        this.loading = false;
                        if (response && response.success) {
                            this.cameras[cameraId].isStreaming = true;
                            this.$message.success(`开始接收${cameraId}相机图像`);
                        } else {
                            this.$message.error('开启相机流失败');
                        }
                    });
                } catch (error) {
                    this.loading = false;
                    console.error('连接失败:', error);
                    this.$message.error('连接失败: ' + error.message);
                }
            },
            
            stopCameraStream(cameraId) {
                this.loading = true;
                this.socket.emit('stop_stream', { camera_id: cameraId }, (response) => {
                    this.loading = false;
                    if (response && response.success) {
                        this.cameras[cameraId].isStreaming = false;
                        this.$message.success(`停止接收${cameraId}相机图像`);
                    } else {
                        this.$message.error('停止相机流失败');
                    }
                });
            },
            
            setCameraAlgorithm(cameraId, algorithm) {
                if (!this.cameras[cameraId]) {
                    this.$message.error(`未找到相机: ${cameraId}`);
                    return;
                }
                
                if (!this.socket || !this.cameras[cameraId].isStreaming) {
                    this.$message.warning('未建立连接，请先点击开启按钮');
                    return;
                }
                
                if (this.socket.connected) {
                    this.socket.emit('set_algorithm', { 
                        camera_id: cameraId, 
                        algorithm: algorithm 
                    });
                    
                    this.cameras[cameraId].algorithm = algorithm;
                    
                    this.$message({
                        message: `已切换${cameraId}相机算法到${algorithm}`,
                        type: 'success',
                        duration: 2000
                    });
                } else {
                    this.$message.warning('未连接到服务器，算法切换可能不生效');
                }
            },
            
            setCameraCentroidDisplay(cameraId, enabled) {
                if (!this.cameras[cameraId]) {
                    this.$message.error(`未找到相机: ${cameraId}`);
                    return;
                }
                
                this.cameras[cameraId].drawSettings.drawCentroid = enabled;
                
                if (this.socket && this.socket.connected) {
                    this.socket.emit('set_centroid_display', { 
                        camera_id: cameraId, 
                        enabled: enabled 
                    });
                } else {
                    this.$message.warning('未建立连接，请先点击开启按钮');
                }
            },
            
            setCameraCrosshairDisplay(cameraId, enabled) {
                if (!this.cameras[cameraId]) {
                    this.$message.error(`未找到相机: ${cameraId}`);
                    return;
                }
                
                this.cameras[cameraId].drawSettings.drawCrosshair = enabled;
                
                if (this.socket && this.socket.connected) {
                    this.socket.emit('set_crosshair_display', { 
                        camera_id: cameraId, 
                        enabled: enabled 
                    });
                } else {
                    this.$message.warning('未建立连接，请先点击开启按钮');
                }
            },
            
            updateImageInfo(cameraId, imageUrl) {
                if (!imageUrl) return;
                
                const img = new Image();
                img.onload = () => {
                    this.cameras[cameraId].imageInfo.width = img.width;
                    this.cameras[cameraId].imageInfo.height = img.height;
                };
                img.src = imageUrl;
            },
            
            // ========== 相机设置与显示相关方法 ==========
            toggleCameraImage(cameraId) {
                this.toggleCameraStream(cameraId);
            },
            
            onAlgorithmChange(cameraId, value) {
                this.setCameraAlgorithm(cameraId, value);
            },
            
            toggleCentroidDisplay(cameraId, enabled) {
                this.setCameraCentroidDisplay(cameraId, enabled);
            },
            
            toggleCrosshairDisplay(cameraId, enabled) {
                this.setCameraCrosshairDisplay(cameraId, enabled);
            },
            
            // ========== 统一的设备控制方法 ==========
            /**
             * 统一的设备控制函数 - 用于开关设备或调整参数值
             * @param {string} deviceType - 设备类型: 'indicationLaser', 'blackBody', 'visibleLight'
             * @param {number|null} [value] - 设置的值，如果为null/undefined则执行开关操作
             * @returns {Promise<void>}
             */
            async controlCompositeDevice(deviceType, value) {
                try {
                    let deviceConfig = null;
                    let apiEndpoint = '';
                    let paramName = '';
                    let deviceDisplayName = '';
                    let defaultValue = 0;
                    
                    // 根据设备类型获取对应配置
                    switch (deviceType) {
                        case 'indicationLaser':
                            deviceConfig = this.indicationLaser;
                            apiEndpoint = '/api/set_laser_power';
                            paramName = 'power';
                            defaultValue = 500;
                            deviceDisplayName = '指示激光';
                            break;
                        case 'blackBody':
                            deviceConfig = this.infraredBlackBody;
                            apiEndpoint = '/api/set_black_body_temperature';
                            paramName = 'temperature';
                            defaultValue = 20000;
                            deviceDisplayName = '红外黑体';
                            break;
                        case 'visibleLight':
                            deviceConfig = this.visibleLight;
                            apiEndpoint = '/api/set_visible_light';
                            paramName = 'power';
                            defaultValue = 250;
                            deviceDisplayName = '可见光源';
                            break;
                        default:
                            throw new Error('未知设备类型');
                    }
                    
                    // 获取设备状态和值的属性名
                    const isOnProp = deviceType === 'indicationLaser' ? 'isLaserOn' : 
                                     deviceType === 'blackBody' ? 'isInfraredBlackBodyOn' : 'isVisibleLightOn';
                    const valueProp = deviceType === 'indicationLaser' ? 'laserPower' : 
                                      deviceType === 'blackBody' ? 'temperature' : 'visibleLightPower';
                    
                    // 判断操作类型：开关操作还是调整参数值
                    const isToggle = value === undefined || value === null;
                    
                    // 如果是调整参数值且设备已关闭，则直接返回
                    if (!isToggle && !deviceConfig[isOnProp]) {
                        return;
                    }
                    
                    // 计算要发送的值
                    let paramValue;
                    if (isToggle) {
                        // 开关操作：如果已开启则关闭(0)，否则使用当前值或默认值
                        paramValue = deviceConfig[isOnProp] ? 0 : (deviceConfig[valueProp] || defaultValue);
                    } else {
                        // 调整参数值：使用传入的值
                        paramValue = value;
                    }
                    
                    // 构造请求参数
                    const params = {};
                    params[paramName] = paramValue;
                    
                    // 发送请求
                    const response = await axios.post(apiEndpoint, params);
                    
                    if (response.data.success) {
                        if (isToggle) {
                            // 开关操作：更新设备状态
                            deviceConfig[isOnProp] = !deviceConfig[isOnProp];
                            deviceConfig[valueProp] = deviceConfig[isOnProp] ? paramValue : 0;
                        } else {
                            // 无需更新状态，值已经通过v-model双向绑定更新
                        }
                    } else {
                        const errorMsg = isToggle ? `${deviceDisplayName}控制失败` : 
                                        (deviceType === 'indicationLaser' ? '激光功率调节失败' : 
                                         deviceType === 'blackBody' ? '黑体温度调节失败' : '可见光亮度调节失败');
                        this.$message.error(errorMsg);
                    }
                } catch (error) {
                    this.$message.error('操作失败：' + error.message);
                }
            },
            
            // ========== 切换步骤时的处理 ==========
            cleanupStep(step) {
                // 步骤2: 停止pod相机流和关闭指示激光
                if (step === 2) {
                    if (this.cameras.pod.isStreaming) {
                        this.stopCameraStream('pod');
                    }
                    
                    if (this.indicationLaser.isLaserOn) {
                        this.controlCompositeDevice('indicationLaser');
                    }
                }
                // 步骤3: 停止相关相机流，并关闭并关闭黑体和可见光光源
                else if (step === 3) {
                    // 使用正确的相机ID
                    const cameraIds = this.referenceAxisType === 'transmit' 
                        ? ['system'] 
                        : ['pod', 'detection'];
                        
                    cameraIds.forEach(cameraId => {
                        if (this.cameras[cameraId] && this.cameras[cameraId].isStreaming) {
                            this.stopCameraStream(cameraId);
                        }
                    });
                    // 关闭黑体和可见光光源
                    if(this.infraredBlackBody.isInfraredBlackBodyOn){
                        this.controlCompositeDevice('blackBody');
                    }
                    if(this.visibleLight.isVisibleLightOn){
                        this.controlCompositeDevice('visibleLight');
                    }
                }
                // 步骤4: 停止相关相机流
                else if (step === 4) {
                    // 同样修改这里，使用正确的相机ID
                    const cameraIds = this.referenceAxisType === 'transmit' 
                        ? ['system'] 
                        : ['pod', 'detection'];
                        
                    cameraIds.forEach(cameraId => {
                        if (this.cameras[cameraId] && this.cameras[cameraId].isStreaming) {
                            this.stopCameraStream(cameraId);
                        }
                    });
                }
            },
            
            // ========== 切换基准光轴的处理 ==========
            cleanupChangeAxis(oldAxis, newAxis) {
                // 操作与切换出步骤3一致
                this.cleanupStep(3);
            },

            initStep(step) {
                // 移除自动初始化Socket连接
                console.log(`进入步骤${step}`);
                // 不再自动初始化socket: if (step >= 2 && step <= 4) { ... }
            },

            /**
             * 格式化提示文本
             * @param {string} deviceType - 设备类型: 'indicationLaser', 'blackBody', 'visibleLight'
             * @param {number} value - 原始值
             * @returns {string} 格式化后的文本
             */
            formatCompositeDeviceTooltip(deviceType, value) {
                // 增加空值检查
                if (deviceType === null || deviceType === undefined) {
                    return '0';
                }
                
                if (value === null || value === undefined) {
                    return '0';
                }
                
                switch (deviceType) {
                    case 'indicationLaser':
                        return value / 10 + '%';  // 将0-1000转换为0-100%
                    case 'blackBody':
                        return (value / 1000).toFixed(2) + '°C';  // 将0-40000转换为0-40°C
                    case 'visibleLight':
                        return (value / 5) + '%';  // 将0-500转换为0-100%
                    default:
                        // 确保无论什么情况都返回字符串
                        return String(value || 0);
                }
            }
        },
        computed: {
            // 获取指定相机的光斑中心与图像中心X方向偏差
            getCameraXDifference() {
                return (cameraId) => {
                    const camera = this.cameras[cameraId];
                    if (camera.centroidData.success && camera.imageInfo.width) {
                        return camera.centroidData.x - camera.imageInfo.width / 2;
                    }
                    return 0;
                };
            },
            
            // 获取指定相机的光斑中心与图像中心Y方向偏差
            getCameraYDifference() {
                return (cameraId) => {
                    const camera = this.cameras[cameraId];
                    if (camera.centroidData.success && camera.imageInfo.height) {
                        return camera.centroidData.y - camera.imageInfo.height / 2;
                    }
                    return 0;
                };
            },
            
            // 获取当前步骤需要的相机ID列表
            stepCameraIds() {
                switch (this.active) {
                    case 2:
                        return ['pod'];
                    case 3:
                        // 步骤3：发射光轴需要用到系统相机，接收光轴需要用到吊舱相机和靶面监控相机
                        return this.referenceAxisType === 'transmit' ? ['system'] : ['pod', 'detection'];
                    case 4:
                        // 步骤4：发射光轴需要用到系统相机，接收光轴需要用到系统相机和靶面监控相机
                        return this.referenceAxisType === 'transmit' ? ['system'] : ['pod', 'detection'];
                    default:
                        return [];
                }
            }
        },
        watch: {
            active(newVal, oldVal) {
                console.log(`从步骤 ${oldVal} 切换到步骤 ${newVal}`);
                
                // 清理旧的步骤
                this.cleanupStep(oldVal);
                
                // 初始化新的步骤
                this.initStep(newVal);
            },

            referenceAxisType(newValue, oldValue) {
                console.log('切换到', newValue === 'transmit' ? '发射光轴' : '接收光轴');
                this.cleanupChangeAxis();
            }
        },
        mounted() {
            // 不再自动初始化socket
            console.log('组件已挂载');
        },
        beforeDestroy() {
            // 销毁前停止所有相机并断开连接
            if (this.socket) {
                Object.keys(this.cameras).forEach(cameraId => {
                    if (this.cameras[cameraId].isStreaming) {
                        this.socket.emit('stop_stream', { camera_id: cameraId });
                    }
                });
                            this.socket.disconnect();
                            this.socket = null;
            }
            
            // 确保激光关闭
            if (this.indicationLaser.isLaserOn) {
                axios.post('/api/set_laser_power', { power: 0 })
                    .catch(error => console.error('关闭激光失败:', error));
            }

        }
    });
}