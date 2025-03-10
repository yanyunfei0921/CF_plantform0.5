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
                    loading: false  //是否处于加载、保存过程中
                }
            },
            computed:{
                serial_settings: {
                    get() {
                        return window.DeviceManager.serial_settings;
                    },
                    set(newValue) {
                        window.DeviceManager.serial_settings = newValue;
                    }
                },
                displayOrder: {
                    get() {
                        return window.DeviceManager.displayOrder;
                    },
                    set(newValue) {
                        window.DeviceManager.displayOrder = newValue;
                    }
                }
            },
            methods:{
                // 加载串口设置
                loadSerialSettings() {
                    this.loading = true;
                    axios.get('/api/serial_settings')
                        .then(response => {
                            if (response.data.success) {
                                this.serial_settings = response.data.settings;
                                console.log('从数据库加载串口设置成功');
                                this.$message.success('串口设置已从数据库中加载');
                            } else {
                                console.log('未找到串口设置，使用默认值');
                                this.$message.warning('数据库中未找到串口设置，已使用默认值');
                                // 保存默认设置到数据库
                                this.saveSerialSettingsToDb();
                            }
                        })
                        .catch(error => {
                            console.error('加载串口设置出错:', error);
                            this.$message.error('加载串口设置出错' + error);
                        })
                        .finally(() => {
                            this.loading = false;
                        });
                },
                
                // 保存串口设置到数据库
                saveSerialSettingsToDb() {
                    this.loading = true;
                    axios.post('/api/serial_settings', {
                        settings: this.serial_settings
                    })
                    .then(response => {
                        if (response.data.success) {
                            this.$message.success('串口设置已保存到数据库');
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
                    //console.log(this.form);
                },
                
                saveSerialSetting(){
                    //console.log(this.form.port);
                    for(var key in this.form){
                        this.serial_settings[this.current_serial_name][key] = this.form[key];
                    }
                    this.dialogVisible = false;
                    
                    // 保存到数据库
                    this.saveSerialSettingsToDb();
                    this.$message.success('串口设置已保存');
                }
            },
            mounted(){
                // 组件挂载时加载串口设置
                this.loadSerialSettings();
            }
        });
    }
    