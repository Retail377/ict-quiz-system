// 刷题页面核心逻辑
let questions = [];
let currentIndex = 0;
let userAnswers = {};
let correctCount = 0;
let wrongCount = 0;
let startTime = Date.now();

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    const container = document.getElementById('quizContainer');
    if (!container) return;

    questions = JSON.parse(container.dataset.questions);
    window.quizMode = container.dataset.mode;

    if (questions.length > 0) {
        renderQuestion(0);
    }
});

// 渲染题目
function renderQuestion(index) {
    if (index < 0 || index >= questions.length) return;

    currentIndex = index;
    const q = questions[index];

    // 更新进度
    document.getElementById('progressText').textContent =
        `${index + 1} / ${questions.length}`;

    // 更新元信息
    document.getElementById('qCategory').textContent = q.category || '未分类';
    document.getElementById('qNumber').textContent = `第 ${index + 1} 题`;

    // 更新题目内容
    document.getElementById('qContent').textContent = q.content;

    // 渲染选项
    const optionsContainer = document.getElementById('optionsContainer');
    optionsContainer.innerHTML = '';

    const options = [
        { key: 'A', text: q.option_a },
        { key: 'B', text: q.option_b },
        { key: 'C', text: q.option_c },
        { key: 'D', text: q.option_d }
    ].filter(o => o.text);

    options.forEach(opt => {
        const optionDiv = document.createElement('div');
        optionDiv.className = 'option';
        optionDiv.dataset.key = opt.key;
        optionDiv.innerHTML = `
            <span class="option-label">${opt.key}</span>
            <span class="option-text">${opt.text}</span>
        `;
        optionDiv.onclick = () => selectOption(opt.key);
        optionsContainer.appendChild(optionDiv);
    });

    // 恢复已选答案
    if (userAnswers[index]) {
        restoreAnswer(userAnswers[index]);
    }

    // 重置按钮状态
    document.getElementById('submitBtn').style.display = 'inline-block';
    document.getElementById('nextBtn').style.display = 'none';
    document.getElementById('answerPanel').style.display = 'none';

    // 更新导航按钮
    document.getElementById('prevBtn').disabled = index === 0;

    // 检查收藏状态
    checkFavoriteStatus(q.id);

    // 重置计时
    startTime = Date.now();
}

// 选择选项
function selectOption(key) {
    // 如果已经提交过，不允许修改
    if (document.getElementById('answerPanel').style.display !== 'none') return;

    // 移除其他选中
    document.querySelectorAll('.option').forEach(opt => {
        opt.classList.remove('selected');
    });

    // 添加选中
    const selected = document.querySelector(`.option[data-key="${key}"]`);
    if (selected) {
        selected.classList.add('selected');
    }

    // 记录答案
    userAnswers[currentIndex] = key;
}

// 恢复答案
function restoreAnswer(answer) {
    const selected = document.querySelector(`.option[data-key="${answer}"]`);
    if (selected) {
        selected.classList.add('selected');
    }
}

// 提交答案
function submitAnswer() {
    const q = questions[currentIndex];
    const userAnswer = userAnswers[currentIndex];

    if (!userAnswer) {
        alert('请先选择答案');
        return;
    }

    const timeSpent = Math.floor((Date.now() - startTime) / 1000);

    // 调用API
    fetch('/api/submit_answer', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            question_id: q.id,
            answer: userAnswer,
            mode: window.quizMode || 'random',
            time_spent: timeSpent
        })
    })
    .then(res => res.json())
    .then(data => {
        showAnswerResult(data);

        if (data.is_correct) {
            correctCount++;
        } else {
            wrongCount++;
        }
    })
    .catch(err => {
        console.error('提交失败:', err);
        alert('提交失败，请重试');
    });
}

// 显示答案结果
function showAnswerResult(data) {
    const q = questions[currentIndex];
    const userAnswer = userAnswers[currentIndex];

    // 标记选项
    document.querySelectorAll('.option').forEach(opt => {
        const key = opt.dataset.key;
        opt.classList.remove('selected');

        if (key === data.correct_answer) {
            opt.classList.add('correct');
        } else if (key === userAnswer && !data.is_correct) {
            opt.classList.add('wrong');
        }
    });

    // 显示答案面板
    const panel = document.getElementById('answerPanel');
    panel.style.display = 'block';

    const badge = document.getElementById('resultBadge');
    if (data.is_correct) {
        badge.textContent = '✅ 回答正确！';
        badge.className = 'result-badge correct';
    } else {
        badge.textContent = '❌ 回答错误';
        badge.className = 'result-badge wrong';
    }

    document.getElementById('correctAnswer').textContent = data.correct_answer;
    document.getElementById('explanationText').textContent = data.explanation || '暂无解析';

    // 切换按钮
    document.getElementById('submitBtn').style.display = 'none';
    document.getElementById('nextBtn').style.display = 'inline-block';

    // 如果是最后一题
    if (currentIndex === questions.length - 1) {
        document.getElementById('nextBtn').textContent = '查看结果 🎉';
    }
}

// 下一题
function nextQuestion() {
    if (currentIndex < questions.length - 1) {
        renderQuestion(currentIndex + 1);
    } else {
        showSummary();
    }
}

// 上一题
function prevQuestion() {
    if (currentIndex > 0) {
        renderQuestion(currentIndex - 1);
    }
}

// 显示汇总
function showSummary() {
    document.getElementById('quizContainer').style.display = 'none';
    document.getElementById('quizSummary').style.display = 'block';

    document.getElementById('summaryTotal').textContent = questions.length;
    document.getElementById('summaryCorrect').textContent = correctCount;
    document.getElementById('summaryWrong').textContent = wrongCount;

    const accuracy = questions.length > 0
        ? (correctCount / questions.length * 100).toFixed(1)
        : 0;
    document.getElementById('summaryAccuracy').textContent = accuracy + '%';
}

// 切换收藏
function toggleFavorite() {
    const q = questions[currentIndex];

    fetch('/api/toggle_favorite', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({question_id: q.id})
    })
    .then(res => res.json())
    .then(data => {
        const btn = document.getElementById('favBtn');
        if (data.is_favorite) {
            btn.textContent = '⭐ 已收藏';
            btn.classList.add('active');
        } else {
            btn.textContent = '⭐ 收藏';
            btn.classList.remove('active');
        }
    });
}

// 检查收藏状态
function checkFavoriteStatus(questionId) {
    fetch(`/api/check_favorite/${questionId}`)
        .then(res => res.json())
        .then(data => {
            const btn = document.getElementById('favBtn');
            if (data.is_favorite) {
                btn.textContent = '⭐ 已收藏';
                btn.classList.add('active');
            } else {
                btn.textContent = '⭐ 收藏';
                btn.classList.remove('active');
            }
        });
}

// 键盘快捷键
document.addEventListener('keydown', function(e) {
    // 数字键选择选项
    if (e.key >= '1' && e.key <= '4') {
        const keys = ['A', 'B', 'C', 'D'];
        selectOption(keys[parseInt(e.key) - 1]);
    }
    // 字母键选择选项
    else if (e.key.toUpperCase() >= 'A' && e.key.toUpperCase() <= 'D') {
        selectOption(e.key.toUpperCase());
    }
    // 回车提交
    else if (e.key === 'Enter') {
        const submitBtn = document.getElementById('submitBtn');
        const nextBtn = document.getElementById('nextBtn');
        if (submitBtn.style.display !== 'none') {
            submitAnswer();
        } else if (nextBtn.style.display !== 'none') {
            nextQuestion();
        }
    }
    // 左右箭头切换
    else if (e.key === 'ArrowLeft') {
        prevQuestion();
    } else if (e.key === 'ArrowRight') {
        const nextBtn = document.getElementById('nextBtn');
        if (nextBtn.style.display !== 'none') {
            nextQuestion();
        }
    }
});