"""
Template Engine - 解析並渲染 Logseq template
"""
from datetime import datetime
from pathlib import Path
from typing import Any


DEFAULT_TEMPLATE = """\
- author:: [[{{ author }}]]
- full-title:: "{{ title }}"
- category:: #books
- tags:: #[[reading]]
- Highlights first synced by [[{{ sync_date }}]]
{% for highlight in highlights %}
- {{ highlight.text }}{% if highlight.page %} (Page {{ highlight.page }}){% endif %}
	{% if highlight.note %}- Note:: {{ highlight.note }}{% endif %}
{% endfor %}
"""

TEMPLATE_FILE = Path(__file__).parent / "template.md"


def load_template() -> str:
    """載入 template，若不存在則使用預設"""
    if TEMPLATE_FILE.exists():
        return TEMPLATE_FILE.read_text(encoding="utf-8")
    return DEFAULT_TEMPLATE


def save_default_template() -> None:
    """儲存預設 template 供使用者修改"""
    if not TEMPLATE_FILE.exists():
        TEMPLATE_FILE.write_text(DEFAULT_TEMPLATE, encoding="utf-8")


def render_template(
    template: str,
    title: str,
    author: str,
    highlights: list[dict],
    sync_date: str | None = None,
) -> str:
    """
    渲染 template 為 Logseq markdown 格式
    
    Args:
        template: Template 字串
        title: 書名
        author: 作者
        highlights: Highlight 列表，每個包含 text, note, page, created_at
        sync_date: 同步日期
        
    Returns:
        渲染後的 Logseq markdown
    """
    if sync_date is None:
        sync_date = datetime.now().strftime("%Y-%m-%d")
    
    # 簡單的 template 解析（支援基本變數替換和 for loop）
    result = template
    
    # 替換簡單變數
    result = result.replace("{{ author }}", author or "Unknown")
    result = result.replace("{{ title }}", title or "Unknown")
    result = result.replace("{{ sync_date }}", sync_date)
    
    # 處理 for loop
    if "{% for highlight in highlights %}" in result:
        # 找出 for loop 區塊
        start_marker = "{% for highlight in highlights %}"
        end_marker = "{% endfor %}"
        
        start_idx = result.find(start_marker)
        end_idx = result.find(end_marker)
        
        if start_idx != -1 and end_idx != -1:
            before = result[:start_idx]
            loop_template = result[start_idx + len(start_marker):end_idx]
            after = result[end_idx + len(end_marker):]
            
            # 渲染每個 highlight
            rendered_highlights = []
            for h in highlights:
                item = loop_template
                
                # 替換 highlight 變數
                item = item.replace("{{ highlight.text }}", h.get("text", ""))
                
                # 處理條件: page
                if "{% if highlight.page %}" in item:
                    page_start = "{% if highlight.page %}"
                    page_end = "{% endif %}"
                    ps = item.find(page_start)
                    pe = item.find(page_end, ps)
                    if ps != -1 and pe != -1:
                        page_content = item[ps + len(page_start):pe]
                        if h.get("page"):
                            page_content = page_content.replace("{{ highlight.page }}", str(h["page"]))
                        else:
                            page_content = ""
                        item = item[:ps] + page_content + item[pe + len(page_end):]
                
                # 處理條件: note
                if "{% if highlight.note %}" in item:
                    note_start = "{% if highlight.note %}"
                    note_end = "{% endif %}"
                    ns = item.find(note_start)
                    ne = item.find(note_end, ns)
                    if ns != -1 and ne != -1:
                        note_content = item[ns + len(note_start):ne]
                        if h.get("note"):
                            note_content = note_content.replace("{{ highlight.note }}", h["note"])
                        else:
                            note_content = ""
                        item = item[:ns] + note_content + item[ne + len(note_end):]
                
                rendered_highlights.append(item.strip('\n'))
            
            result = before + "\n".join(rendered_highlights) + after
    
    # 清理多餘空行
    lines = [line for line in result.split("\n") if line.strip()]
    return "\n".join(lines)


def generate_page_content(
    title: str,
    author: str,
    highlights: list[dict],
) -> str:
    """
    產生完整的 Logseq page 內容
    
    Args:
        title: 書名
        author: 作者
        highlights: Highlight 列表
        
    Returns:
        Logseq page 內容
    """
    template = load_template()
    return render_template(template, title, author, highlights)
