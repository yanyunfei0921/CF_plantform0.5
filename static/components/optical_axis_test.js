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
                serial_settings: ''
            }
        },
        methods: {
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
                    console.log(this.active);
                } else {
                    this.$message.warning('已经是第一步了');
                }
            },

            initSocket() {
                if(this.socket) {
                    this.socket.disconnect();
                }
                
                console.log('初始化Socket连接');
                this.socket = io('http://localhost:5000/camera', {
                    transports: ['websocket']
                });

                this.socket.on('connect', () => {
                    console.log("WebSocket连接成功");
                });

                this.socket.on('image_frame', (data) => {
                    console.log("收到图像数据");
                    if (data && data.data) {
                        this.currentFrame = `data:image/jpeg;base64,${data.data}`;
                    }
                });
            },
            
            async sendTestImage() {
                try {
                    if (!this.socket) {
                        await new Promise((resolve, reject) => {
                            this.initSocket();
                        
                        // 当WebSocket连接成功时，调用resolve()
                        this.socket.on('connect', () => {
                            console.log("WebSocket连接成功");
                            resolve();  // 这里告诉await可以继续往下执行了
                            });
                        
                        // 如果5秒后还没连接成功，就报错
                        setTimeout(() => {
                            reject(new Error('连接超时'));
                            }, 5000);
                        });
                    }
                    
                    // 只有在上面的Promise resolve后，才会执行到这里
                    const response = await axios.post('/api/send_test_image');
                    if (response.data.status === 'success') {
                        this.$message.success('接收相机图像成功');
                    }

                } catch (error) {
                    this.$message.error('接收相机图像失败');
                    }
            }
        },
        beforeDestroy() {
            if (this.socket) {
                this.socket.disconnect();
            }
        },
        mounted() {
            //
        },
        watch: {
            active: {
                handler(newVal,oldVal) {
                    //console.log(newVal);
                    //console.log(oldVal);
                    if(oldVal == 2){
                        if(this.socket){
                            console.log('断开WebSocket连接');
                            this.socket.disconnect();
                            this.socket = null;
                            this.currentFrame = '';
                        }
                    }
                }
            }
        }
    });
}