if(!Vue.options.components['interface_configuration']){
    Vue.component('interface_configuration',{
            template: '#interface_configuration-template',
            data(){
                return {
                    message: 'Hello Vue!',
                    current_serial_name: '',
                    dialogVisible: false,
                    form: {
                        protocol: '',
                        port: '',
                        baudrate: '',
                        databits: '',
                        stopbits: '',
                        parity: '',
                        flowcontrol: '',
                        timeout: ''
                    },
                    formLabelWidth: '120px',
                    serial_settings: {}, //串口设置
                    isLoaded: false, //是否加载完成
                    loading: false , //是否处于加载、保存过程中
                    //前端显示顺序，为避免因json文件转换而导致的乱序
                    displayOrder:[
                        'light_source',
                        'motor_three_axis',
                        'ccd_camera_sys',
                        'ccd_camera_pod',
                        'delay_module',
                        'motor2',
                        'motor3'
                    ]
                }
            },
            methods:{
                // 加载串口设置
                loadSerialSettings() {
                    console.log('加载串口设置');
                    this.loading = true;
                    axios.get('/api/serial_settings')
                        .then(response => {
                            if (response.data.success) {
                                this.serial_settings = response.data.data;
                                this.$message.success('串口设置已加载');
                            } else {
                                this.$message.error('加载串口设置出错' + response.data.message);
                            }
                        })
                        .catch(error => {
                            this.$message.error('加载串口设置出错' + error);
                        })
                        .finally(() => {
                            this.loading = false;
                            this.isLoaded = true;
                        });
                },
                
                // 连接设备
                connectDevice(device_name) {
                    const settings = {
                        ...this.serial_settings[device_name],
                        device_type: this.getDeviceType(device_name)
                    };
                    
                    axios.post('/api/connect_device', {
                        device_name: device_name,
                        settings: settings
                    })
                    .then(response => {
                        if (response.data.success) {
                            this.$message.success(`${device_name}连接成功`);
                            this.updateDeviceStatus();
                        } else {
                            this.$message.error(`${device_name}连接失败: ${response.data.message}`);
                        }
                    })
                    .catch(error => {
                        this.$message.error(`连接失败: ${error}`);
                    });
                },

                // 断开设备
                disconnectDevice(device_name) {
                    axios.post('/api/disconnect_device', {
                        device_name: device_name
                    })
                    .then(response => {
                        if (response.data.success) {
                            this.$message.success(`${device_name}已断开连接`);
                            this.updateDeviceStatus();
                        } else {
                            this.$message.error(`断开连接失败: ${response.data.message}`);
                        }
                    })
                    .catch(error => {
                        this.$message.error(`断开连接失败: ${error}`);
                    });
                },

                // 更新设备状态
                updateDeviceStatus() {
                    axios.get('/api/devices_status')
                        .then(response => {
                            if (response.data.success) {
                                const statusData = response.data.data;
                                for (const [deviceName, status] of Object.entries(statusData)) {
                                    if (this.serial_settings[deviceName]) {
                                        this.$set(this.serial_settings[deviceName], 'is_connected', status);
                                    }
                                }
                            }
                        })
                        .catch(error => {
                            console.error('获取设备状态失败:', error);
                        });
                },

                // 获取设备类型
                getDeviceType(device_name) {
                    const deviceTypes = {
                        'light_source': 'light_source',
                        'ccd_camera_sys': 'ccd_camera',
                        'ccd_camera_pod': 'ccd_camera',
                        'motor_three_axis': 'motor_three_axis'
                        // 可以添加更多设备类型映射
                    };
                    return deviceTypes[device_name] || '';
                },

                // 保存串口设置到数据库
                saveSerialSettingsToDb() {
                    this.loading = true;
                    axios.post('/api/serial_settings', {
                        serial_settings: this.serial_settings
                    })
                    .then(response => {
                        if (response.data.success) {
                            this.$message.success('串口设置已保存');
                        } else {
                            this.$message.error('保存串口设置失败: ' + response.data.message);
                        }
                    })
                    .catch(error => {
                        console.error('保存串口设置出错:', error);
                        this.$message.error('保存串口设置出错');
                    })
                    .finally(() => {
                        this.loading = false;
                    });
                },
                
                editSerialSetting(serial_name){
                    this.current_serial_name = serial_name;
                    for(var key in this.serial_settings[serial_name]){
                        this.form[key] = this.serial_settings[serial_name][key];
                    }
                    this.dialogVisible = true;
                },
                
                saveSerialSetting(){
                    for(var key in this.form){
                        this.serial_settings[this.current_serial_name][key] = this.form[key];
                    }
                    this.dialogVisible = false;
                    
                    // 保存到数据库
                    this.saveSerialSettingsToDb();
                }
            },
            created(){
                // 组件挂载前加载串口设置
                this.loadSerialSettings();
                // 定期更新设备状态
                setInterval(this.updateDeviceStatus, 5000);
            }
        });
    }
    