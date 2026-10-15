import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import matplotlib

matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.font_manager as fm
from datetime import datetime
import os

from config import CHART_DIR
from database import Database
from pdf_importer import PDFImporter

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False


class QuizDesktopApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ICT网络赛道刷题系统")
        self.root.geometry("1100x750")
        self.root.configure(bg='#f5f7fa')

        self.db = Database()
        self.user_id = self.db.get_or_create_user('desktop_user')

        # 当前刷题状态
        self.questions = []
        self.current_index = 0
        self.user_answers = {}
        self.correct_count = 0
        self.wrong_count = 0

        self.setup_styles()
        self.create_widgets()
        self.show_home()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')

        style.configure('Title.TLabel',
                        font=('Microsoft YaHei', 20, 'bold'),
                        background='#f5f7fa',
                        foreground='#667eea')

        style.configure('Subtitle.TLabel',
                        font=('Microsoft YaHei', 12),
                        background='#f5f7fa',
                        foreground='#666')

        style.configure('Card.TFrame',
                        background='white',
                        relief='flat')

        style.configure('Primary.TButton',
                        font=('Microsoft YaHei', 11),
                        padding=(20, 10))

        style.configure('Question.TLabel',
                        font=('Microsoft YaHei', 13),
                        background='white',
                        foreground='#333',
                        wraplength=900)

        style.configure('Option.TRadiobutton',
                        font=('Microsoft YaHei', 11),
                        background='white')

    def create_widgets(self):
        # 顶部导航栏
        nav_frame = tk.Frame(self.root, bg='#667eea', height=60)
        nav_frame.pack(fill='x')
        nav_frame.pack_propagate(False)

        title_label = tk.Label(nav_frame, text="📚 ICT刷题大师",
                               font=('Microsoft YaHei', 16, 'bold'),
                               bg='#667eea', fg='white')
        title_label.pack(side='left', padx=20, pady=15)

        # 导航按钮
        nav_buttons = [
            ("🏠 首页", self.show_home),
            ("🎲 刷题", self.show_quiz_setup),
            ("❌ 错题集", self.show_wrong),
            ("⭐ 收藏", self.show_favorites),
            ("📊 统计", self.show_stats),
            ("📅 日历", self.show_calendar),
            ("📄 导入PDF", self.import_pdf),
        ]

        for text, cmd in nav_buttons:
            btn = tk.Button(nav_frame, text=text, command=cmd,
                            font=('Microsoft YaHei', 10),
                            bg='#667eea', fg='white',
                            bd=0, padx=15, pady=5,
                            activebackground='#5568d3',
                            activeforeground='white',
                            cursor='hand2')
            btn.pack(side='left', padx=2)

        # 主内容区
        self.content_frame = tk.Frame(self.root, bg='#f5f7fa')
        self.content_frame.pack(fill='both', expand=True, padx=20, pady=20)

    def clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    # ============ 首页 ============
    def show_home(self):
        self.clear_content()

        # 标题
        tk.Label(self.content_frame, text="🎯 欢迎使用ICT刷题系统",
                 font=('Microsoft YaHei', 22, 'bold'),
                 bg='#f5f7fa', fg='#667eea').pack(pady=20)

        tk.Label(self.content_frame,
                 text="覆盖无线、安全、网络、VLAN、数通五大考点",
                 font=('Microsoft YaHei', 12),
                 bg='#f5f7fa', fg='#666').pack(pady=5)

        # 统计卡片
        stats = self.db.get_user_statistics(self.user_id)
        total_questions = self.db.get_total_question_count()
        continuous_days = self.db.get_continuous_days(self.user_id)

        cards_frame = tk.Frame(self.content_frame, bg='#f5f7fa')
        cards_frame.pack(pady=30)

        cards_data = [
            ("题库总数", total_questions, '#667eea'),
            ("已答题数", stats['total_questions'], '#67c23a'),
            ("正确率", f"{stats['accuracy']:.1f}%", '#e6a23c'),
            ("连续打卡", f"{continuous_days}天", '#f56c6c'),
            ("错题数", stats['wrong_count'], '#909399'),
            ("收藏数", stats['favorite_count'], '#409eff'),
        ]

        for i, (label, value, color) in enumerate(cards_data):
            card = tk.Frame(cards_frame, bg='white', width=160, height=110,
                            relief='flat', bd=0)
            card.grid(row=0, column=i, padx=10, pady=10)
            card.pack_propagate(False)

            tk.Label(card, text=str(value), font=('Microsoft YaHei', 22, 'bold'),
                     bg='white', fg=color).pack(pady=(20, 5))
            tk.Label(card, text=label, font=('Microsoft YaHei', 10),
                     bg='white', fg='#666').pack()

        # 快速开始按钮
        tk.Label(self.content_frame, text="🚀 快速开始",
                 font=('Microsoft YaHei', 14, 'bold'),
                 bg='#f5f7fa', fg='#333').pack(pady=(30, 15))

        quick_frame = tk.Frame(self.content_frame, bg='#f5f7fa')
        quick_frame.pack()

        quick_buttons = [
            ("🎲 随机10题", lambda: self.start_quiz('random', 10)),
            ("📝 随机20题", lambda: self.start_quiz('random', 20)),
            ("💪 随机50题", lambda: self.start_quiz('random', 50)),
            ("❌ 错题重做", lambda: self.start_quiz('wrong', 20)),
            ("⭐ 收藏重做", lambda: self.start_quiz('favorite', 20)),
        ]

        for text, cmd in quick_buttons:
            btn = tk.Button(quick_frame, text=text, command=cmd,
                            font=('Microsoft YaHei', 11),
                            bg='#667eea', fg='white',
                            bd=0, padx=20, pady=12,
                            activebackground='#5568d3',
                            cursor='hand2')
            btn.pack(side='left', padx=8)

    # ============ 刷题设置 ============
    def show_quiz_setup(self):
        self.clear_content()

        tk.Label(self.content_frame, text="⚙️ 刷题设置",
                 font=('Microsoft YaHei', 20, 'bold'),
                 bg='#f5f7fa', fg='#667eea').pack(pady=20)

        # 设置卡片
        setup_frame = tk.Frame(self.content_frame, bg='white', padx=40, pady=30)
        setup_frame.pack(pady=20)

        # 考点选择
        tk.Label(setup_frame, text="考点分类:",
                 font=('Microsoft YaHei', 12),
                 bg='white', fg='#333').grid(row=0, column=0, sticky='w', pady=10)

        categories = ['全部'] + [c['category'] for c in self.db.get_categories()]
        self.category_var = tk.StringVar(value='全部')
        category_combo = ttk.Combobox(setup_frame, textvariable=self.category_var,
                                      values=categories, state='readonly',
                                      font=('Microsoft YaHei', 11), width=25)
        category_combo.grid(row=0, column=1, padx=20, pady=10)

        # 题目数量
        tk.Label(setup_frame, text="题目数量:",
                 font=('Microsoft YaHei', 12),
                 bg='white', fg='#333').grid(row=1, column=0, sticky='w', pady=10)

        self.count_var = tk.StringVar(value='20')
        count_combo = ttk.Combobox(setup_frame, textvariable=self.count_var,
                                   values=['10', '20', '30', '50', '100'],
                                   state='readonly',
                                   font=('Microsoft YaHei', 11), width=25)
        count_combo.grid(row=1, column=1, padx=20, pady=10)

        # 开始按钮
        tk.Button(setup_frame, text="🚀 开始刷题",
                  command=lambda: self.start_quiz(
                      'random',
                      int(self.count_var.get()),
                      self.category_var.get()
                  ),
                  font=('Microsoft YaHei', 12, 'bold'),
                  bg='#667eea', fg='white',
                  bd=0, padx=40, pady=12,
                  cursor='hand2').grid(row=2, column=0, columnspan=2, pady=25)

    # ============ 刷题核心 ============
    def start_quiz(self, mode, count=20, category='全部'):
        """开始刷题"""
        if mode == 'wrong':
            questions = self.db.get_wrong_questions(self.user_id)[:count]
        elif mode == 'favorite':
            questions = self.db.get_favorites(self.user_id)[:count]
        else:
            questions = self.db.get_random_questions(count, category)

        if not questions:
            messagebox.showinfo("提示", "没有可用的题目")
            return

        self.questions = questions
        self.current_index = 0
        self.user_answers = {}
        self.correct_count = 0
        self.wrong_count = 0
        self.quiz_mode = mode

        self.show_question()

    def show_question(self):
        """显示当前题目"""
        self.clear_content()

        if self.current_index >= len(self.questions):
            self.show_quiz_summary()
            return

        q = self.questions[self.current_index]

        # 顶部进度
        header_frame = tk.Frame(self.content_frame, bg='#f5f7fa')
        header_frame.pack(fill='x', pady=(0, 15))

        tk.Label(header_frame,
                 text=f"第 {self.current_index + 1} / {len(self.questions)} 题",
                 font=('Microsoft YaHei', 12, 'bold'),
                 bg='#f5f7fa', fg='#667eea').pack(side='left')

        tk.Label(header_frame,
                 text=f"考点: {q['category']}",
                 font=('Microsoft YaHei', 11),
                 bg='#f5f7fa', fg='#666').pack(side='right')

        # 进度条
        progress = ttk.Progressbar(self.content_frame,
                                   value=(self.current_index + 1) / len(self.questions) * 100,
                                   length=1000)
        progress.pack(fill='x', pady=(0, 15))

        # 题目卡片
        q_card = tk.Frame(self.content_frame, bg='white', padx=30, pady=25)
        q_card.pack(fill='both', expand=True)

        # 题目内容
        tk.Label(q_card, text=q['content'],
                 font=('Microsoft YaHei', 13),
                 bg='white', fg='#333',
                 wraplength=900, justify='left',
                 anchor='w').pack(fill='x', pady=(0, 20))

        # 选项
        self.answer_var = tk.StringVar(value=self.user_answers.get(self.current_index, ''))
        self.option_frames = {}

        options = [
            ('A', q.get('option_a')),
            ('B', q.get('option_b')),
            ('C', q.get('option_c')),
            ('D', q.get('option_d')),
        ]

        for key, text in options:
            if not text:
                continue

            frame = tk.Frame(q_card, bg='#f8f9fa', padx=15, pady=12)
            frame.pack(fill='x', pady=5)

            rb = tk.Radiobutton(frame, text=f"{key}. {text}",
                                variable=self.answer_var, value=key,
                                font=('Microsoft YaHei', 11),
                                bg='#f8f9fa', fg='#333',
                                activebackground='#e8f0fe',
                                selectcolor='#f8f9fa',
                                anchor='w', justify='left',
                                wraplength=850,
                                cursor='hand2')
            rb.pack(fill='x')

            # 点击整行都可以选中
            frame.bind('<Button-1>', lambda e, k=key: self.answer_var.set(k))
            self.option_frames[key] = frame

        # 答案面板（初始隐藏）
        self.answer_panel = tk.Frame(q_card, bg='#f8f9fa', padx=20, pady=15)
        self.answer_panel.pack(fill='x', pady=(20, 0))
        self.answer_panel.pack_forget()

        # 按钮区
        btn_frame = tk.Frame(q_card, bg='white')
        btn_frame.pack(fill='x', pady=(20, 0))

        # 上一题
        if self.current_index > 0:
            tk.Button(btn_frame, text="⬅️ 上一题",
                      command=self.prev_question,
                      font=('Microsoft YaHei', 11),
                      bg='#e0e0e0', fg='#333',
                      bd=0, padx=20, pady=10,
                      cursor='hand2').pack(side='left')

        # 提交按钮
        self.submit_btn = tk.Button(btn_frame, text="提交答案",
                                    command=self.submit_answer,
                                    font=('Microsoft YaHei', 11, 'bold'),
                                    bg='#667eea', fg='white',
                                    bd=0, padx=30, pady=10,
                                    cursor='hand2')
        self.submit_btn.pack(side='right', padx=5)

        # 下一题按钮（初始隐藏）
        self.next_btn = tk.Button(btn_frame, text="下一题 ➡️",
                                  command=self.next_question,
                                  font=('Microsoft YaHei', 11, 'bold'),
                                  bg='#67c23a', fg='white',
                                  bd=0, padx=30, pady=10,
                                  cursor='hand2')

        # 收藏按钮
        self.fav_btn = tk.Button(btn_frame, text="⭐ 收藏",
                                 command=self.toggle_favorite,
                                 font=('Microsoft YaHei', 11),
                                 bg='#ffd700', fg='#333',
                                 bd=0, padx=20, pady=10,
                                 cursor='hand2')
        self.fav_btn.pack(side='right', padx=5)

        # 检查收藏状态
        if self.db.is_favorite(self.user_id, q['id']):
            self.fav_btn.config(text="⭐ 已收藏")

    def submit_answer(self):
        """提交答案"""
        user_answer = self.answer_var.get()

        if not user_answer:
            messagebox.showwarning("提示", "请先选择答案")
            return

        q = self.questions[self.current_index]
        correct_answer = q['answer'].strip().upper()
        is_correct = user_answer.strip().upper() == correct_answer

        # 记录答案
        self.user_answers[self.current_index] = user_answer

        # 保存到数据库
        self.db.save_answer_record(
            self.user_id, q['id'], user_answer, is_correct, self.quiz_mode
        )
        self.db.update_check_in(self.user_id, is_correct)

        if is_correct:
            self.correct_count += 1
            self.db.update_wrong_streak(self.user_id, q['id'])
        else:
            self.wrong_count += 1
            self.db.add_to_wrong_questions(self.user_id, q['id'])

        # 显示答案
        self.show_answer_result(q, user_answer, is_correct)

    def show_answer_result(self, q, user_answer, is_correct):
        """显示答案结果"""
        # 高亮选项
        for key, frame in self.option_frames.items():
            if key == q['answer'].strip().upper():
                frame.config(bg='#f0f9eb')
                for child in frame.winfo_children():
                    child.config(bg='#f0f9eb')
            elif key == user_answer and not is_correct:
                frame.config(bg='#fef0f0')
                for child in frame.winfo_children():
                    child.config(bg='#fef0f0')

        # 显示答案面板
        self.answer_panel.pack(fill='x', pady=(20, 0))
        for widget in self.answer_panel.winfo_children():
            widget.destroy()

        if is_correct:
            result_text = "✅ 回答正确！"
            result_color = '#67c23a'
        else:
            result_text = "❌ 回答错误"
            result_color = '#f56c6c'

        tk.Label(self.answer_panel, text=result_text,
                 font=('Microsoft YaHei', 13, 'bold'),
                 bg='#f8f9fa', fg=result_color).pack(anchor='w', pady=(0, 10))

        tk.Label(self.answer_panel,
                 text=f"正确答案: {q['answer']}",
                 font=('Microsoft YaHei', 12),
                 bg='#f8f9fa', fg='#67c23a').pack(anchor='w', pady=5)

        if q.get('explanation'):
            tk.Label(self.answer_panel, text="📖 解析:",
                     font=('Microsoft YaHei', 11, 'bold'),
                     bg='#f8f9fa', fg='#667eea').pack(anchor='w', pady=(10, 5))

            tk.Label(self.answer_panel, text=q['explanation'],
                     font=('Microsoft YaHei', 10),
                     bg='#f8f9fa', fg='#555',
                     wraplength=900, justify='left',
                     anchor='w').pack(fill='x')

        # 切换按钮
        self.submit_btn.pack_forget()
        self.next_btn.pack(side='right', padx=5)

        if self.current_index == len(self.questions) - 1:
            self.next_btn.config(text="查看结果 🎉")

    def next_question(self):
        """下一题"""
        self.current_index += 1
        if self.current_index >= len(self.questions):
            self.show_quiz_summary()
        else:
            self.show_question()

    def prev_question(self):
        """上一题"""
        if self.current_index > 0:
            self.current_index -= 1
            self.show_question()

    def toggle_favorite(self):
        """切换收藏"""
        q = self.questions[self.current_index]
        result = self.db.toggle_favorite(self.user_id, q['id'])

        if result:
            self.fav_btn.config(text="⭐ 已收藏")
            messagebox.showinfo("提示", "已加入收藏")
        else:
            self.fav_btn.config(text="⭐ 收藏")
            messagebox.showinfo("提示", "已取消收藏")

    def show_quiz_summary(self):
        """显示刷题汇总"""
        self.clear_content()

        total = len(self.questions)
        accuracy = self.correct_count / total * 100 if total > 0 else 0

        tk.Label(self.content_frame, text="🎉 本轮刷题完成！",
                 font=('Microsoft YaHei', 24, 'bold'),
                 bg='#f5f7fa', fg='#667eea').pack(pady=40)

        # 统计卡片
        cards_frame = tk.Frame(self.content_frame, bg='#f5f7fa')
        cards_frame.pack(pady=20)

        summary_data = [
            ("总题数", total, '#667eea'),
            ("正确", self.correct_count, '#67c23a'),
            ("错误", self.wrong_count, '#f56c6c'),
            ("正确率", f"{accuracy:.1f}%", '#e6a23c'),
        ]

        for label, value, color in summary_data:
            card = tk.Frame(cards_frame, bg='white', width=150, height=120)
            card.pack(side='left', padx=15)
            card.pack_propagate(False)

            tk.Label(card, text=str(value),
                     font=('Microsoft YaHei', 28, 'bold'),
                     bg='white', fg=color).pack(pady=(25, 5))
            tk.Label(card, text=label,
                     font=('Microsoft YaHei', 11),
                     bg='white', fg='#666').pack()

        # 操作按钮
        btn_frame = tk.Frame(self.content_frame, bg='#f5f7fa')
        btn_frame.pack(pady=30)

        tk.Button(btn_frame, text="🔄 再来一轮",
                  command=lambda: self.start_quiz('random', 20),
                  font=('Microsoft YaHei', 12),
                  bg='#667eea', fg='white',
                  bd=0, padx=30, pady=12,
                  cursor='hand2').pack(side='left', padx=10)

        tk.Button(btn_frame, text="❌ 查看错题",
                  command=self.show_wrong,
                  font=('Microsoft YaHei', 12),
                  bg='#f56c6c', fg='white',
                  bd=0, padx=30, pady=12,
                  cursor='hand2').pack(side='left', padx=10)

        tk.Button(btn_frame, text="🏠 返回首页",
                  command=self.show_home,
                  font=('Microsoft YaHei', 12),
                  bg='#909399', fg='white',
                  bd=0, padx=30, pady=12,
                  cursor='hand2').pack(side='left', padx=10)

    # ============ 错题集 ============
    def show_wrong(self):
        self.clear_content()

        wrong_questions = self.db.get_wrong_questions(self.user_id)

        tk.Label(self.content_frame, text="❌ 错题集",
                 font=('Microsoft YaHei', 20, 'bold'),
                 bg='#f5f7fa', fg='#667eea').pack(pady=20)

        tk.Label(self.content_frame, text=f"共 {len(wrong_questions)} 道错题",
                 font=('Microsoft YaHei', 12),
                 bg='#f5f7fa', fg='#666').pack()

        if not wrong_questions:
            tk.Label(self.content_frame, text="🎉 错题集为空！",
                     font=('Microsoft YaHei', 14),
                     bg='#f5f7fa', fg='#67c23a').pack(pady=40)
            return

        # 重做按钮
        tk.Button(self.content_frame, text="🔄 重做错题",
                  command=lambda: self.start_quiz('wrong', 20),
                  font=('Microsoft YaHei', 11),
                  bg='#667eea', fg='white',
                  bd=0, padx=20, pady=8,
                  cursor='hand2').pack(pady=10)

        # 滚动列表
        canvas = tk.Canvas(self.content_frame, bg='#f5f7fa', highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.content_frame, orient='vertical', command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#f5f7fa')

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        for q in wrong_questions:
            self.create_wrong_item(scrollable_frame, q)

    def create_wrong_item(self, parent, q):
        """创建错题项"""
        frame = tk.Frame(parent, bg='white', padx=20, pady=15)
        frame.pack(fill='x', pady=5, padx=5)

        # 头部信息
        header = tk.Frame(frame, bg='white')
        header.pack(fill='x', pady=(0, 10))

        tk.Label(header, text=q['category'],
                 font=('Microsoft YaHei', 10),
                 bg='#e8f0fe', fg='#667eea',
                 padx=8, pady=2).pack(side='left')

        tk.Label(header, text=f"错 {q['wrong_count']} 次",
                 font=('Microsoft YaHei', 10),
                 bg='#fef0f0', fg='#f56c6c',
                 padx=8, pady=2).pack(side='left', padx=5)

        # 题目内容
        tk.Label(frame, text=q['content'],
                 font=('Microsoft YaHei', 11),
                 bg='white', fg='#333',
                 wraplength=900, justify='left',
                 anchor='w').pack(fill='x', pady=5)

        # 正确答案
        tk.Label(frame, text=f"正确答案: {q['answer']}",
                 font=('Microsoft YaHei', 10),
                 bg='white', fg='#67c23a').pack(anchor='w', pady=5)

        # 解析（可选显示）
        if q.get('explanation'):
            exp_text = q['explanation'][:100] + ('...' if len(q['explanation']) > 100 else '')
            tk.Label(frame, text=f"解析: {exp_text}",
                     font=('Microsoft YaHei', 9),
                     bg='white', fg='#999',
                     wraplength=900, justify='left',
                     anchor='w').pack(fill='x', pady=5)

        # 移出按钮
        tk.Button(frame, text="🗑️ 移出错题集",
                  command=lambda qid=q['id']: self.remove_wrong(qid),
                  font=('Microsoft YaHei', 9),
                  bg='#f56c6c', fg='white',
                  bd=0, padx=10, pady=4,
                  cursor='hand2').pack(anchor='e')

    def remove_wrong(self, question_id):
        """移出错题集"""
        if messagebox.askyesno("确认", "确定移出错题集吗？"):
            self.db.remove_from_wrong(self.user_id, question_id)
            self.show_wrong()

    # ============ 收藏夹 ============
    def show_favorites(self):
        self.clear_content()

        favs = self.db.get_favorites(self.user_id)

        tk.Label(self.content_frame, text="⭐ 收藏夹",
                 font=('Microsoft YaHei', 20, 'bold'),
                 bg='#f5f7fa', fg='#667eea').pack(pady=20)

        tk.Label(self.content_frame, text=f"共 {len(favs)} 道收藏题",
                 font=('Microsoft YaHei', 12),
                 bg='#f5f7fa', fg='#666').pack()

        if not favs:
            tk.Label(self.content_frame, text="⭐ 收藏夹为空",
                     font=('Microsoft YaHei', 14),
                     bg='#f5f7fa', fg='#999').pack(pady=40)
            return

        # 重做按钮
        tk.Button(self.content_frame, text="🔄 重做收藏题",
                  command=lambda: self.start_quiz('favorite', 20),
                  font=('Microsoft YaHei', 11),
                  bg='#667eea', fg='white',
                  bd=0, padx=20, pady=8,
                  cursor='hand2').pack(pady=10)

        # 滚动列表
        canvas = tk.Canvas(self.content_frame, bg='#f5f7fa', highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.content_frame, orient='vertical', command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#f5f7fa')

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        for q in favs:
            self.create_favorite_item(scrollable_frame, q)

    def create_favorite_item(self, parent, q):
        """创建收藏项"""
        frame = tk.Frame(parent, bg='white', padx=20, pady=15)
        frame.pack(fill='x', pady=5, padx=5)

        # 头部信息
        header = tk.Frame(frame, bg='white')
        header.pack(fill='x', pady=(0, 10))

        tk.Label(header, text=q['category'],
                 font=('Microsoft YaHei', 10),
                 bg='#e8f0fe', fg='#667eea',
                 padx=8, pady=2).pack(side='left')

        tk.Label(header, text=f"收藏于 {q['fav_time'][:10]}",
                 font=('Microsoft YaHei', 10),
                 bg='#fff9e6', fg='#e6a23c',
                 padx=8, pady=2).pack(side='left', padx=5)

        # 题目内容
        tk.Label(frame, text=q['content'],
                 font=('Microsoft YaHei', 11),
                 bg='white', fg='#333',
                 wraplength=900, justify='left',
                 anchor='w').pack(fill='x', pady=5)

        # 正确答案
        tk.Label(frame, text=f"正确答案: {q['answer']}",
                 font=('Microsoft YaHei', 10),
                 bg='white', fg='#67c23a').pack(anchor='w', pady=5)

    # ============ 学习统计 ============
    def show_stats(self):
        self.clear_content()

        tk.Label(self.content_frame, text="📊 学习统计",
                 font=('Microsoft YaHei', 20, 'bold'),
                 bg='#f5f7fa', fg='#667eea').pack(pady=20)

        stats = self.db.get_user_statistics(self.user_id)
        daily_stats = self.db.get_daily_stats(self.user_id, days=30)

        # 统计卡片
        cards_frame = tk.Frame(self.content_frame, bg='#f5f7fa')
        cards_frame.pack(pady=20)

        cards_data = [
            ("总答题数", stats['total_questions'], '#667eea'),
            ("正确数", stats['correct_questions'], '#67c23a'),
            ("正确率", f"{stats['accuracy']:.1f}%", '#e6a23c'),
            ("打卡天数", stats['check_in_days'], '#f56c6c'),
        ]

        for label, value, color in cards_data:
            card = tk.Frame(cards_frame, bg='white', width=180, height=110)
            card.pack(side='left', padx=10)
            card.pack_propagate(False)

            tk.Label(card, text=str(value),
                     font=('Microsoft YaHei', 24, 'bold'),
                     bg='white', fg=color).pack(pady=(20, 5))
            tk.Label(card, text=label,
                     font=('Microsoft YaHei', 11),
                     bg='white', fg='#666').pack()

        # 图表区
        chart_frame = tk.Frame(self.content_frame, bg='white')
        chart_frame.pack(fill='both', expand=True, pady=20)

        fig = Figure(figsize=(12, 5), dpi=80, facecolor='white')

        # 子图1：近30天答题趋势
        ax1 = fig.add_subplot(121)
        if daily_stats:
            dates = [d['date'][-5:] for d in daily_stats]
            totals = [d['total'] for d in daily_stats]
            corrects = [d['correct'] for d in daily_stats]

            ax1.plot(dates, totals, marker='o', label='答题数', color='#667eea')
            ax1.plot(dates, corrects, marker='s', label='正确数', color='#67c23a')
            ax1.set_title('近30天答题趋势', fontsize=12)
            ax1.legend()
            ax1.tick_params(axis='x', rotation=45, labelsize=8)
            ax1.grid(True, alpha=0.3)
        else:
            ax1.text(0.5, 0.5, '暂无数据', ha='center', va='center',
                     transform=ax1.transAxes, fontsize=14, color='#999')
            ax1.set_title('近30天答题趋势', fontsize=12)

        # 子图2：各考点正确率
        ax2 = fig.add_subplot(122)
        if stats['by_category']:
            categories = [c['category'][:6] for c in stats['by_category']]
            accuracies = [
                (c['correct'] / c['total'] * 100) if c['total'] else 0
                for c in stats['by_category']
            ]

            colors = ['#667eea', '#67c23a', '#e6a23c', '#f56c6c', '#909399']
            bars = ax2.bar(categories, accuracies, color=colors[:len(categories)])
            ax2.set_title('各考点正确率(%)', fontsize=12)
            ax2.set_ylim(0, 100)
            ax2.tick_params(axis='x', rotation=30, labelsize=9)
            ax2.grid(True, alpha=0.3, axis='y')

            for bar, acc in zip(bars, accuracies):
                ax2.text(bar.get_x() + bar.get_width() / 2,
                         bar.get_height() + 2,
                         f'{acc:.0f}%',
                         ha='center', fontsize=9)
        else:
            ax2.text(0.5, 0.5, '暂无数据', ha='center', va='center',
                     transform=ax2.transAxes, fontsize=14, color='#999')
            ax2.set_title('各考点正确率', fontsize=12)

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)

        # 保存图表按钮
        tk.Button(self.content_frame, text="💾 保存图表",
                  command=lambda: self.save_chart(fig),
                  font=('Microsoft YaHei', 10),
                  bg='#67c23a', fg='white',
                  bd=0, padx=20, pady=8,
                  cursor='hand2').pack(pady=10)

    def save_chart(self, fig):
        """保存图表到文件"""
        filename = f"stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = os.path.join(CHART_DIR, filename)
        fig.savefig(filepath, dpi=150, bbox_inches='tight')
        messagebox.showinfo("保存成功", f"图表已保存到:\n{filepath}")

    # ============ 打卡日历 ============
    def show_calendar(self):
        self.clear_content()

        now = datetime.now()
        year, month = now.year, now.month

        tk.Label(self.content_frame, text=f"📅 {year}年{month}月 打卡日历",
                 font=('Microsoft YaHei', 20, 'bold'),
                 bg='#f5f7fa', fg='#667eea').pack(pady=20)

        harvest = self.db.get_monthly_harvest(self.user_id, year, month)

        # 月度收获
        harvest_frame = tk.Frame(self.content_frame, bg='#667eea', padx=30, pady=20)
        harvest_frame.pack(fill='x', pady=10)

        tk.Label(harvest_frame, text="🎁 本月收获",
                 font=('Microsoft YaHei', 14, 'bold'),
                 bg='#667eea', fg='white').pack(anchor='w', pady=(0, 15))

        stats_frame = tk.Frame(harvest_frame, bg='#667eea')
        stats_frame.pack()

        harvest_data = [
            ("答题总数", harvest['total_questions']),
            ("正确数", harvest['correct_questions']),
            ("正确率", f"{harvest['accuracy']:.1f}%"),
            ("活跃天数", harvest['active_days']),
        ]

        for label, value in harvest_data:
            item = tk.Frame(stats_frame, bg='#5568d3', padx=20, pady=10)
            item.pack(side='left', padx=8)

            tk.Label(item, text=str(value),
                     font=('Microsoft YaHei', 20, 'bold'),
                     bg='#5568d3', fg='white').pack()
            tk.Label(item, text=label,
                     font=('Microsoft YaHei', 10),
                     bg='#5568d3', fg='white').pack()

        # 日历热力图
        chart_frame = tk.Frame(self.content_frame, bg='white', padx=20, pady=20)
        chart_frame.pack(fill='both', expand=True, pady=10)

        fig = Figure(figsize=(10, 3), dpi=80, facecolor='white')
        ax = fig.add_subplot(111)

        daily_data = harvest['daily_data']
        if daily_data:
            dates = [d['date'][-2:] for d in daily_data]
            totals = [d['total'] for d in daily_data]

            colors = ['#ebedf0' if t == 0 else
                      '#c6e48b' if t < 10 else
                      '#7bc96f' if t < 20 else
                      '#239a3b' if t < 30 else
                      '#196127'
                      for t in totals]

            ax.bar(range(len(dates)), [1] * len(dates), color=colors)
            ax.set_xticks(range(len(dates)))
            ax.set_xticklabels(dates, fontsize=8)
            ax.set_yticks([])
            ax.set_title(f'{year}年{month}月 每日答题量', fontsize=12)

            for i, (d, t) in enumerate(zip(dates, totals)):
                ax.text(i, 0.5, str(t), ha='center', va='center',
                        fontsize=7, color='white' if t >= 20 else 'black')
        else:
            ax.text(0.5, 0.5, '本月暂无答题记录', ha='center', va='center',
                    transform=ax.transAxes, fontsize=14, color='#999')
            ax.set_xticks([])
            ax.set_yticks([])

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)

        # 每日详情列表
        if daily_data:
            list_frame = tk.Frame(self.content_frame, bg='white', padx=20, pady=15)
            list_frame.pack(fill='x', pady=10)

            tk.Label(list_frame, text="📋 每日详情",
                     font=('Microsoft YaHei', 12, 'bold'),
                     bg='white', fg='#333').pack(anchor='w', pady=(0, 10))

            for d in daily_data:
                row = tk.Frame(list_frame, bg='white')
                row.pack(fill='x', pady=2)

                tk.Label(row, text=d['date'],
                         font=('Microsoft YaHei', 10),
                         bg='white', fg='#666',
                         width=15, anchor='w').pack(side='left')

                tk.Label(row, text=f"答题: {d['total']}",
                         font=('Microsoft YaHei', 10),
                         bg='white', fg='#667eea',
                         width=12, anchor='w').pack(side='left')

                tk.Label(row, text=f"正确: {d['correct']}",
                         font=('Microsoft YaHei', 10),
                         bg='white', fg='#67c23a',
                         width=12, anchor='w').pack(side='left')

                acc = d['correct'] / d['total'] * 100 if d['total'] else 0
                color = '#67c23a' if acc >= 80 else '#e6a23c' if acc >= 60 else '#f56c6c'
                tk.Label(row, text=f"正确率: {acc:.0f}%",
                         font=('Microsoft YaHei', 10),
                         bg='white', fg=color,
                         width=15, anchor='w').pack(side='left')

                # ============ PDF导入 ============

            def import_pdf(self):
                """导入PDF题库"""
                filepath = filedialog.askopenfilename(
                    title="选择PDF题库文件",
                    filetypes=[("PDF文件", "*.pdf"), ("所有文件", "*.*")]
                )

                if not filepath:
                    return

                # 显示进度窗口
                progress_win = tk.Toplevel(self.root)
                progress_win.title("正在导入")
                progress_win.geometry("400x150")
                progress_win.configure(bg='white')
                progress_win.transient(self.root)
                progress_win.grab_set()

                # 居中显示
                progress_win.update_idletasks()
                x = (progress_win.winfo_screenwidth() - 400) // 2
                y = (progress_win.winfo_screenheight() - 150) // 2
                progress_win.geometry(f"400x150+{x}+{y}")

                tk.Label(progress_win, text="📄 正在解析PDF文件...",
                         font=('Microsoft YaHei', 12),
                         bg='white', fg='#333').pack(pady=20)

                progress_bar = ttk.Progressbar(progress_win, mode='indeterminate', length=300)
                progress_bar.pack(pady=10)
                progress_bar.start(10)

                status_label = tk.Label(progress_win, text="",
                                        font=('Microsoft YaHei', 10),
                                        bg='white', fg='#666')
                status_label.pack(pady=5)

                def do_import():
                    try:
                        importer = PDFImporter(self.db)
                        count = importer.import_pdf(filepath, source=os.path.basename(filepath))

                        progress_bar.stop()
                        progress_win.destroy()

                        messagebox.showinfo("导入成功",
                                            f"✅ 成功导入 {count} 道题目！\n\n"
                                            f"文件: {os.path.basename(filepath)}")
                        self.show_home()

                    except Exception as e:
                        progress_bar.stop()
                        progress_win.destroy()
                        messagebox.showerror("导入失败", f"❌ 导入失败:\n{str(e)}")

                # 延迟执行，让界面先显示
                self.root.after(100, do_import)

                # ============ 模拟考试 ============

            def show_exam(self):
                """模拟考试"""
                self.clear_content()

                tk.Label(self.content_frame, text="📝 模拟考试",
                         font=('Microsoft YaHei', 20, 'bold'),
                         bg='#f5f7fa', fg='#667eea').pack(pady=20)

                tk.Label(self.content_frame,
                         text="模拟考试将随机抽取50道题目，限时60分钟",
                         font=('Microsoft YaHei', 12),
                         bg='#f5f7fa', fg='#666').pack(pady=10)

                exam_frame = tk.Frame(self.content_frame, bg='white', padx=40, pady=30)
                exam_frame.pack(pady=20)

                tk.Label(exam_frame, text="考试配置",
                         font=('Microsoft YaHei', 14, 'bold'),
                         bg='white', fg='#333').pack(pady=(0, 20))

                # 题目数量
                tk.Label(exam_frame, text="题目数量:",
                         font=('Microsoft YaHei', 11),
                         bg='white', fg='#666').pack(anchor='w')

                self.exam_count_var = tk.StringVar(value='50')
                ttk.Combobox(exam_frame, textvariable=self.exam_count_var,
                             values=['20', '30', '50', '100'],
                             state='readonly', width=20).pack(pady=5, anchor='w')

                # 限时
                tk.Label(exam_frame, text="限时(分钟):",
                         font=('Microsoft YaHei', 11),
                         bg='white', fg='#666').pack(anchor='w', pady=(15, 0))

                self.exam_time_var = tk.StringVar(value='60')
                ttk.Combobox(exam_frame, textvariable=self.exam_time_var,
                             values=['30', '60', '90', '120'],
                             state='readonly', width=20).pack(pady=5, anchor='w')

                tk.Button(exam_frame, text="🚀 开始考试",
                          command=self.start_exam,
                          font=('Microsoft YaHei', 12, 'bold'),
                          bg='#667eea', fg='white',
                          bd=0, padx=40, pady=12,
                          cursor='hand2').pack(pady=25)

            def start_exam(self):
                """开始模拟考试"""
                count = int(self.exam_count_var.get())
                minutes = int(self.exam_time_var.get())

                questions = self.db.get_random_questions(count)
                if not questions:
                    messagebox.showinfo("提示", "没有可用的题目")
                    return

                self.questions = questions
                self.current_index = 0
                self.user_answers = {}
                self.correct_count = 0
                self.wrong_count = 0
                self.quiz_mode = 'exam'
                self.exam_end_time = datetime.now().timestamp() + minutes * 60

                self.show_question()
                self.update_exam_timer()

            def update_exam_timer(self):
                """更新考试计时器"""
                if not hasattr(self, 'exam_end_time'):
                    return

                if self.quiz_mode != 'exam':
                    return

                remaining = int(self.exam_end_time - datetime.now().timestamp())

                if remaining <= 0:
                    messagebox.showinfo("时间到", "考试时间已结束！")
                    self.show_quiz_summary()
                    return

                minutes = remaining // 60
                seconds = remaining % 60

                # 更新标题栏计时
                self.root.title(f"ICT刷题系统 - 剩余时间: {minutes:02d}:{seconds:02d}")

                # 每秒更新
                self.root.after(1000, self.update_exam_timer)

            def on_closing(self):
                """关闭窗口时的处理"""
                if messagebox.askokcancel("退出", "确定要退出刷题系统吗？"):
                    self.root.destroy()

            # ============ 主程序入口 ============
            def main():
                root = tk.Tk()
                app = QuizDesktopApp(root)
                root.protocol("WM_DELETE_WINDOW", app.on_closing)
                root.mainloop()

            if __name__ == '__main__':
                main()