/** Graphic Display of Detection Result**/
/** written by J.CHOU@ate-lab 2022-07-16**/
function sleep(time){
    return new Promise((resolve)=>setTimeout(resolve,time));
}

new function(){
    Vue.component(
        'ate-graphic-result', 
        {
            props: ['result', 'timeData', 'rows', 'columns'],
            template: `
                <div>
                    <el-row>
                        <el-col :span="22">
                            <el-button :type="getItemType(resultItem.anomRatio)"
                                v-for="resultItem in result.slice(row_actual*setDefault(columns,4),(row_actual+setDefault(rows,2))*setDefault(columns,4))" size="mini"
                                @click="clickDetail(resultItem)">
                                <div>{{ resultItem.name }}</div>
                                <div>
                                    <el-progress :show-text="false" :stroke-width="15" :percentage="resultItem.anomRatio*100"
                                        :color="getItemColor(resultItem.anomRatio)"></el-progress>
                                </div>
                            </el-button>
                        </el-col>
                        <el-col :span="2" v-if="result.length > setDefault(columns,4)*setDefault(rows,2)">
                            <el-slider v-model="row_actual_ratio" :format-tooltip="formatTooltip" vertical>
                            </el-slider>
                        </el-col>
                    </el-row>
                    <el-drawer :visible.sync="dialogItemShow" :title="clickItemInfo.name+'详情信息'" width="600px">
                        <el-row>
                            <el-col :span="15">
                                <el-descriptions title="基本信息" :column="1" border>
                                    <el-descriptions-item :label="infoItem.label" v-for="infoItem,count in clickItemInfo.detailInfo" :key="count">
                                        <span v-text="infoItem.value"></span>
                                    </el-descriptions-item>
                                </el-descriptions>
                            </el-col>
                            <el-col :span="8" :offset="1">
                                <el-progress type="circle" :percentage="clickItemInfo.anomRatio*100"
                                    :color="getItemColor(clickItemInfo.anomRatio)"></el-progress>
                            </el-col>
                        </el-row>
                        <div ref="dialogItemArea" style="height: 300px; width: 550px;"></div>
                    </el-drawer>
                </div>
            `,
            data() {
                return {
                    row_actual: 0,
                    row_actual_ratio: 1,
                    clickItemInfo: {},
                    dialogItemShow: false,
                }
            },
            watch: {
                row_actual_ratio(val) {
                    let rows_all = Math.ceil(this.result.length / this.setDefault(this.columns,4));
                    this.row_actual = Math.round(rows_all * (1 - this.row_actual_ratio / 100));
                }
            },
            methods: {
                setDefault(val, val_default){
                    if (!val){
                        return val_default;
                    }else{
                        return val;
                    }
                },
                getItemType(ratio) {
                    if (ratio == 0) {
                        return "success"
                    } else if (ratio < 0.3) {
                        return "warning"
                    } else {
                        return "danger"
                    }
                },
                getItemColor(ratio) {
                    if (ratio == 0) {
                        return "green"
                    } else if (ratio < 0.3) {
                        return "orange"
                    } else {
                        return "red"
                    }
                },
                clickDetail(resultItem) {
                    this.clickItemInfo = resultItem;
                    this.dialogItemShow = true;
                    this.$nextTick(()=>{
                        this.initZone();
                    })
                },
                formatTooltip(val) {
                    let rows_all = Math.ceil(this.result.length / this.setDefault(this.columns,4));
                    return Math.round(rows_all * (1 - val / 100));
                },
                initZone() {
                    let vm = this;
                    var itemZone = echarts.init(this.$refs.dialogItemArea);
                    itemZone.setOption({
                        title: {
                            text: '异常分数演化情况',
                            left: '1%'
                        },
                        tooltip: {
                            trigger: 'axis'
                        },
                        grid: {
                            left: '5%',
                            right: '15%',
                            bottom: '10%'
                        },
                        xAxis: {
                            data: vm.timeData
                        },
                        yAxis: {},
                        toolbox: {
                            right: 10,
                            feature: {
                                dataZoom: {
                                    yAxisIndex: 'none'
                                },
                                restore: {},
                                saveAsImage: {}
                            }
                        },
                        dataZoom: [
                            {},
                            {
                                type: 'inside'
                            }
                        ],
                        visualMap: {
                            top: 50,
                            right: 10,
                            pieces: [
                                {
                                    gt: 0,
                                    lte: 0.1,
                                    color: '#93CE07'
                                },
                                {
                                    gt: 0.1,
                                    lte: 0.5,
                                    color: '#FBDB0F'
                                },
                                {
                                    gt: 0.5,
                                    lte: 0.9,
                                    color: '#FC7D02'
                                },
                                {
                                    gt: 0.9,
                                    color: '#FD0100'
                                },
                            ]
                        },
                        series: {
                            name: '异常分数',
                            type: 'line',
                            data: vm.clickItemInfo.scoreInfo,
                            markLine: {
                                silent: true,
                                lineStyle: {
                                    color: '#333'
                                },
                                data: [
                                    {
                                        yAxis: 0.1
                                    },
                                    {
                                        yAxis: 0.5
                                    },
                                    {
                                        yAxis: 0.9
                                    }]
                            }
                        }
                    });
                }
            }
        });
    Vue.component(
        'ate-panel-result', 
        {
            props: ['result'],
            template: `
                <div>
                    <div ref="drawZone" style="height: 400px; width: 1200px;"></div>
                    <el-drawer :visible.sync="clickDialog" title="详情">
                        <el-collapse v-model="dialogActiveName">
                            <el-collapse-item :title="modelItem.name" :name="count" v-for="modelItem, count in clickItem" :key="count">
                                <el-descriptions title="" border :column="1">
                                    <el-descriptions-item :label="detailItem.label" v-for="detailItem,count_ in modelItem.info" :key="count_">
                                        <span v-text="detailItem.value"></span>
                                    </el-descriptions-item>
                                </el-descriptions>
                            </el-collapse-item>
                        </el-collapse>
                    </el-drawer>
                </div>
            `,
            data() {
                return {
                    dialogActiveName: [],
                    clickDialog: false,
                    clickItem: [],
                    itemMax: 0
                }
            },
            mounted(){
                this.initZone()
            },
            methods: {
                initZone() {
                    let vm = this;
                    var itemZone = echarts.init(this.$refs.drawZone);
                    let resultData = this.result.map(function (item) {
                        if (item.itemInfo[2]>vm.itemMax){
                            vm.itemMax = item.itemInfo[2];
                        }
                        return [item.itemInfo[0],item.itemInfo[1],item.itemInfo[2]||"-"];
                    });
                    itemZone.setOption({
                        tooltip: {
                            triggerOn: 'click',
                        },
                        formatter: function(params){
                            vm.clickItem = vm.result[params.dataIndex].modelInfo;
                            vm.clickDialog = true;
                            vm.dialogActiveName = Array(vm.clickItem.length).fill(1).map((v,k)=>k);
                            return 
                        },
                        grid: {
                            height: '50%',
                            top: '10%'
                        },
                        xAxis: {
                            type: 'category',
                            name: '预测异常时间',
                            data: ["1周以内","+1周","+2周","+3周","+4周",
                                    "+1月","+2月","+3月","+4月","+5月","+6月","+7月",
                                    "+8月","+9月","+10月","+11月","+12月","1年以后"],
                            splitArea: {
                                show: true
                            },
                            axisLabel:{
                                show: true,
                                interval: 0,
                            },
                        },
                        yAxis: {
                            type: 'category',
                            name: '预测置信程度',
                            data: ['低等', '中低','中等','中高','高等'],
                            splitArea: {
                                show: true
                            }
                        },
                        visualMap: {
                            min: 0,
                            max: vm.itemMax,
                            calculable: true,
                            orient: 'horizontal',
                            left: 'center',
                            bottom: '15%',
                            inRange: {
                                color: ['Green','Red']
                            }
                        },
                        series: [
                            {
                            name: 'detail',
                            type: 'heatmap',
                            data: resultData,
                            label: {
                                show: true
                            },
                            emphasis: {
                                itemStyle: {
                                shadowBlur: 10,
                                shadowColor: 'rgba(0, 0, 0, 0.5)'
                                }
                            }
                            }
                        ]
                    });
                }
            }
        });
    Vue.component(
        'ate-sunburst-result', 
        {
            props: ['result'],
            template: `
                <div>
                    <div ref="drawZone" style="height: 400px; width: 1200px;"></div>
                </div>
            `,
            data() {
                return {
                }
            },
            mounted() {
                this.initZone()
            },
            methods: {
                markRadicalLeave(obj, level, weight){
                    if (!level){
                        level = 0;
                    }
                    if (!weight && obj.weight != 0){
                        weight = 1;
                    }
                    if (!obj.weight && obj.weight != 0){
                        obj.weight = 1
                    }
                    obj.value = weight*obj.weight;
                    obj.name = obj.name
                    obj.symbolSize = Math.max(25 - 5 * level, 5)
                    obj.level = level;
                    if (obj.score > 85){
                        obj.itemStyle = {
                                    color: "lightgreen",
                                    borderColor: "lightgreen",
                                    borderWidth: 3
                                };
                    } else if (obj.score > 60){
                        obj.itemStyle = {
                                    color: "lightyellow",
                                    borderColor: "lightyellow",
                                    borderWidth: 3
                                };
                    } else if (obj.score > 25){
                        obj.itemStyle = {
                                    color: "wheat",
                                    borderColor: "wheat",
                                    borderWidth: 3
                                };
                    } else {
                        obj.itemStyle = {
                                    color: "lightcoral",
                                    borderColor: "lightcoral",
                                    borderWidth: 3
                                };
                    }
                    if (obj.children){
                        for (child of obj.children){
                            this.markRadicalLeave(child, level+1, obj.value);
                        }
                    }
                },
                initZone() {
                    let vm = this;
                    this.markRadicalLeave(this.result)
                    var itemZone = echarts.init(this.$refs.drawZone);
                    itemZone.setOption({
                        tooltip: {
                            triggerOn: 'mousemove',
                            enterable: true
                        },
                        formatter: function (params) {
                            return "<h3>" + params.name + "</h3><p>健康分数:&nbsp;" + params.data.score + "</p><p>影响权重:&nbsp;" + params.data.weight*100 + "%</p>"
                        },
                        series: [
                            {
                                type: 'sunburst',
                                data: [vm.result],
                                top: '18%',
                                bottom: '14%',
                                layout: 'radial',
                                symbol: 'emptyCircle',
                                symbolSize: 7,
                                initialTreeDepth: 3,
                                animationDurationUpdate: 750,
                                emphasis: {
                                    focus: 'descendant'
                                },
                                radius: [60, '90%'],
                                itemStyle: {
                                    borderRadius: 7
                                },
                            }
                        ]
                    });
                }
            }
        });
    Vue.component(
        'ate-detect-item-result', 
        {
            props: ['result', 'timedata', 'pnames', 'pdata'],
            template: `
                <div>
                    <el-row>
                        <el-col :span="15">
                            <el-descriptions :title="result.name+'详情信息'" :column="1" border>
                                <el-descriptions-item :label="infoItem.name" :key="count" v-for="infoItem,count in result.detailInfo">
                                    <span v-text="infoItem.value"></span>
                                </el-descriptions-item>
                            </el-descriptions>
                        </el-col>
                        <el-col :span="8" :offset="1">
                            <el-progress type="circle" :percentage="Math.round(result.anomRatio*10000)/100"
                                :color="getItemColor(result.anomRatio)">
                            </el-progress>
                        </el-col>
                    </el-row>
                    <div :ref="'dialogdectscoreareaby'+result.name" :style="{width: GLw, height: GLh}"></div>
                    <div :ref="'dialogdectitemareaby'+pa" :key="pa" v-for="pa of result.relatParas" :style="{width: GLw, height: GLh}"></div>
                </div>
            `,
            data() {
                return {
                    //GLh: '200px',
                    //GLw: '800px',
                }
            },
            created(){
                this.GLh = Math.min(window.innerHeight/5, 200) + 'px';
                this.GLw = window.innerWidth + 'px';
            },
            mounted(){
                sleep(0).then(()=>{
                    this.initScoreZone();
                    this.result.relatParas.forEach((pa, k)=>{
                        this.initItemZone(pa, k);
                    })
                })
            },
            methods: {
                getItemColor(ratio) {
                    if (ratio == 0) {
                        return "green"
                    } else if (ratio < 0.2) {
                        return "orange"
                    } else {
                        return "red"
                    }
                },
                initScoreZone() {
                    var itemZone = echarts.init(this.$refs['dialogdectscoreareaby'+this.result.name]);
                    itemZone.setOption({
                        title: {
                            text: '异常分数演化情况',
                            left: '1%'
                        },
                        tooltip: {
                            trigger: 'axis'
                        },
                        grid: {
                            left: '5%',
                            right: '15%',
                            bottom: '10%'
                        },
                        xAxis: {
                            data: this.timedata
                        },
                        yAxis: {},
                        toolbox: {
                            right: 10,
                            feature: {
                                dataZoom: {
                                    yAxisIndex: 'none'
                                },
                                restore: {},
                                saveAsImage: {}
                            }
                        },
                        dataZoom: [
                            {
                                type: 'inside'
                            },
                            {
                                type: 'inside'
                            }
                        ],
                        visualMap: {
                            top: 50,
                            right: 10,
                            precision: 1,
                            pieces: [
                                {
                                    gt: 0,
                                    lte: 0.1,
                                    color: '#93CE07'
                                },
                                {
                                    gt: 0.1,
                                    lte: 0.5,
                                    color: '#FBDB0F'
                                },
                                {
                                    gt: 0.5,
                                    lte: 0.9,
                                    color: '#FC7D02'
                                },
                                {
                                    gt: 0.9,
                                    color: '#FD0100'
                                },
                            ]
                        },
                        series: {
                            name: '异常分数',
                            type: 'line',
                            data: this.result.scoreList,
                        }
                    });
                },
                initItemZone(pa,k) {
                    let itemData = [{
                            name: pa+'|参数曲线',
                            type: 'line',
                            data: this.pdata[this.pnames.indexOf(pa)],
                        }];
                    if (this.result.supportData){
                        this.result.supportData.forEach((paraItem, ki)=>{
                            itemData.push({
                                name: this.result.supportLabel ? this.result.supportLabel[ki] : '辅助线' + ki,
                                type: 'line',
                                data: this.result.supportData[k][ki],
                            })
                        })
                    }
                    var itemZone = echarts.init(this.$refs['dialogdectitemareaby'+pa][0]);
                    itemZone.setOption({
                        title: {
                            text: pa+'|检测详情',
                            left: '1%'
                        },
                        tooltip: {
                            trigger: 'axis'
                        },
                        grid: {
                            left: '5%',
                            right: '15%',
                            bottom: '10%'
                        },
                        xAxis: {
                            data: this.timedata
                        },
                        yAxis: {},
                        toolbox: {
                            right: 10,
                            feature: {
                                dataZoom: {
                                    yAxisIndex: 'none'
                                },
                                restore: {},
                                saveAsImage: {}
                            }
                        },
                        dataZoom: [
                            {
                                type: 'inside'
                            },
                            {
                                type: 'inside'
                            }
                        ],
                        legend: {
                            orient: 'vertical',
                            right: 10,
                            top: 'center'
                        },
                        series: itemData
                    });
                }
            }
        });
    Vue.component(
        'ate-predict-panel-result', 
        {
            props: ['result', 'timedata', 'pnames', 'pdata'],
            template: `
                <div>
                    <div ref="dialogscorearea" style="height: 400px; width: 1000;"></div>
                    <el-drawer :visible.sync="clickDialog" title="详情" :size="GLw">
                        <el-collapse v-model="dialogActiveName">
                            <el-collapse-item :title="modelItem.name" :name="count" :key="count" v-for="modelItem, count in clickItem">
                                <el-descriptions title="" border :column="2">
                                    <el-descriptions-item :label="detailItem.name || detailItem.label" :key="count_" v-for="detailItem, count_ in modelItem.info">
                                        <span v-text="detailItem.value"></span>
                                    </el-descriptions-item>
                                </el-descriptions>
                                <div :ref="'dialogpredcurveareaby'+modelItem.name" :style="{width: GLw, height: GLh}"></div>
                                <div :ref="modelItem.scoreData?'dialogitemareaby'+count+'model':'dialogitemareaby'+count+pa" :key="count+pa" v-for="pa of modelItem.relatParas" :style="{width: GLw, height: GLh}"></div>
                            </el-collapse-item>
                        </el-collapse>
                    </el-drawer>
                </div>
            `,
            data() {
                return {
                    dialogActiveName: [],
                    clickDialog: false,
                    clickItem: [],
                    itemMax: 0,
                }
            },
            created(){
                this.GLh = Math.min(window.innerHeight/5, 200) + 'px';
                this.GLw = (window.innerWidth*0.6) + 'px';
            },
            mounted(){
                sleep(0).then(()=>{
                    this.initScoreZone();
                })
            },
            methods: {
                initScoreZone() {
                    let vm = this;
                    var itemZone = echarts.init(this.$refs.dialogscorearea);
                    let resultData = this.result.map(item=>{
                        if (item.itemInfo[2]>vm.itemMax){
                            vm.itemMax = item.itemInfo[2];
                        }
                        return [item.itemInfo[0],item.itemInfo[1],item.itemInfo[2]||"-"];
                    });
                    itemZone.setOption({
                        tooltip: {
                            triggerOn: 'click',
                        },
                        formatter: function(params){
                            vm.clickItem = vm.result[params.dataIndex].modelInfo;
                            vm.clickDialog = true;
                            vm.dialogActiveName = Array(vm.clickItem.length).fill(1).map((v,k)=>k);
                            sleep(0).then(()=>{
                                vm.clickItem.forEach((itemDetail, count)=>{
                                    vm.initItemTitleZone(itemDetail);
                                    if (typeof itemDetail.scoreData != 'undefined'){
                                        itemDetail.scoreData.forEach((pa, k)=>{
                                            vm.initItemZone("model", k, itemDetail, count, "score");
                                        })
                                    }else{
                                        itemDetail.relatParas.forEach((pa, k)=>{
                                            vm.initItemZone(pa, k, itemDetail, count, "para");
                                        })
                                    }
                                })
                            })
                            return 
                        },
                        grid: {
                            height: '50%',
                            top: '10%'
                        },
                        xAxis: {
                            type: 'category',
                            name: '预测异常时间',
                            data: ["1周以内","+1周","+2周","+3周","+4周",
                                    "+1月","+2月","+3月","+4月","+5月","+6月","+7月",
                                    "+8月","+9月","+10月","+11月","+12月","1年以后"],
                            splitArea: {
                                show: true
                            },
                            axisLabel:{
                                show: true,
                                interval: 0,
                            },
                        },
                        yAxis: {
                            type: 'category',
                            name: '预测置信程度',
                            data: ['低等', '中低','中等','中高','高等'],
                            splitArea: {
                                show: true
                            }
                        },
                        visualMap: {
                            min: 0,
                            max: vm.itemMax,
                            calculable: true,
                            orient: 'horizontal',
                            left: 'center',
                            bottom: '15%',
                            inRange: {
                                color: ['Green','Red']
                            }
                        },
                        series: [
                            {
                            name: 'detail',
                            type: 'heatmap',
                            data: resultData,
                            label: {
                                show: true
                            },
                            emphasis: {
                                itemStyle: {
                                shadowBlur: 10,
                                shadowColor: 'rgba(0, 0, 0, 0.5)'
                                }
                            }
                            }
                        ]
                    });
                },
                initItemTitleZone(itemDetail) {
                    let vm = this;
                    let itemData = []
                    var timeData = this.timedata.slice(Math.max(this.timedata.length-1000,0),this.timedata.length);
                    if (itemDetail.supportData){
                        itemDetail.supportData.forEach((paraItem, ki)=>{
                            itemData.push({
                                name: itemDetail.supportLabel ? itemDetail.supportLabel[ki] : '辅助线' + ki,
                                type: 'line',
                                data: paraItem,
                            })
                            if (paraItem.length > timeData.length){
                                timeData = timeData.concat(Array(paraItem.length-timeData.length).fill(''))
                            }
                        })
                    }
                    var itemZone = echarts.init(this.$refs['dialogpredcurveareaby'+itemDetail.name][0]);
                    itemZone.setOption({
                        tooltip: {
                            trigger: 'axis'
                        },
                        grid: {
                            left: '5%',
                            right: '15%',
                            bottom: '10%'
                        },
                        xAxis: {
                            data: timeData
                        },
                        yAxis: {},
                        toolbox: {
                            right: 10,
                            feature: {
                                dataZoom: {
                                    yAxisIndex: 'none'
                                },
                                restore: {},
                                saveAsImage: {}
                            }
                        },
                        dataZoom: [
                            {
                                type: 'inside'
                            },
                            {
                                type: 'inside'
                            }
                        ],
                        legend: {
                            orient: 'vertical',
                            right: 10,
                            top: 'center'
                        },
                        series: itemData
                    });
                },
                initItemZone(pa, k, itemDetail, count, mode) {
                    let vm = this;
                    let itemData = []
                    if (mode === "score"){
                        itemData.push({
                            name: '异常演化曲线',
                            type: 'line',
                            data: itemDetail.scoreData[k],
                        });
                    }else{
                        itemData.push({
                            name: pa+'|参数曲线',
                            type: 'line',
                            data: this.pdata[this.pnames.indexOf(pa)],
                        });
                    }
                    var timeData = this.timedata;
                    /**if (itemDetail.supportData){
                        itemDetail.supportData[k].forEach((paraItem, ki)=>{
                            itemData.push({
                                name: itemDetail.supportLabel ? itemDetail.supportLabel[ki] : '辅助线' + ki,
                                type: 'line',
                                data: paraItem,
                            })
                            if (paraItem.length > timeData.length){
                                timeData = timeData.concat(Array(paraItem.length-timeData.length).fill(''))
                            }
                        })
                    }**/
                    var itemZone = echarts.init(this.$refs['dialogitemareaby'+count+pa][0]);
                    itemZone.setOption({
                        tooltip: {
                            trigger: 'axis'
                        },
                        grid: {
                            left: '5%',
                            right: '15%',
                            bottom: '10%'
                        },
                        xAxis: {
                            data: timeData
                        },
                        yAxis: {},
                        toolbox: {
                            right: 10,
                            feature: {
                                dataZoom: {
                                    yAxisIndex: 'none'
                                },
                                restore: {},
                                saveAsImage: {}
                            }
                        },
                        dataZoom: [
                            {
                                type: 'inside'
                            },
                            {
                                type: 'inside'
                            }
                        ],
                        legend: {
                            orient: 'vertical',
                            right: 10,
                            top: 'center'
                        },
                        series: itemData
                    });
                }
            }
        });
    Vue.component(
        'ate-general-graphic-display', 
        {
            props: {
                result: {
                    type: Array,
                    required: true,
                },
                rows: {
                    type: Number,
                    default: 6,
                },
                columns: {
                    type: Number,
                    default: 2,
                },
                localsrc: {
                    type: String,
                    required: true,
                },
            },
            template: `
                <div ref="graphGL" style="width: 100%;">
                    <el-row>
                        <el-col :span="22">
                            <el-badge :value="resultItem.faultNum" :type="getItemType(resultItem.faultNum, resultItem.maxNum)" 
                                v-for="(resultItem, k) in result.slice(rowActual*columns,(rowActual+rows)*columns)" :key="k" :style="{margin:'10px', width:localw+'px!important'}">
                                <el-button :type="getItemType(resultItem.faultNum, resultItem.maxNum)" size="mini" :style="{width:localw+'px!important'}"
                                        @click="clickDetail(k+rowActual*columns)">
                                    <span v-if="resultItem.descript[0].value.length<Math.round(localw/15)">{{ resultItem.descript[0].value }}</span>
                                    <el-popover placement="right" trigger="hover" v-else>
                                        <span style="width: 55px; height: 50px; font-size: 10px!important; overflow-y:auto;">
                                            {{ resultItem.descript[0].value }}
                                        </span>
                                        <span slot="reference" :style="{width:localw+'px!important', 'font-size': '10px!important'}">
                                            {{ resultItem.descript[0].value.slice(0,Math.round(localw/15)-2) }}...
                                        </span>
                                    </el-popover>
                                </el-button>
                            </el-badge>
                        </el-col>
                        <el-col :offset="1" :span="1" v-if="result.length > rows*columns">
                            <el-slider v-model="rowActualRatio" :format-tooltip="formatTooltip" vertical size="mini">
                            </el-slider>
                        </el-col>
                    </el-row>
                    <el-drawer :visible.sync="dialogItemShow" :title="'['+dataArgs.descript[0].value+']-详情信息'" size="GLw" v-if="clickItemInd!=-1">
                        <el-descriptions title="基本信息" :column="2" border>
                            <el-descriptions-item :label="infoItem.name" v-for="(infoItem, k) in dataArgs.descript" :key="k">
                                <span v-text="infoItem.value"></span>
                            </el-descriptions-item>
                        </el-descriptions>
                        <iframe :src="localsrc+'/#/query?data-args='+encodeURI(JSON.stringify(dataArgs.data))" :style="{width: GLw*0.95+'px', height: GLh+'px'}"></iframe>
                    </el-drawer>
                </div>
            `,
            data() {
                return {
                    rowActual: 0,
                    rowActualRatio: 1,
                    clickItemInd: -1,
                    dialogItemShow: false,
                    framePlamb: null,
                    localw: 150,
                    dataArgs: {descript: [{name: null, value: null}], data: []},
                }
            },
            created() {
                if (!this.rows){
                    this.rows = 2;
                }
                if (!this.columns){
                    this.columns = 4;
                }
                this.rowsAll = Math.ceil(this.result.length / this.columns);
                this.GLw = window.innerWidth * 0.75;
                this.GLh = window.innerHeight * 0.75;
            },
            watch: {
                rowActualRatio(val,newVal) {
                    this.rowActual = Math.round(this.rowsAll * (1 - this.rowActualRatio / 100));
                },
                result(val,newVal){
                    if (this.clickItemInd != -1){
                        this.dataArgs = this.result[this.clickItemInd];
                        this.$forceUpdate();
                    }
                },
                dialogItemShow(val,newVal){
                    if (!this.dialogItemShow){
                        this.clickItemInd = -1
                    }
                }
            },
            mounted(){
                this.localw = Math.round(this.$refs.graphGL.clientWidth*0.8/this.columns) - 5;
            },
            methods: {
                getItemType(inNum, allNum) {
                    if (inNum == 0) {
                        return "success"
                    } else if (inNum < 0.5*allNum) {
                        return "warning"
                    } else {
                        return "danger"
                    }
                },
                clickDetail(index) {
                    this.clickItemInd = index;
                    this.dialogItemShow = true;
                    sleep(0).then(()=>{
                        this.dataArgs = this.result[index];
                    })
                },
                formatTooltip(val) {
                    return Math.round(this.rows_all * (1 - val / 100));
                }
            }
        });
  }