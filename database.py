import sqlite3
import os
from datetime import datetime, timedelta
from config import DB_PATH


class Database:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.init_database()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_database(self):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_no INTEGER,
                type TEXT NOT NULL,
                category TEXT NOT NULL,
                sub_category TEXT,
                content TEXT NOT NULL,
                option_a TEXT,
                option_b TEXT,
                option_c TEXT,
                option_d TEXT,
                answer TEXT NOT NULL,
                explanation TEXT,
                difficulty INTEGER DEFAULT 2,
                source TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                nickname TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS answer_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                question_id INTEGER,
                user_answer TEXT,
                is_correct INTEGER,
                mode TEXT,
                time_spent INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (question_id) REFERENCES questions(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS wrong_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                question_id INTEGER,
                wrong_count INTEGER DEFAULT 1,
                correct_streak INTEGER DEFAULT 0,
                last_wrong_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, question_id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (question_id) REFERENCES questions(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                question_id INTEGER,
                note TEXT,
                tags TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, question_id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (question_id) REFERENCES questions(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS check_ins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                check_date DATE,
                question_count INTEGER DEFAULT 0,
                correct_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, check_date),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        conn.commit()
        conn.close()

    # ============ 题目操作 ============
    def add_question(self, q):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO questions 
            (question_no, type, category, sub_category, content, 
             option_a, option_b, option_c, option_d, answer, explanation, difficulty, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            q.get('question_no'), q['type'], q['category'], q.get('sub_category'),
            q['content'], q.get('option_a'), q.get('option_b'),
            q.get('option_c'), q.get('option_d'),
            q['answer'], q.get('explanation'), q.get('difficulty', 2),
            q.get('source')
        ))
        conn.commit()
        qid = cursor.lastrowid
        conn.close()
        return qid

    def batch_add_questions(self, questions):
        conn = self.get_connection()
        cursor = conn.cursor()
        count = 0
        for q in questions:
            try:
                cursor.execute('''
                    INSERT INTO questions 
                    (question_no, type, category, sub_category, content, 
                     option_a, option_b, option_c, option_d, answer, explanation, difficulty, source)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    q.get('question_no'), q['type'], q['category'], q.get('sub_category'),
                    q['content'], q.get('option_a'), q.get('option_b'),
                    q.get('option_c'), q.get('option_d'),
                    q['answer'], q.get('explanation'), q.get('difficulty', 2),
                    q.get('source')
                ))
                count += 1
            except Exception as e:
                print(f"导入失败: {e}")
        conn.commit()
        conn.close()
        return count

    def get_random_questions(self, count=20, category=None, exclude_ids=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        if category and category != '全部':
            cursor.execute('''
                SELECT * FROM questions WHERE category = ?
                ORDER BY RANDOM() LIMIT ?
            ''', (category, count))
        else:
            cursor.execute('''
                SELECT * FROM questions ORDER BY RANDOM() LIMIT ?
            ''', (count,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_question_by_id(self, qid):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM questions WHERE id = ?', (qid,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_questions_by_ids(self, ids):
        if not ids:
            return []
        conn = self.get_connection()
        cursor = conn.cursor()
        placeholders = ','.join('?' * len(ids))
        cursor.execute(f'SELECT * FROM questions WHERE id IN ({placeholders})', ids)
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_categories(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT category, COUNT(*) as count 
            FROM questions GROUP BY category
        ''')
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_total_question_count(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as c FROM questions')
        row = cursor.fetchone()
        conn.close()
        return row['c'] if row else 0

    # ============ 用户操作 ============
    def create_user(self, username, nickname=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                'INSERT INTO users (username, nickname) VALUES (?, ?)',
                (username, nickname or username)
            )
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()
            return user_id
        except sqlite3.IntegrityError:
            conn.close()
            return None

    def get_user(self, username):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_or_create_user(self, username):
        user = self.get_user(username)
        if user:
            return user['id']
        return self.create_user(username)

    # ============ 答题记录 ============
    def save_answer_record(self, user_id, question_id, user_answer, is_correct, mode, time_spent=0):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO answer_records 
            (user_id, question_id, user_answer, is_correct, mode, time_spent)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, question_id, user_answer, 1 if is_correct else 0, mode, time_spent))
        conn.commit()
        conn.close()

    # ============ 错题集 ============
    def add_to_wrong_questions(self, user_id, question_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM wrong_questions 
            WHERE user_id = ? AND question_id = ?
        ''', (user_id, question_id))
        existing = cursor.fetchone()

        if existing:
            cursor.execute('''
                UPDATE wrong_questions 
                SET wrong_count = wrong_count + 1,
                    correct_streak = 0,
                    last_wrong_at = ?
                WHERE user_id = ? AND question_id = ?
            ''', (datetime.now(), user_id, question_id))
        else:
            cursor.execute('''
                INSERT INTO wrong_questions 
                (user_id, question_id, last_wrong_at)
                VALUES (?, ?, ?)
            ''', (user_id, question_id, datetime.now()))
        conn.commit()
        conn.close()

    def update_wrong_streak(self, user_id, question_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE wrong_questions 
            SET correct_streak = correct_streak + 1
            WHERE user_id = ? AND question_id = ?
        ''', (user_id, question_id))
        conn.commit()
        conn.close()

    def get_wrong_questions(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT q.*, wq.wrong_count, wq.correct_streak
            FROM wrong_questions wq
            JOIN questions q ON wq.question_id = q.id
            WHERE wq.user_id = ?
            ORDER BY wq.wrong_count DESC, wq.last_wrong_at DESC
        ''', (user_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def remove_from_wrong(self, user_id, question_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            DELETE FROM wrong_questions 
            WHERE user_id = ? AND question_id = ?
        ''', (user_id, question_id))
        conn.commit()
        conn.close()

    # ============ 收藏 ============
    def toggle_favorite(self, user_id, question_id, note=None, tags=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM favorites WHERE user_id = ? AND question_id = ?
        ''', (user_id, question_id))
        existing = cursor.fetchone()

        if existing:
            cursor.execute('''
                DELETE FROM favorites WHERE user_id = ? AND question_id = ?
            ''', (user_id, question_id))
            result = False
        else:
            cursor.execute('''
                INSERT INTO favorites (user_id, question_id, note, tags)
                VALUES (?, ?, ?, ?)
            ''', (user_id, question_id, note, tags))
            result = True
        conn.commit()
        conn.close()
        return result

    def is_favorite(self, user_id, question_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 1 FROM favorites WHERE user_id = ? AND question_id = ?
        ''', (user_id, question_id))
        row = cursor.fetchone()
        conn.close()
        return row is not None

    def get_favorites(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT q.*, f.note, f.tags, f.created_at as fav_time
            FROM favorites f
            JOIN questions q ON f.question_id = q.id
            WHERE f.user_id = ?
            ORDER BY f.created_at DESC
        ''', (user_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    # ============ 打卡 ============
    def update_check_in(self, user_id, is_correct):
        today = datetime.now().strftime('%Y-%m-%d')
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM check_ins 
            WHERE user_id = ? AND check_date = ?
        ''', (user_id, today))
        existing = cursor.fetchone()

        if existing:
            cursor.execute('''
                UPDATE check_ins 
                SET question_count = question_count + 1,
                    correct_count = correct_count + ?
                WHERE user_id = ? AND check_date = ?
            ''', (1 if is_correct else 0, user_id, today))
        else:
            cursor.execute('''
                INSERT INTO check_ins 
                (user_id, check_date, question_count, correct_count)
                VALUES (?, ?, 1, ?)
            ''', (user_id, today, 1 if is_correct else 0))
        conn.commit()
        conn.close()

    def get_check_in_calendar(self, user_id, year, month):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM check_ins 
            WHERE user_id = ? 
            AND strftime('%Y', check_date) = ?
            AND strftime('%m', check_date) = ?
            ORDER BY check_date
        ''', (user_id, str(year), f"{month:02d}"))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_continuous_days(self, user_id):
        """获取连续打卡天数"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT check_date FROM check_ins 
            WHERE user_id = ?
            ORDER BY check_date DESC
        ''', (user_id,))
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return 0

        dates = [datetime.strptime(r['check_date'], '%Y-%m-%d').date() for r in rows]
        today = datetime.now().date()

        if dates[0] != today and dates[0] != today - timedelta(days=1):
            return 0

        continuous = 0
        expected = dates[0]
        for d in dates:
            if d == expected:
                continuous += 1
                expected = d - timedelta(days=1)
            else:
                break
        return continuous

    # ============ 统计 ============
    def get_user_statistics(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT COUNT(*) as total, SUM(is_correct) as correct
            FROM answer_records WHERE user_id = ?
        ''', (user_id,))
        total = cursor.fetchone()

        cursor.execute('''
            SELECT q.category,
                   COUNT(*) as total,
                   SUM(ar.is_correct) as correct
            FROM answer_records ar
            JOIN questions q ON ar.question_id = q.id
            WHERE ar.user_id = ?
            GROUP BY q.category
        ''', (user_id,))
        by_category = [dict(row) for row in cursor.fetchall()]

        cursor.execute('''
            SELECT COUNT(DISTINCT check_date) as days
            FROM check_ins WHERE user_id = ?
        ''', (user_id,))
        days = cursor.fetchone()['days']

        cursor.execute('''
            SELECT COUNT(*) as c FROM wrong_questions WHERE user_id = ?
        ''', (user_id,))
        wrong_count = cursor.fetchone()['c']

        cursor.execute('''
            SELECT COUNT(*) as c FROM favorites WHERE user_id = ?
        ''', (user_id,))
        fav_count = cursor.fetchone()['c']

        conn.close()

        return {
            'total_questions': total['total'] or 0,
            'correct_questions': total['correct'] or 0,
            'accuracy': (total['correct'] or 0) / total['total'] * 100 if total['total'] else 0,
            'by_category': by_category,
            'check_in_days': days,
            'wrong_count': wrong_count,
            'favorite_count': fav_count
        }

    def get_daily_stats(self, user_id, days=30):
        """获取最近N天的每日统计"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as total,
                SUM(is_correct) as correct
            FROM answer_records
            WHERE user_id = ?
            AND created_at >= date('now', ?)
            GROUP BY DATE(created_at)
            ORDER BY date
        ''', (user_id, f'-{days} days'))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_monthly_harvest(self, user_id, year, month):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(is_correct) as correct,
                COUNT(DISTINCT DATE(created_at)) as active_days
            FROM answer_records
            WHERE user_id = ?
            AND strftime('%Y', created_at) = ?
            AND strftime('%m', created_at) = ?
        ''', (user_id, str(year), f"{month:02d}"))
        result = cursor.fetchone()

        cursor.execute('''
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as total,
                SUM(is_correct) as correct
            FROM answer_records
            WHERE user_id = ?
            AND strftime('%Y', created_at) = ?
            AND strftime('%m', created_at) = ?
            GROUP BY DATE(created_at)
            ORDER BY date
        ''', (user_id, str(year), f"{month:02d}"))
        daily = [dict(row) for row in cursor.fetchall()]

        cursor.execute('''
            SELECT q.category,
                   COUNT(*) as total,
                   SUM(ar.is_correct) as correct
            FROM answer_records ar
            JOIN questions q ON ar.question_id = q.id
            WHERE ar.user_id = ?
            AND strftime('%Y', ar.created_at) = ?
            AND strftime('%m', ar.created_at) = ?
            GROUP BY q.category
        ''', (user_id, str(year), f"{month:02d}"))
        by_category = [dict(row) for row in cursor.fetchall()]

        conn.close()

        return {
            'year': year,
            'month': month,
            'total_questions': result['total'] or 0,
            'correct_questions': result['correct'] or 0,
            'accuracy': (result['correct'] or 0) / result['total'] * 100 if result['total'] else 0,
            'active_days': result['active_days'] or 0,
            'daily_data': daily,
            'by_category': by_category
        }