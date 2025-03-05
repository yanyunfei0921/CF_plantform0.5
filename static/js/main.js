const app = new Vue({
    el: '#app',
    data() {
        return {
            activeMenu: '',
            message: 'Hello Vue!',
            currentComponent: null,
            loadedComponents: {}
        }
    },
    mounted() {
        console.log('Vue instance mounted');
    },
    methods: {
        //侧菜单栏点击加载组件
        handleSelect(index, indexPath) {
            const menuMap = {
                '1-1': {title: '首页 / 使用说明', component: 'instructions'},
                '1-2': {title: '首页 / 注意事项', component: 'notes'},
                '2-1': {title: '接口配置 / 接口配置', component: 'interface_configuration'},
                '3-1': {title: '光轴一致性测试 / 选项1', component: 'optical_axis_test'},
                '3-2': {title: '光轴一致性测试 / 选项2', component: 'optical_axis_test2'},
                '4-1': {title: '动态目标模拟 / 选项1', component: 'dynamic_target'},
                '4-2': {title: '动态目标模拟 / 选项2', component: 'dynamic_target2'},
                '5-1': {title: '激光模拟测距 / 选项1', component: 'laser_ranging'},
                '5-2': {title: '激光模拟测距 / 选项2', component: 'laser_ranging2'},
                '6-1': {title: '激光能力测试 / 选项1', component: 'laser_capability'},
                '6-2': {title: '激光能力测试 / 选项2', component: 'laser_capability2'}
            };  
            const menuItem = menuMap[index];
            if (menuItem) {
                console.log(menuItem);
                this.activeMenu = menuItem.title;
                this.loadComponent(menuItem.component);
            }
        },
        //加载组件
        async loadComponent(name){
            if(this.loadedComponents[name]){
                this.currentComponent = name;
                return;
            }
            try{
                //加载html
                const html = await fetch(`/static/components/${name}.html`)
                .then(response => response.text());
                const templateId = `${name}-template`;
                if(!document.getElementById(templateId)){
                    const templateNode = document.createElement('template');
                    templateNode.id = templateId;
                    templateNode.innerHTML = html;
                    document.body.appendChild(templateNode);
                }
                //加载js
                await new Promise((resolve, reject) => {
                    const script = document.createElement('script');
                    script.src = `/static/components/${name}.js`;
                    script.onload = resolve;
                    script.onerror = () =>reject(new Error(`Failed to load script: ${name}.js`));
                    document.head.appendChild(script);
                });
                //更新状态
                this.loadedComponents[name] = true;
                this.currentComponent = name;
                console.log(`Component ${name} loaded`);
            }catch(error){
                console.error(`Failed to load component: ${name}`, error);
            }
        }
    }
});

// 全局错误处理
Vue.config.errorHandler = function(err, vm, info) {
    console.error('Vue error:', err);
    console.error('Error info:', info);
};