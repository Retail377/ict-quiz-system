"""
Web应用启动脚本
用法: python run_web.py
"""
import os
import sys
import webbrowser
import threading
import time


# 检查依赖
def check_dependencies():
    """检查依赖是否安装"""
    missing = []

    try:
        import flask
    except ImportError:
        missing.append('Flask')

    try:
        import pdfplumber
    except ImportError:
        missing.append('pdfplumber')

    try:
        import matplotlib
    except ImportError:
        missing.append('matplotlib')

    if missing:
        print("❌ 缺少以下依赖，请先安装:")
        for m in missing:
            print(f"   pip install {m}")
        print("\n或者一键安装所有依赖:")
        print("   pip install -r requirements.txt.txt")
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


# 延迟打开浏览器
def open_browser():
    time.sleep(1.5)
    webbrowser.open('http://127.0.0.1:5000')


print("=" * 60)
print("🌐 ICT网络赛道刷题系统 - Web版")
print("=" * 60)
print("📍 访问地址: http://127.0.0.1:5000")
print("📍 按 Ctrl+C 停止服务")
print("=" * 60)

threading.Thread(target=open_browser, daemon=True).start()

from app import app

app.run(host='0.0.0.0', port=5000, debug=False)