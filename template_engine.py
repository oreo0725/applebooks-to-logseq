"""
Template Engine - Parse and render Logseq template
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
    """Load template, use default if not exists"""
    if TEMPLATE_FILE.exists():
        return TEMPLATE_FILE.read_text(encoding="utf-8")
    return DEFAULT_TEMPLATE


def save_default_template() -> None:
    """Save default template for customization"""
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
    Render template to Logseq markdown format
    
    Args:
        template: Template string
        title: Title
        author: Author
        highlights: List of highlights, each containing text, note, page, created_at
        sync_date: Sync date
        
    Returns:
        Rendered Logseq markdown
    """
    if sync_date is None:
        sync_date = datetime.now().strftime("%Y-%m-%d")
    
    result = template
    
    result = result.replace("{{ author }}", author or "Unknown")
    result = result.replace("{{ title }}", title or "Unknown")
    result = result.replace("{{ sync_date }}", sync_date)
    
    if "{% for highlight in highlights %}" in result:
        start_marker = "{% for highlight in highlights %}"
        end_marker = "{% endfor %}"
        
        start_idx = result.find(start_marker)
        end_idx = result.find(end_marker)
        
        if start_idx != -1 and end_idx != -1:
            before = result[:start_idx]
            loop_template = result[start_idx + len(start_marker):end_idx]
            after = result[end_idx + len(end_marker):]
            
            rendered_highlights = []
            for h in highlights:
                item = loop_template
                
                item = item.replace("{{ highlight.text }}", h.get("text", ""))
                
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
    
    lines = [line for line in result.split("\n") if line.strip()]
    return "\n".join(lines)


def generate_page_content(
    title: str,
    author: str,
    highlights: list[dict],
) -> str:
    """
    Generate complete Logseq page content
    
    Args:
        title: Title
        author: Author
        highlights: Highlight list
        
    Returns:
        Logseq page content
    """
    template = load_template()
    return render_template(template, title, author, highlights)
