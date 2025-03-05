if(!Vue.options.components['optical_axis_test']){
    Vue.component('optical_axis_test',{
        template: '#optical_axis_test-template',
        data(){
            return {
                message: 'Hello Vue!',
                active: 1,
                socket: null,
                currentFrame: '',        // 简化为单个frame
                isStreaming: false,      // 简化为单个状态
                loading: false,          // 简化为单个loading状态
                cameraSettings: {        // 相机设置
                    port: 'COM1',
                    baudrate: 9600
                }
            }
        },
        methods: {
            initSocket() {
                if(this.socket) {
                    console.log("断开现有连接");
                    this.socket.disconnect();
                }
                
                console.log('开始初始化Socket连接');
                this.socket = io('http://localhost:5000/camera', {
                    transports: ['websocket']
                });

                this.socket.on('connect', () => {
                    console.log("WebSocket连接成功, 前端 socket.id:", this.socket.id);
                    // 发送测试消息
                    this.socket.emit('test_connection', { 
                        client_id: this.socket.id,
                        timestamp: Date.now()
                    });
                });

                this.socket.on('test_response', (data) => {
                    console.log("收到测试响应:", data);
                    console.log("服务器的 SID:", data.server_sid);
                    console.log("当前前端 socket.id:", this.socket.id);
                });

                this.socket.on('image_frame', (data) => {
                    console.log("收到图像数据, 来自服务器 SID:", data.server_sid);
                    console.log("当前前端 socket.id:", this.socket.id);
                    // ... 处理图像 ...
                });
            },
            
            async toggleStream() {
                this.loading = true;
                try {
                    const url = this.isStreaming ? '/api/stop_stream' : '/api/start_stream';
                    const response = await axios.post(url, {
                        device_id: 'camera',
                        port: this.cameraSettings.port,
                        baudrate: this.cameraSettings.baudrate,
                        mock: true  // 设置为true使用模拟模式，false使用实际串口
                    });

                    if (response.data.status === 'success') {
                        this.isStreaming = !this.isStreaming;
                        this.$message.success(response.data.message);
                    }
                } catch (error) {
                    this.$message.error(error.response?.data?.message || '操作失败');
                } finally {
                    this.loading = false;
                }
            },
            
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
            
            stopStream() {
                if (this.isStreaming) {
                    this.toggleStream();
                }
            }
        },
        mounted() {
            //
        },
        beforeDestroy() {
            this.stopStream();
            if (this.socket) {
                this.socket.disconnect();
            }
        },
        watch: {
            active: {
                handler(newVal) {
                    console.log(newVal);
                    if(newVal == 1){

                    }
                    else if(newVal == 2 && !this.socket){
                        console.log('initSocket');

                        this.initSocket();
                    }
                }
            }
        }
    });
}