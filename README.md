# 📚 AppleBooks to Logseq

<p align="center">
  <strong>Sync your Apple Books highlights and notes to Logseq with a single command.</strong>
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#installation">Installation</a> •
  <a href="#usage">Usage</a> •
  <a href="#configuration">Configuration</a> •
  <a href="#template-customization">Templates</a> •
  <a href="#contributing">Contributing</a>
</p>

---

## ✨ Features

- 🔄 **One-command sync** — Sync all your Apple Books highlights to Logseq
- 📖 **Selective sync** — Choose which books to sync via `target_books.json`
- 🎨 **Customizable templates** — Define your own page format with Jinja2-style syntax
- 🔗 **Logseq-native format** — Outputs proper Logseq properties, tags, and page links
- 📝 **Notes support** — Includes both highlights and your personal annotations
- 🔁 **Incremental updates** — Re-run anytime; existing pages are updated seamlessly

## 📋 Prerequisites

- macOS (Apple Books is required)
- [Logseq](https://logseq.com/) running locally with **Developer Mode** enabled
- [uv](https://github.com/astral-sh/uv) — Fast Python package manager
- Python 3.10+

## 🚀 Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/oreo0725/applebooks-to-logseq.git
   cd applebooks-to-logseq
   ```

2. **Install dependencies**

   ```bash
   uv sync
   ```

3. **Configure environment variables**

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add your Logseq API token:

   ```
   LOGSEQ_URL=http://127.0.0.1:12315/api
   LOGSEQ_TOKEN=your_token_here
   ```

   > 💡 **How to get your Logseq token:**  
   > In Logseq, go to **Settings → Advanced → Developer mode** (enable it), then find your authorization token.
   
   > 📝 **Note:** The default `LOGSEQ_URL` is `http://127.0.0.1:12315/api`. You only need to change it if your Logseq API runs on a different port.

## 📖 Usage

### Quick Start

```bash
uv run python sync.py
```

On first run, the script will:

1. Scan your Apple Books library
2. Generate `target_books.json` with all your books
3. Exit — prompting you to configure which books to sync

### Selecting Books to Sync

Edit `target_books.json` and set `"sync": true` for books you want to sync:

```json
{
  "asset_id": "ABC123...",
  "title": "Atomic Habits",
  "author": "James Clear",
  "sync": true,
  "alias": "Atomic Habits"
}
```

| Field | Description |
|-------|-------------|
| `sync` | Set to `true` to include this book in sync |
| `alias` | (Optional) Custom page name in Logseq |

### Running the Sync

```bash
uv run python sync.py
```

The script will:

1. ✅ Connect to Logseq API
2. 📚 Read your selected books from `target_books.json`
3. 📝 Fetch highlights and notes from Apple Books
4. 🚀 Create/update pages in Logseq

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `LOGSEQ_URL` | Logseq API endpoint URL (default: `http://127.0.0.1:12315/api`) | ❌ |
| `LOGSEQ_TOKEN` | Your Logseq API authorization token | ✅ |

### Files

| File | Description |
|------|-------------|
| `target_books.json` | Book list with sync preferences (auto-generated) |
| `template.md` | Customizable page template |
| `.env` | Environment variables |

## 🎨 Template Customization

Customize how your highlights appear in Logseq by editing `template.md`.

### Default Template

```markdown
- author:: [[{{ author }}]]
- full-title:: "{{ title }}"
- category:: #books
- tags:: #[[reading]]
- Highlights first synced by [[{{ sync_date }}]]
{% for highlight in highlights %}
  - > {{ highlight.text }}{% if highlight.page %} (Page {{ highlight.page }}){% endif %}
    {% if highlight.note %}- Note:: {{ highlight.note }}{% endif %}
{% endfor %}
```

### Available Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{ title }}` | Book title | "Atomic Habits" |
| `{{ author }}` | Author name | "James Clear" |
| `{{ sync_date }}` | Current sync date | "2026-01-31" |

### Highlight Properties

| Property | Description |
|----------|-------------|
| `{{ highlight.text }}` | The highlighted text |
| `{{ highlight.note }}` | Your annotation (if any) |
| `{{ highlight.page }}` | Page number (if available) |
| `{{ highlight.created_at }}` | Creation timestamp |

### Template Syntax

- **Variables:** `{{ variable_name }}`
- **Loops:** `{% for item in list %}...{% endfor %}`
- **Conditionals:** `{% if condition %}...{% endif %}`

### Example: Minimal Template

```markdown
# {{ title }}

Author: {{ author }}

## Highlights

{% for highlight in highlights %}
- {{ highlight.text }}
{% endfor %}
```

## 🏗️ Project Structure

```
applebooks-to-logseq/
├── sync.py              # Main entry point
├── books_manager.py     # Book list management
├── list_books.py        # Apple Books library scanner
├── list_all_note.py     # Highlights/notes extractor
├── template_engine.py   # Template rendering engine
├── logseq_sync.py       # Logseq API client
├── template.md          # Page template
├── target_books.json    # Book sync configuration (generated)
└── .env                 # Environment variables
```

## 🤝 Contributing

Contributions are welcome! Feel free to:

- 🐛 Report bugs
- 💡 Suggest features
- 🔧 Submit pull requests

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 🙏 Acknowledgments

- [Logseq](https://logseq.com/) — The amazing local-first knowledge base
- [Apple Books](https://www.apple.com/apple-books/) — For making reading and highlighting seamless

---

<p align="center">
  Made with ❤️ for the Logseq community
</p>
