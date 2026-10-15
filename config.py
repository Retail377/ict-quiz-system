import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
PDF_DIR = os.path.join(DATA_DIR, 'pdfs')
EXPORT_DIR = os.path.join(BASE_DIR, 'exports')
CHART_DIR = os.path.join(EXPORT_DIR, 'charts')

DB_PATH = os.path.join(DATA_DIR, 'quiz.db')

# 确保目录存在
for d in [DATA_DIR, PDF_DIR, EXPORT_DIR, CHART_DIR]:
    os.makedirs(d, exist_ok=True)

# Flask配置
SECRET_KEY = 'ict-quiz-system-secret-key-2024'
DEBUG = True

# 分页
PAGE_SIZE = 20