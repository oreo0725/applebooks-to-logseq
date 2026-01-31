"""
Books Manager - Manage target_books.json
"""
import json
from pathlib import Path
from typing import Optional


TARGET_BOOKS_FILE = Path(__file__).parent / "target_books.json"


def load_target_books() -> list[dict]:
    """Load target_books.json"""
    if not TARGET_BOOKS_FILE.exists():
        return []
    with open(TARGET_BOOKS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_target_books(books: list[dict]) -> None:
    """Save target_books.json"""
    with open(TARGET_BOOKS_FILE, "w", encoding="utf-8") as f:
        json.dump(books, f, ensure_ascii=False, indent=2)


def sync_from_apple_books(apple_books: list[dict]) -> list[dict]:
    """
    Sync book list from Apple Books, preserving existing sync status and alias
    
    Args:
        apple_books: Book list read from Apple Books
        
    Returns:
        Merged book list
    """
    existing = {book["asset_id"]: book for book in load_target_books()}
    
    result = []
    for book in apple_books:
        asset_id = book["asset_id"]
        if asset_id in existing:
            merged = {
                **book,
                "sync": existing[asset_id].get("sync", False),
                "alias": existing[asset_id].get("alias", ""),
            }
            result.append(merged)
        else:
            result.append({
                **book,
                "sync": False,
                "alias": "",
            })
    
    return result


def get_books_to_sync() -> list[dict]:
    """Get list of books to sync"""
    books = load_target_books()
    return [book for book in books if book.get("sync", False)]


def get_page_name(book: dict) -> str:
    """Get Logseq page name (alias prioritized)"""
    alias = book.get("alias", "").strip()
    return alias if alias else book.get("title", "Unknown")
