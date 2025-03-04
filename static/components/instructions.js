if(!Vue.options.components['instructions']){
Vue.component('instructions',{
        template: '#instructions-template',
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
