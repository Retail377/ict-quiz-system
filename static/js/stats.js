// 统计页面辅助脚本（可选，主要逻辑在stats.html内联）
// 用于导出图表为图片等功能

function exportChart(chartId, filename) {
    const chart = echarts.getInstanceByDom(document.getElementById(chartId));
    if (!chart) return;

    const url = chart.getDataURL({
        type: 'png',
        pixelRatio: 2,
        backgroundColor: '#fff'
    });

    const link = document.createElement('a');
    link.download = filename || 'chart.png';
    link.href = url;
    link.click();
}

// 导出所有图表
function exportAllCharts() {
    const charts = ['dailyChart', 'categoryChart', 'categoryBarChart'];
    charts.forEach((id, index) => {
        setTimeout(() => {
            exportChart(id, `chart_${index + 1}.png`);
        }, index * 500);
    });
}