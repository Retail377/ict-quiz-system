"""
使用matplotlib生成学习报告图表并导出为图片
可用于生成月度报告、学习曲线等
"""
import matplotlib

matplotlib.use('Agg')  # 无GUI环境使用
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from datetime import datetime
import os

from config import CHART_DIR
from database import Database

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False


class ChartExporter:
    def __init__(self, user_id=None):
        self.db = Database()
        self.user_id = user_id or self.db.get_or_create_user('default_user')

    def export_daily_trend(self, days=30, filename=None):
        """导出近N天答题趋势图"""
        data = self.db.get_daily_stats(self.user_id, days=days)

        if not data:
            print("⚠️ 没有数据可导出")
            return None

        fig, ax = plt.subplots(figsize=(12, 5), dpi=150)

        dates = [d['date'][-5:] for d in data]
        totals = [d['total'] for d in data]
        corrects = [d['correct'] for d in data]

        ax.plot(dates, totals, marker='o', label='答题数',
                color='#667eea', linewidth=2, markersize=6)
        ax.plot(dates, corrects, marker='s', label='正确数',
                color='#67c23a', linewidth=2, markersize=6)

        ax.set_title(f'近{days}天答题趋势', fontsize=16, fontweight='bold')
        ax.set_xlabel('日期', fontsize=12)
        ax.set_ylabel('题数', fontsize=12)
        ax.legend(fontsize=11)
        ax.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()

        if not filename:
            filename = f"daily_trend_{datetime.now().strftime('%Y%m%d')}.png"
        filepath = os.path.join(CHART_DIR, filename)
        fig.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close(fig)

        print(f"✅ 已导出: {filepath}")
        return filepath

    def export_category_pie(self, filename=None):
        """导出各考点答题分布饼图"""
        stats = self.db.get_user_statistics(self.user_id)
        by_cat = stats['by_category']

        if not by_cat:
            print("⚠️ 没有数据可导出")
            return None

        fig, ax = plt.subplots(figsize=(10, 8), dpi=150)

        labels = [c['category'] for c in by_cat]
        sizes = [c['total'] for c in by_cat]
        colors = ['#667eea', '#67c23a', '#e6a23c', '#f56c6c', '#909399']

        wedges, texts, autotexts = ax.pie(
            sizes, labels=labels, colors=colors[:len(labels)],
            autopct='%1.1f%%', startangle=90,
            textprops={'fontsize': 11}
        )

        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')

        ax.set_title('各考点答题分布', fontsize=16, fontweight='bold')
        plt.tight_layout()

        if not filename:
            filename = f"category_pie_{datetime.now().strftime('%Y%m%d')}.png"
        filepath = os.path.join(CHART_DIR, filename)
        fig.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close(fig)

        print(f"✅ 已导出: {filepath}")
        return filepath

    def export_category_bar(self, filename=None):
        """导出各考点正确率柱状图"""
        stats = self.db.get_user_statistics(self.user_id)
        by_cat = stats['by_category']

        if not by_cat:
            print("⚠️ 没有数据可导出")
            return None

        fig, ax = plt.subplots(figsize=(10, 6), dpi=150)

        categories = [c['category'] for c in by_cat]
        accuracies = [
            (c['correct'] / c['total'] * 100) if c['total'] else 0
            for c in by_cat
        ]

        colors = ['#667eea', '#67c23a', '#e6a23c', '#f56c6c', '#909399']
        bars = ax.bar(categories, accuracies, color=colors[:len(categories)])

        ax.set_title('各考点正确率', fontsize=16, fontweight='bold')
        ax.set_xlabel('考点', fontsize=12)
        ax.set_ylabel('正确率(%)', fontsize=12)
        ax.set_ylim(0, 110)
        ax.grid(True, alpha=0.3, axis='y')
        plt.xticks(rotation=30, ha='right')

        for bar, acc in zip(bars, accuracies):
            ax.text(bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 2,
                    f'{acc:.1f}%',
                    ha='center', fontsize=10, fontweight='bold')

        plt.tight_layout()

        if not filename:
            filename = f"category_bar_{datetime.now().strftime('%Y%m%d')}.png"
        filepath = os.path.join(CHART_DIR, filename)
        fig.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close(fig)

        print(f"✅ 已导出: {filepath}")
        return filepath

    def export_monthly_report(self, year=None, month=None, filename=None):
        """导出月度报告（多图表组合）"""
        now = datetime.now()
        year = year or now.year
        month = month or now.month

        harvest = self.db.get_monthly_harvest(self.user_id, year, month)
        stats = self.db.get_user_statistics(self.user_id)

        fig = plt.figure(figsize=(14, 10), dpi=150)

        # 子图1：每日答题量
        ax1 = fig.add_subplot(2, 2, 1)
        if harvest['daily_data']:
            dates = [d['date'][-2:] for d in harvest['daily_data']]
            totals = [d['total'] for d in harvest['daily_data']]
            ax1.bar(dates, totals, color='#667eea')
            ax1.set_title(f'{year}年{month}月 每日答题量', fontsize=13, fontweight='bold')
            ax1.set_xlabel('日期', fontsize=11)
            ax1.set_ylabel('题数', fontsize=11)
            ax1.tick_params(axis='x', rotation=45, labelsize=8)
            ax1.grid(True, alpha=0.3, axis='y')
        else:
            ax1.text(0.5, 0.5, '暂无数据', ha='center', va='center',
                     transform=ax1.transAxes, fontsize=14, color='#999')
            ax1.set_title(f'{year}年{month}月 每日答题量', fontsize=13)

        # 子图2：各考点正确率
        ax2 = fig.add_subplot(2, 2, 2)
        if harvest['by_category']:
            cats = [c['category'][:6] for c in harvest['by_category']]
            accs = [
                (c['correct'] / c['total'] * 100) if c['total'] else 0
                for c in harvest['by_category']
            ]
            colors = ['#667eea', '#67c23a', '#e6a23c', '#f56c6c', '#909399']
            bars = ax2.bar(cats, accs, color=colors[:len(cats)])
            ax2.set_title(f'{year}年{month}月 各考点正确率', fontsize=13, fontweight='bold')
            ax2.set_ylabel('正确率(%)', fontsize=11)
            ax2.set_ylim(0, 110)
            ax2.tick_params(axis='x', rotation=30, labelsize=9)
            ax2.grid(True, alpha=0.3, axis='y')

            for bar, acc in zip(bars, accs):
                ax2.text(bar.get_x() + bar.get_width() / 2,
                         bar.get_height() + 2,
                         f'{acc:.0f}%',
                         ha='center', fontsize=9)
        else:
            ax2.text(0.5, 0.5, '暂无数据', ha='center', va='center',
                     transform=ax2.transAxes, fontsize=14, color='#999')
            ax2.set_title(f'{year}年{month}月 各考点正确率', fontsize=13)

        # 子图3：月度数据概览
        ax3 = fig.add_subplot(2, 2, 3)
        ax3.axis('off')

        summary_text = f"""
        📅 {year}年{month}月 学习报告
        {'=' * 30}

        📝 答题总数: {harvest['total_questions']} 题
        ✅ 正确题数: {harvest['correct_questions']} 题
        🎯 正确率: {harvest['accuracy']:.1f}%
        📆 活跃天数: {harvest['active_days']} 天

        {'=' * 30}
        📊 累计数据

        📚 总答题数: {stats['total_questions']} 题
        🎯 总正确率: {stats['accuracy']:.1f}%
        📅 打卡天数: {stats['check_in_days']} 天
        ❌ 错题数: {stats['wrong_count']} 题
        ⭐ 收藏数: {stats['favorite_count']} 题
        """

        ax3.text(0.1, 0.9, summary_text, transform=ax3.transAxes,
                 fontsize=11, verticalalignment='top',
                 fontfamily='SimHei',
                 bbox=dict(boxstyle='round', facecolor='#f8f9fa',
                           edgecolor='#667eea', linewidth=2))

        # 子图4：累计各考点正确率
        ax4 = fig.add_subplot(2, 2, 4)
        if stats['by_category']:
            cats = [c['category'][:6] for c in stats['by_category']]
            accs = [
                (c['correct'] / c['total'] * 100) if c['total'] else 0
                for c in stats['by_category']
            ]
            colors = ['#667eea', '#67c23a', '#e6a23c', '#f56c6c', '#909399']
            bars = ax4.barh(cats, accs, color=colors[:len(cats)])
            ax4.set_title('累计各考点正确率', fontsize=13, fontweight='bold')
            ax4.set_xlabel('正确率(%)', fontsize=11)
            ax4.set_xlim(0, 110)
            ax4.grid(True, alpha=0.3, axis='x')

            for bar, acc in zip(bars, accs):
                ax4.text(bar.get_width() + 2,
                         bar.get_y() + bar.get_height() / 2,
                         f'{acc:.0f}%',
                         va='center', fontsize=9)
        else:
            ax4.text(0.5, 0.5, '暂无数据', ha='center', va='center',
                     transform=ax4.transAxes, fontsize=14, color='#999')
            ax4.set_title('累计各考点正确率', fontsize=13)

        plt.suptitle(f'ICT刷题系统 - {year}年{month}月学习报告',
                     fontsize=16, fontweight='bold', y=0.98)
        plt.tight_layout()

        if not filename:
            filename = f"monthly_report_{year}{month:02d}.png"
        filepath = os.path.join(CHART_DIR, filename)
        fig.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close(fig)

        print(f"✅ 月度报告已导出: {filepath}")
        return filepath


if __name__ == '__main__':
    exporter = ChartExporter()
    print("=" * 50)
    print("📊 图表导出工具")
    print("=" * 50)

    exporter.export_daily_trend(days=30)
    exporter.export_category_pie()
    exporter.export_category_bar()
    exporter.export_monthly_report()

    print("\n✅ 所有图表已导出到:", CHART_DIR)