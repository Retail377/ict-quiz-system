import pdfplumber
import re
import os
from database import Database


class PDFImporter:
    """PDF题库导入器（增强版）

    支持的题目格式：

    【格式1：标准格式】
    单选题
    1. 以下哪条命令在配置Mesh白名单时不是必须用到的?【无线考点】
    A. radio radio-id
    B. ap-system-profile
    C. mesh-whitelist-profile
    D. peer-ap mac
    正确答案:B
    解析:在配置Mesh网络的白名单时...

    【格式2：紧凑格式】
    1.以下哪条命令...【无线考点】
    A.xxx B.xxx C.xxx D.xxx
    正确答案:B
    解析:...

    【格式3：多选题】
    多选题
    1. xxx
    A.xxx
    B.xxx
    C.xxx
    D.xxx
    正确答案:ABCD
    解析:...
    """

    def __init__(self, db=None):
        self.db = db or Database()

    def extract_text(self, pdf_path):
        """提取PDF所有文本"""
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            total = len(pdf.pages)
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
                print(f"  解析进度: {i + 1}/{total}")
        return text

    def parse_text(self, text, source=None):
        """解析文本为题目列表"""
        questions = []

        # 按行分割并预处理
        lines = text.split('\n')

        current_question = None
        current_type = 'single'
        current_category = '未分类'

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            if not line:
                i += 1
                continue

            # 检测题目类型
            if re.match(r'^(单选题|选择题)', line):
                current_type = 'single'
                i += 1
                continue
            if '多选题' in line:
                current_type = 'multiple'
                i += 1
                continue
            if '判断题' in line:
                current_type = 'judge'
                i += 1
                continue
            if '填空题' in line:
                current_type = 'fill'
                i += 1
                continue

            # 检测考点分类
            cat_match = re.search(r'【(.+?)考点】', line)
            if cat_match:
                current_category = cat_match.group(1) + '考点'

            # 检测题目开头
            q_match = re.match(r'^(\d+)[.、]\s*(.+)', line)
            if q_match:
                # 保存上一题
                if current_question:
                    questions.append(current_question)

                question_no = int(q_match.group(1))
                content = q_match.group(2).strip()

                # 移除内容中的考点标记
                content = re.sub(r'【.+?考点】', '', content).strip()

                # 移除题目序号
                content = re.sub(r'^\d+[.、]\s*', '', content)

                current_question = {
                    'question_no': question_no,
                    'type': current_type,
                    'category': current_category,
                    'sub_category': None,
                    'content': content,
                    'option_a': None,
                    'option_b': None,
                    'option_c': None,
                    'option_d': None,
                    'answer': None,
                    'explanation': None,
                    'difficulty': 2,
                    'source': source
                }
                i += 1
                continue

            if current_question is None:
                i += 1
                continue

            # 检测选项 A. / B. / C. / D.
            opt_match = re.match(r'^([A-D])[.、．]\s*(.+)', line)
            if opt_match:
                opt_key = opt_match.group(1).lower()
                opt_value = opt_match.group(2).strip()
                # 清除选项中的答案解析
                opt_value = re.split(r'正确答案|解析', opt_value)[0].strip()
                # 如果一行有多个选项，拆分
                multi_opts = re.split(r'\s+([B-D])[.、．]', ' ' + opt_value)
                if len(multi_opts) > 1:
                    opt_value = multi_opts[0].strip()
                    # 处理剩余的选项
                    j = 1
                    while j < len(multi_opts) - 1:
                        next_key = multi_opts[j].lower()
                        next_val = multi_opts[j + 1].strip()
                        next_val = re.split(r'正确答案|解析', next_val)[0].strip()
                        current_question[f'option_{next_key}'] = next_val
                        j += 2

                current_question[f'option_{opt_key}'] = opt_value
                i += 1
                continue

            # 检测正确答案（支持多种格式）
            ans_match = re.search(r'正确答案[：:]\s*([A-D]+)', line)
            if not ans_match:
                ans_match = re.search(r'答案[：:]\s*([A-D]+)', line)
            if not ans_match:
                ans_match = re.search(r'参考答案[：:]\s*([A-D]+)', line)

            if ans_match:
                current_question['answer'] = ans_match.group(1).strip()
                # 检查同一行是否有解析
                exp_inline = re.search(r'解析[：:]\s*(.+)', line)
                if exp_inline:
                    current_question['explanation'] = exp_inline.group(1).strip()
                    i += 1
                    continue
                i += 1
                continue

            # 检测解析
            exp_match = re.search(r'解析[：:]\s*(.+)', line)
            if exp_match:
                explanation = exp_match.group(1).strip()
                j = i + 1
                while j < len(lines):
                    next_line = lines[j].strip()
                    if not next_line:
                        j += 1
                        if j < len(lines) and re.match(r'^\d+[.、]', lines[j].strip()):
                            break
                        continue
                    if re.match(r'^\d+[.、]', next_line) or re.match(r'^[A-D][.、]', next_line):
                        break
                    if '正确答案' in next_line:
                        break
                    explanation += ' ' + next_line
                    j += 1
                current_question['explanation'] = explanation
                i = j
                continue

            # 如果是判断题，可能直接以"正确/错误"作为答案
            if current_question['type'] == 'judge':
                if line in ['正确', '错误', '对', '错']:
                    current_question['answer'] = line
                    i += 1
                    continue

            i += 1

        # 保存最后一题
        if current_question:
            questions.append(current_question)

        # 过滤无效题目
        questions = [q for q in questions if q['content'] and q['answer']]

        # 统计
        print(f"\n📊 解析统计:")
        print(f"  总题目数: {len(questions)}")
        by_cat = {}
        by_type = {}
        for q in questions:
            by_cat[q['category']] = by_cat.get(q['category'], 0) + 1
            by_type[q['type']] = by_type.get(q['type'], 0) + 1

        for cat, count in by_cat.items():
            print(f"  {cat}: {count}题")
        for t, count in by_type.items():
            print(f"  {t}: {count}题")

        return questions

    def import_pdf(self, pdf_path, source=None):
        """导入PDF并保存到数据库"""
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")

        if not source:
            source = os.path.basename(pdf_path)

        print(f"📄 正在解析: {pdf_path}")
        text = self.extract_text(pdf_path)
        print(f"  提取文本长度: {len(text)} 字符")

        questions = self.parse_text(text, source=source)
        print(f"✅ 解析出 {len(questions)} 道题目")

        if questions:
            count = self.db.batch_add_questions(questions)
            print(f"✅ 成功导入 {count} 道题目到数据库")
            return count
        return 0

    def preview_parse(self, pdf_path, max_show=5):
        """预览解析结果（不保存）"""
        text = self.extract_text(pdf_path)
        questions = self.parse_text(text)
        print(f"\n共解析出 {len(questions)} 道题目")
        for q in questions[:max_show]:
            print("-" * 60)
            print(f"[{q['category']}] {q['type']} - 第{q['question_no']}题")
            print(f"内容: {q['content'][:80]}")
            for opt in ['a', 'b', 'c', 'd']:
                if q.get(f'option_{opt}'):
                    print(f"  {opt.upper()}. {q[f'option_{opt}'][:60]}")
            print(f"答案: {q['answer']}")
            if q.get('explanation'):
                print(f"解析: {q['explanation'][:100]}...")
        return questions


def import_pdf_to_db(pdf_path, source=None):
    """快捷函数：导入PDF到数据库"""
    importer = PDFImporter()
    return importer.import_pdf(pdf_path, source=source)


# ============ 命令行工具 ============
if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("=" * 60)
        print("PDF题库导入工具")
        print("=" * 60)
        print("用法:")
        print("  python pdf_importer.py <pdf文件路径>            # 导入")
        print("  python pdf_importer.py <pdf文件路径> --preview  # 预览")
        print("=" * 60)
        sys.exit(1)

    pdf_file = sys.argv[1]

    if '--preview' in sys.argv:
        importer = PDFImporter()
        importer.preview_parse(pdf_file)
    else:
        import_pdf_to_db(pdf_file)