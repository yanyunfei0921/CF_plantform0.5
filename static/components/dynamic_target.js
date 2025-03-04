if(!Vue.options.components['dynamic_target']){
    Vue.component('dynamic_target',{
            template: '#dynamic_target-template',
            data(){
                return {
                    message: 'Hello Vue!'
                }
            },
            methods:{
                //
            }
        });
    }
    