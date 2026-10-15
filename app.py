from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from datetime import datetime
import os
import json
from config import SECRET_KEY, DEBUG, PDF_DIR
from database import Database
from pdf_importer import PDFImporter
from flask import send_from_directory


app = Flask(__name__)
app.secret_key = SECRET_KEY

db = Database()

@app.route('/sw.js')
def service_worker():
    return send_from_directory('.', 'sw.js', mimetype='application/javascript')


def get_current_user_id():
    """获取当前用户ID（简化处理，默认default_user）"""
    if 'user_id' not in session:
        user_id = db.get_or_create_user('default_user')
        session['user_id'] = user_id
    return session['user_id']


# ============ 页面路由 ============

@app.route('/')
def index():
    user_id = get_current_user_id()
    stats = db.get_user_statistics(user_id)
    categories = db.get_categories()
    total_questions = db.get_total_question_count()
    continuous_days = db.get_continuous_days(user_id)

    return render_template('index.html',
                           stats=stats,
                           categories=categories,
                           total_questions=total_questions,
                           continuous_days=continuous_days)


@app.route('/quiz')
def quiz():
    user_id = get_current_user_id()
    mode = request.args.get('mode', 'random')
    category = request.args.get('category', '全部')
    count = int(request.args.get('count', 10))

    if mode == 'wrong':
        questions = db.get_wrong_questions(user_id)[:count]
    elif mode == 'favorite':
        questions = db.get_favorites(user_id)[:count]
    else:
        questions = db.get_random_questions(count, category)

    return render_template('quiz.html',
                           questions=questions,
                           mode=mode,
                           category=category)


@app.route('/wrong')
def wrong():
    user_id = get_current_user_id()
    questions = db.get_wrong_questions(user_id)
    return render_template('wrong.html', questions=questions)


@app.route('/favorites')
def favorites():
    user_id = get_current_user_id()
    questions = db.get_favorites(user_id)
    return render_template('favorites.html', questions=questions)


@app.route('/stats')
def stats():
    user_id = get_current_user_id()
    stats_data = db.get_user_statistics(user_id)
    daily_stats = db.get_daily_stats(user_id, days=30)
    return render_template('stats.html',
                           stats=stats_data,
                           daily_stats=json.dumps(daily_stats))


@app.route('/calendar')
def calendar():
    user_id = get_current_user_id()
    now = datetime.now()
    year = int(request.args.get('year', now.year))
    month = int(request.args.get('month', now.month))

    check_ins = db.get_check_in_calendar(user_id, year, month)
    harvest = db.get_monthly_harvest(user_id, year, month)

    return render_template('calendar.html',
                           check_ins=check_ins,
                           harvest=harvest,
                           year=year,
                           month=month)


# ============ API 接口 ============

@app.route('/api/submit_answer', methods=['POST'])
def submit_answer():
    user_id = get_current_user_id()
    data = request.get_json()
    question_id = data['question_id']
    user_answer = data['answer'].strip().upper()
    mode = data.get('mode', 'random')
    time_spent = data.get('time_spent', 0)

    question = db.get_question_by_id(question_id)
    if not question:
        return jsonify({'error': '题目不存在'}), 404

    correct_answer = question['answer'].strip().upper()

    # 判断对错
    if question['type'] == 'multiple':
        user_set = set(re.sub(r'[^A-D]', '', user_answer))
        correct_set = set(re.sub(r'[^A-D]', '', correct_answer))
        is_correct = user_set == correct_set
    else:
        is_correct = user_answer == correct_answer

    # 保存记录
    db.save_answer_record(user_id, question_id, user_answer, is_correct, mode, time_spent)
    db.update_check_in(user_id, is_correct)

    if is_correct:
        db.update_wrong_streak(user_id, question_id)
    else:
        db.add_to_wrong_questions(user_id, question_id)

    return jsonify({
        'is_correct': is_correct,
        'correct_answer': correct_answer,
        'explanation': question.get('explanation', ''),
        'content': question['content']
    })


@app.route('/api/toggle_favorite', methods=['POST'])
def toggle_favorite():
    user_id = get_current_user_id()
    data = request.get_json()
    question_id = data['question_id']
    result = db.toggle_favorite(user_id, question_id)
    return jsonify({'is_favorite': result})


@app.route('/api/check_favorite/<int:question_id>')
def check_favorite(question_id):
    user_id = get_current_user_id()
    result = db.is_favorite(user_id, question_id)
    return jsonify({'is_favorite': result})


@app.route('/api/remove_wrong', methods=['POST'])
def remove_wrong():
    user_id = get_current_user_id()
    data = request.get_json()
    question_id = data['question_id']
    db.remove_from_wrong(user_id, question_id)
    return jsonify({'success': True})


@app.route('/api/stats_data')
def stats_data():
    user_id = get_current_user_id()
    daily_stats = db.get_daily_stats(user_id, days=30)
    stats_data = db.get_user_statistics(user_id)
    return jsonify({
        'daily': daily_stats,
        'summary': stats_data
    })


@app.route('/api/upload_pdf', methods=['POST'])
def upload_pdf():
    if 'file' not in request.files:
        return jsonify({'error': '没有文件'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '文件名为空'}), 400

    if not file.filename.endswith('.pdf'):
        return jsonify({'error': '只支持PDF文件'}), 400

    # 保存文件
    save_path = os.path.join(PDF_DIR, file.filename)
    file.save(save_path)

    # 导入
    try:
        importer = PDFImporter(db)
        count = importer.import_pdf(save_path, source=file.filename)
        return jsonify({
            'success': True,
            'count': count,
            'message': f'成功导入 {count} 道题目'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# 用于正则表达式
import re

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=DEBUG)