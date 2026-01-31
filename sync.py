#!/usr/bin/env python3
"""
Apple Books to Logseq Sync Tool
Sync highlights from Apple Books to Logseq
"""
import sys
from pathlib import Path

from books_manager import (
    load_target_books,
    save_target_books,
    sync_from_apple_books,
    get_books_to_sync,
    get_page_name,
    TARGET_BOOKS_FILE,
)
from list_books import get_all_books
from list_all_note import get_all_annotations
from template_engine import generate_page_content, save_default_template
from logseq_sync import LogseqClient, sync_book_to_logseq


def init_target_books() -> bool:
    """Initialize target_books.json"""
    print("📚 Initializing book list...")
    
    try:
        apple_books = get_all_books()
        print(f"   Read {len(apple_books)} books from Apple Books")
    except RuntimeError as e:
        print(f"❌ {e}")
        return False
    
    merged_books = sync_from_apple_books(apple_books)
    save_target_books(merged_books)
    print(f"✅ Saved to {TARGET_BOOKS_FILE}")
    print(f"   Please edit this file and set 'sync' to true for books you want to sync")
    
    return True


def main():
    print("=" * 60)
    print("🔄 Apple Books → Logseq Sync Tool")
    print("=" * 60)
    print()
    
    if not TARGET_BOOKS_FILE.exists():
        print("⚠️  target_books.json not found, initializing...")
        if not init_target_books():
            sys.exit(1)
        print()
        print("Please edit target_books.json and run this script again")
        sys.exit(0)
    
    save_default_template()
    
    print("📚 Updating book list from Apple Books...")
    try:
        apple_books = get_all_books()
        print(f"   Read {len(apple_books)} books from Apple Books")
    except RuntimeError as e:
        print(f"❌ {e}")
        sys.exit(1)
    
    merged_books = sync_from_apple_books(apple_books)
    save_target_books(merged_books)
    print(f"✅ Updated {TARGET_BOOKS_FILE}")
    print()
    
    print("🔌 Connecting to Logseq API...")
    client = LogseqClient()
    
    if not client.check_connection():
        print()
        print("Tip: Please confirm the following:")
        print("  1. Logseq is running")
        print("  2. Developer Mode is enabled in Settings → Advanced")
        print("  3. LOGSEQ_TOKEN is set in .env file")
        sys.exit(1)
    print()
    
    books_to_sync = get_books_to_sync()
    
    if not books_to_sync:
        print("⚠️  No books need to be synced")
        print("   Please edit target_books.json and set 'sync' to true for books you want to sync")
        sys.exit(0)
    
    print(f"📖 Found {len(books_to_sync)} books to sync")
    print()
    
    print("📝 Reading Apple Books annotations...")
    try:
        all_annotations = get_all_annotations()
        total_annotations = sum(len(anns) for anns in all_annotations.values())
        print(f"   Total {total_annotations} annotations")
    except RuntimeError as e:
        print(f"❌ {e}")
        sys.exit(1)
    print()
    
    print("🚀 Starting sync...")
    print("-" * 60)
    
    success_count = 0
    fail_count = 0
    
    for book in books_to_sync:
        asset_id = book["asset_id"]
        page_name = get_page_name(book)
        title = book.get("title", "Unknown")
        author = book.get("author", "Unknown")
        
        annotations = all_annotations.get(asset_id, [])
        
        if not annotations:
            print(f"⚠️  {title}: No annotations, skipping")
            continue
        
        content = generate_page_content(
            title=title,
            author=author,
            highlights=annotations,
        )
        
        if sync_book_to_logseq(client, page_name, content):
            success_count += 1
        else:
            fail_count += 1
    
    print("-" * 60)
    print()
    print("📊 Sync completed!")
    print(f"   ✅ Success: {success_count}")
    print(f"   ❌ Failed: {fail_count}")


if __name__ == "__main__":
    main()
