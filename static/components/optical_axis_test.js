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
                },
                connectedDevices: []
            }
        },
        methods: {
            connectSocket(){
                return new Promise((resolve, reject) => {
                    if(this.socket){
                        this.socket.disconnectSocket();
                    }
                    console.log('建立WebSocket连接。。。');
                    this.socket = io('http://localhost:5000/camera', {
                        transports: ['websocket'],
                        query: {device_id: this.cameraSettings.device_id},
                        upgrade: false
                    });
                    this.socket.on('connect', () => {
                        console.log('WebSocket连接成功');
                        this.setupSocketEvents();
                        resolve();
                    });
                    this.socket.on('connect_error', (error) => {
                        console.error('WebSocket连接失败', error);
                        reject(error);
                    });
                    setTimeout(()=>{
                        reject(new Error('连接超时'));
                    }, 5000);
                });
            },
            disconnectSocket(){
                if(this.socket){
                    console.log('断开WebSocket连接。。。');
                    this.socket.off('image_frame');
                    //this.socket.off('disconnect');
                    this.socket.disconnect();
                    this.socket = null;
                    this.currentFrame = '';
                }
            },
            setupSocketEvents(){
                console.log('setupevents');
                this.socket.on('image_frame', (data) => {
                    console.log('接收到的图像帧,大小：', data.data.length);
                    this.currentFrame = 'data:image/jpeg;base64,' + data.data;
                });
                this.socket.on('disconnect', () => {
                    console.log('WebSocket连接断开');
                    if(this.isStreaming){
                        this.$message.warning('相机连接已断开，正在重连。。');
                        this.isStreaming = false;
                        this.toggleStream();
                    }
                });
            },
            async toggleStream(){
                this.loading = true;
                try{

                    
                    const url = this.isStreaming ? '/api/stop_stream' : '/api/start_stream';
                    const response = await axios.post(url, {
                        device_id: 'default',
                        port: this.cameraSettings.port,
                        baudrate: this.cameraSettings.baudrate,
                        mock: true
                    });
                    if(response.data.status == 'start'){
                        await this.connectSocket();
                        this.isStreaming = !this.isStreaming;
                        this.$message.success('开启相机！');
                    }
                    else if(response.data.status == 'stop'){
                        this.isStreaming = !this.isStreaming;
                        await this.disconnectSocket();
                        this.$message.success('关闭相机！');
                    }
                }
                catch(error){
                    this.$message.error(error.response?.data?.message || '操作失败');

                }
                finally{
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
        watch: {
            active: {
                handler(newVal) {
                    console.log(newVal);
                    if(newVal == 1){

                    }
                    else if(newVal == 2){

                    }
                }
            }
        }
    });
}