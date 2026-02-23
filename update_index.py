#!/usr/bin/env python3
import re

def update_index_file():
    # 讀取索引文件
    with open('tcm_notebook/html/huangdi_waijing_index.html', 'r', encoding='utf-8') as f:
        content = f.read()

    # 定義需要更新的章節及其對應的新連結
    updates = [
        # 第35篇
        (r'<li><span class="chapter-name">35 小腸火篇</span><span class="pending">研究中</span></li>',
         '<li><span class="chapter-name">35 小腸火篇</span><div class="links"><a href="https://htmlpreview.github.io/?https://github.com/kimitseng0331/tcm_notebook/blob/main/html/hwj_1-35_小腸火篇_research_report.html" class="report-link">報告</a><a href="https://htmlpreview.github.io/?https://github.com/kimitseng0331/tcm_notebook/blob/main/html/hwj_1-35_小腸火篇_summary.html" class="summary-link">摘要</a></div></li>'),

        # 第36篇
        (r'<li><span class="chapter-name">36 命門真火篇</span><span class="pending">研究中</span></li>',
         '<li><span class="chapter-name">36 命門真火篇</span><div class="links"><a href="https://htmlpreview.github.io/?https://github.com/kimitseng0331/tcm_notebook/blob/main/html/hwj_1-36_命門真火篇_research_report.html" class="report-link">報告</a><a href="https://htmlpreview.github.io/?https://github.com/kimitseng0331/tcm_notebook/blob/main/html/hwj_1-36_命門真火篇_summary.html" class="summary-link">摘要</a></div></li>'),

        # 第37篇
        (r'<li><span class="chapter-name">37 命門經主篇</span><span class="pending">研究中</span></li>',
         '<li><span class="chapter-name">37 命門經主篇</span><div class="links"><a href="https://htmlpreview.github.io/?https://github.com/kimitseng0331/tcm_notebook/blob/main/html/hwj_1-37_命門經主篇_research_report.html" class="report-link">報告</a><a href="https://htmlpreview.github.io/?https://github.com/kimitseng0331/tcm_notebook/blob/main/html/hwj_1-37_命門經主篇_summary.html" class="summary-link">摘要</a></div></li>'),

        # 第38篇
        (r'<li><span class="chapter-name">38 五行生克篇</span><span class="pending">研究中</span></li>',
         '<li><span class="chapter-name">38 五行生克篇</span><div class="links"><a href="https://htmlpreview.github.io/?https://github.com/kimitseng0331/tcm_notebook/blob/main/html/hwj_1-38_五行生克篇_research_report.html" class="report-link">報告</a><a href="https://htmlpreview.github.io/?https://github.com/kimitseng0331/tcm_notebook/blob/main/html/hwj_1-38_五行生克篇_summary.html" class="summary-link">摘要</a></div></li>'),

        # 第39篇
        (r'<li><span class="chapter-name">39 小心真主篇</span><span class="pending">研究中</span></li>',
         '<li><span class="chapter-name">39 小心真主篇</span><div class="links"><a href="https://htmlpreview.github.io/?https://github.com/kimitseng0331/tcm_notebook/blob/main/html/hwj_1-39_小心真主篇_research_report.html" class="report-link">報告</a><a href="https://htmlpreview.github.io/?https://github.com/kimitseng0331/tcm_notebook/blob/main/html/hwj_1-39_小心真主篇_summary.html" class="summary-link">摘要</a></div></li>'),

        # 第40篇
        (r'<li><span class="chapter-name">40 水不克火篇</span><span class="pending">研究中</span></li>',
         '<li><span class="chapter-name">40 水不克火篇</span><div class="links"><a href="https://htmlpreview.github.io/?https://github.com/kimitseng0331/tcm_notebook/blob/main/html/hwj_1-40_水不克火篇_research_report.html" class="report-link">報告</a><a href="https://htmlpreview.github.io/?https://github.com/kimitseng0331/tcm_notebook/blob/main/html/hwj_1-40_水不克火篇_summary.html" class="summary-link">摘要</a></div></li>')
    ]

    # 依次進行更新
    for pattern, replacement in updates:
        content = re.sub(pattern, replacement, content, flags=re.DOTALL)

    # 將更新後內容寫回文件
    with open('tcm_notebook/html/huangdi_waijing_index.html', 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == '__main__':
    update_index_file()