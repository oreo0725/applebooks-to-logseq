#!/usr/bin/env python3
"""
Apple Books to Logseq Sync Tool
將 Apple Books 中的 highlights 同步到 Logseq
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
    """初始化 target_books.json"""
    print("📚 初始化書籍清單...")
    
    try:
        apple_books = get_all_books()
        print(f"   從 Apple Books 讀取到 {len(apple_books)} 本書")
    except RuntimeError as e:
        print(f"❌ {e}")
        return False
    
    merged_books = sync_from_apple_books(apple_books)
    save_target_books(merged_books)
    print(f"✅ 已儲存到 {TARGET_BOOKS_FILE}")
    print(f"   請編輯此檔案，將需要同步的書籍 'sync' 設為 true")
    
    return True


def main():
    print("=" * 60)
    print("🔄 Apple Books → Logseq 同步工具")
    print("=" * 60)
    print()
    
    # 1. 檢查 target_books.json
    if not TARGET_BOOKS_FILE.exists():
        print("⚠️  找不到 target_books.json，正在初始化...")
        if not init_target_books():
            sys.exit(1)
        print()
        print("請編輯 target_books.json 後重新執行此腳本")
        sys.exit(0)
    
    # 確保 template 存在
    save_default_template()
    
    # 2. 從 Apple Books 更新書籍清單
    print("📚 從 Apple Books 更新書籍清單...")
    try:
        apple_books = get_all_books()
        print(f"   從 Apple Books 讀取到 {len(apple_books)} 本書")
    except RuntimeError as e:
        print(f"❌ {e}")
        sys.exit(1)
    
    merged_books = sync_from_apple_books(apple_books)
    save_target_books(merged_books)
    print(f"✅ 已更新 {TARGET_BOOKS_FILE}")
    print()
    
    # 3. 檢查 Logseq API 連線
    print("🔌 連接 Logseq API...")
    client = LogseqClient()
    
    if not client.check_connection():
        print()
        print("提示: 請確認以下事項:")
        print("  1. Logseq 已啟動")
        print("  2. 已在 Settings → Advanced 中啟用 Developer Mode")
        print("  3. 已在 .env 檔案中設定 LOGSEQ_TOKEN")
        sys.exit(1)
    print()
    
    # 4. 取得要同步的書籍
    books_to_sync = get_books_to_sync()
    
    if not books_to_sync:
        print("⚠️  沒有書籍需要同步")
        print("   請編輯 target_books.json，將需要同步的書籍 'sync' 設為 true")
        sys.exit(0)
    
    print(f"📖 找到 {len(books_to_sync)} 本書需要同步")
    print()
    
    # 5. 取得所有 annotations
    print("📝 讀取 Apple Books annotations...")
    try:
        all_annotations = get_all_annotations()
        total_annotations = sum(len(anns) for anns in all_annotations.values())
        print(f"   共 {total_annotations} 筆 annotations")
    except RuntimeError as e:
        print(f"❌ {e}")
        sys.exit(1)
    print()
    
    # 6. 同步每本書
    print("🚀 開始同步...")
    print("-" * 60)
    
    success_count = 0
    fail_count = 0
    
    for book in books_to_sync:
        asset_id = book["asset_id"]
        page_name = get_page_name(book)
        title = book.get("title", "Unknown")
        author = book.get("author", "Unknown")
        
        # 取得該書的 annotations
        annotations = all_annotations.get(asset_id, [])
        
        if not annotations:
            print(f"⚠️  {title}: 沒有 annotations，跳過")
            continue
        
        # 產生 page 內容
        content = generate_page_content(
            title=title,
            author=author,
            highlights=annotations,
        )
        
        # 同步到 Logseq
        if sync_book_to_logseq(client, page_name, content):
            success_count += 1
        else:
            fail_count += 1
    
    # 7. 完成
    print("-" * 60)
    print()
    print("📊 同步完成!")
    print(f"   ✅ 成功: {success_count}")
    print(f"   ❌ 失敗: {fail_count}")


if __name__ == "__main__":
    main()
