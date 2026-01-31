"""
Books Manager - 管理 target_books.json
"""
import json
from pathlib import Path
from typing import Optional


TARGET_BOOKS_FILE = Path(__file__).parent / "target_books.json"


def load_target_books() -> list[dict]:
    """載入 target_books.json"""
    if not TARGET_BOOKS_FILE.exists():
        return []
    with open(TARGET_BOOKS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_target_books(books: list[dict]) -> None:
    """儲存 target_books.json"""
    with open(TARGET_BOOKS_FILE, "w", encoding="utf-8") as f:
        json.dump(books, f, ensure_ascii=False, indent=2)


def sync_from_apple_books(apple_books: list[dict]) -> list[dict]:
    """
    從 Apple Books 同步書單，保留既有的 sync 狀態和 alias
    
    Args:
        apple_books: 從 Apple Books 讀取的書籍列表
        
    Returns:
        合併後的書籍列表
    """
    existing = {book["asset_id"]: book for book in load_target_books()}
    
    result = []
    for book in apple_books:
        asset_id = book["asset_id"]
        if asset_id in existing:
            # 保留既有設定，更新書籍資訊
            merged = {
                **book,
                "sync": existing[asset_id].get("sync", False),
                "alias": existing[asset_id].get("alias", ""),
            }
            result.append(merged)
        else:
            # 新書預設不同步
            result.append({
                **book,
                "sync": False,
                "alias": "",
            })
    
    return result


def get_books_to_sync() -> list[dict]:
    """取得需要同步的書籍列表"""
    books = load_target_books()
    return [book for book in books if book.get("sync", False)]


def get_page_name(book: dict) -> str:
    """取得 Logseq page 名稱（優先使用 alias）"""
    alias = book.get("alias", "").strip()
    return alias if alias else book.get("title", "Unknown")
