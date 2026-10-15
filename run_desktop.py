"""
桌面应用启动脚本
用法: python run_desktop.py
"""
import sys


def check_dependencies():
    """检查依赖"""
    missing = []

    try:
        import tkinter
    except ImportError:
        print("❌ tkinter 未安装")
        print("   Windows: 重新安装Python时勾选 tcl/tk")
        print("   Linux: sudo apt-get install python3-tk")
        sys.exit(1)

    try:
        import matplotlib
    except ImportError:
        missing.append('matplotlib')

    try:
        import pdfplumber
    except ImportError:
        missing.append('pdfplumber')

    if missing:
        print("❌ 缺少以下依赖:")
        for m in missing:
            print(f"   pip install {m}")
        sys.exit(1)


check_dependencies()

# 初始化数据库
from database import Database

db = Database()
if db.get_total_question_count() == 0:
    print("📚 数据库为空，正在导入示例题目...")
    from init_db import SAMPLE_QUESTIONS

    db.batch_add_questions(SAMPLE_QUESTIONS)
    print(f"✅ 已导入 {len(SAMPLE_QUESTIONS)} 道示例题目")

print("=" * 60)
print("🖥️ ICT网络赛道刷题系统 - 桌面版")
print("=" * 60)

from desktop_app import main

main()