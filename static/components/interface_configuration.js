if(!Vue.options.components['interface_configuration']){
    Vue.component('interface_configuration',{
            template: '#interface_configuration-template',
            data(){
                return {
                    message: 'Hello Vue!',
                    serial_settings:{
                        'light_source':{
                            port:'COM1',
                            baudrate:'9600',
                            databits:'8',
                            stopbits:'1',
                            parity:'none',
                            flowcontrol:'none',
                            timeout:'1000',
                            is_connected: false
                        },
                        'ccd_camera':{
                            port:'COM2',
                            baudrate:'9600',
                            databits:'8',
                            stopbits:'1',
                            parity:'none',
                            flowcontrol:'none',
                            timeout:'1000',
                            is_connected: false
                        },
                        'delay_module':{
                            port:'COM3',
                            baudrate:'9600',
                            databits:'8',
                            stopbits:'1',
                            parity:'none',
                            flowcontrol:'none',
                            timeout:'1000',
                            is_connected: false
                        },
                        'motor1':{
                            port:'COM4',
                            baudrate:'9600',
                            databits:'8',
                            stopbits:'1',
                            parity:'none',
                            flowcontrol:'none',
                            timeout:'1000',
                            is_connected: false
                        },
                        'motor2':{
                            port:'COM5',
                            baudrate:'9600',
                            databits:'8',
                            stopbits:'1',
                            parity:'none',
                            flowcontrol:'none',
                            timeout:'1000',
                            is_connected: false
                        },
                        'motor3':{
                            port:'COM6',
                            baudrate:'9600',
                            databits:'8',
                            stopbits:'1',
                            parity:'none',
                            flowcontrol:'none',
                            timeout:'1000',
                            is_connected: false
                        }
                    },
                    current_serial_name: '',
                    dialogVisible: false,
                    form: {
                        port: '',
                        baudrate: '',
                        databits: '',
                        stopbits: '',
                        parity: '',
                        flowcontrol: '',
                        timeout: ''
                    },
                    formLabelWidth: '120px'
                }
            },
            methods:{
                editSerialSetting(serial_name){
                    this.current_serial_name = serial_name;
                    for(var key in this.serial_settings[serial_name]){
                        this.form[key] = this.serial_settings[serial_name][key];
                    }
                    this.dialogVisible = true;
                    console.log(this.form);
                },
                saveSerialSetting(){
                    console.log(this.form.port);
                    for(var key in this.form){
                        this.serial_settings[this.current_serial_name][key] = this.form[key];
                    }
                    this.dialogVisible = false;
                }
            },
            mounted(){
                //console.log(this.serial_settings);
            }
            
        });
    }
    