if(!Vue.options.components['optical_axis_test']){
    Vue.component('optical_axis_test',{
            template: '#optical_axis_test-template',
            data(){
                return {
                    message: 'Hello Vue!',
                    active: 1
                }
            },
            methods:{
                nextStep(){
                    console.log(this.active);
                    if(this.active < 6){
                        this.active++;
                    }
                    else{
                        this.$message.success('光轴一致性测试已完成');
                    }
                },
                previousStep(){
                    if(this.active == 6){
                        this.$message.success('光轴一致性测试已完成');
                    }
                    else if(this.active > 1){
                        this.active--;
                    }
                    else{
                        this.$message.warning('已经是第一步了');
                    }
                }
            },
            mounted(){

            },
            watch:{
                active:{
                    handler(newVal){
                        console.log(newVal);
                        
                    }
                }
            }
        });
    }