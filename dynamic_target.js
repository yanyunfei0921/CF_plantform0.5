if (!Vue.options.components['dynamic_target']) {
    Vue.component('dynamic_target', {
        template: '#dynamic_target-template',
        data() {
            return {
                selectedSpectrum: 'infrared', // 默认选择红外光谱
                intensity: 50,  // 默认光强度
                selectedTarget: 'target1', // 默认靶标
                selectedMotion: 'circular', // 默认运动模式
            };
        },
        methods: {
            initSystem() {
                alert("系统初始化完成");
            },
            startSimulation() {
                alert(`开始模拟：\n光谱: ${this.selectedSpectrum}\n光强度: ${this.intensity}\n靶标: ${this.selectedTarget}\n运动模式: ${this.selectedMotion}`);
            }
        },
        mounted() {
            console.log("Dynamic Target Component Mounted");
        },
        watch: {
            intensity(newValue) {
                console.log("光强度调整为:", newValue);
            }
        }
    });
}
