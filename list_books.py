"""
List Books - 讀取 Apple Books 書籍列表
"""
import sqlite3
from pathlib import Path
from datetime import datetime


def convert_apple_time(timestamp):
    """Apple 的時間戳記轉換函數"""
    if not timestamp:
        return None
    apple_epoch = datetime(2001, 1, 1)
    unix_epoch = datetime(1970, 1, 1)
    offset = (apple_epoch - unix_epoch).total_seconds()
    created_datetime = datetime.fromtimestamp(timestamp + offset)
    return created_datetime.strftime("%Y-%m-%d %H:%M:%S")


def get_library_db_path() -> Path:
    """取得 BKLibrary sqlite 路徑"""
    library_base = Path.home() / "Library/Containers/com.apple.iBooksX/Data/Documents/BKLibrary"
    library_files = list(library_base.glob("BKLibrary*.sqlite"))
    
    if not library_files:
        raise RuntimeError("找不到 BKLibrary sqlite，請確認 Apple Books 有同步完成")
    
    return library_files[0]


def get_all_books() -> list[dict]:
    """
    取得 Apple Books 中所有書籍
    
    Returns:
        書籍列表，每個書籍包含 asset_id, title, author 等資訊
    """
    library_db_path = get_library_db_path()
    conn = sqlite3.connect(library_db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT
            ZTITLE,
            ZAUTHOR,
            ZKIND,
            ZLANGUAGE,
            ZPAGECOUNT,
            ZREADINGPROGRESS,
            ZLASTOPENDATE,
            ZCREATIONDATE,
            ZISFINISHED,
            ZASSETID,
            ZGENRE,
            ZYEAR
        FROM ZBKLIBRARYASSET
        WHERE ZTITLE IS NOT NULL
        ORDER BY ZLASTOPENDATE DESC NULLS LAST
    """)
    
    rows = cursor.fetchall()
    conn.close()
    
    books = []
    for row in rows:
        title, author, kind, language, page_count, reading_progress, last_open, created, is_finished, asset_id, genre, year = row
        
        books.append({
            "asset_id": asset_id,
            "title": title,
            "author": author or "未知",
            "kind": kind,
            "language": language,
            "page_count": page_count,
            "reading_progress": reading_progress,
            "last_open": convert_apple_time(last_open),
            "created": convert_apple_time(created),
            "is_finished": bool(is_finished),
            "genre": genre,
            "year": year,
        })
    
    return books


def print_books(books: list[dict]) -> None:
    """顯示書籍列表"""
    if not books:
        print("沒有找到任何書籍")
        return
    
    print(f"總共找到 {len(books)} 本書\n")
    print("=" * 120)
    
    for idx, book in enumerate(books, 1):
        print(f"\n📚 [{idx}] {book['title']}")
        print(f"   作者: {book['author']}")
        
        if book['kind']:
            print(f"   類型: {book['kind']}")
        
        if book['language']:
            print(f"   語言: {book['language']}")
        
        if book['page_count']:
            print(f"   頁數: {book['page_count']}")
        
        if book['reading_progress'] is not None:
            progress_percent = book['reading_progress'] * 100
            print(f"   閱讀進度: {progress_percent:.1f}%")
        
        if book['is_finished']:
            print(f"   狀態: ✅ 已完成")
        elif book['reading_progress'] and book['reading_progress'] > 0:
            print(f"   狀態: 📖 閱讀中")
        else:
            print(f"   狀態: 🆕 未開始")
        
        if book['last_open']:
            print(f"   最後開啟: {book['last_open']}")
        
        if book['genre']:
            print(f"   分類: {book['genre']}")
        
        if book['year']:
            print(f"   出版年份: {book['year']}")
        
        print(f"   Asset ID: {book['asset_id']}")
        print("-" * 120)
    
    # 統計資訊
    print(f"\n\n📊 統計資訊:")
    print(f"   總書籍數: {len(books)}")
    
    finished_count = sum(1 for b in books if b['is_finished'])
    reading_count = sum(1 for b in books if b['reading_progress'] and b['reading_progress'] > 0 and not b['is_finished'])
    not_started_count = len(books) - finished_count - reading_count
    
    print(f"   已完成: {finished_count}")
    print(f"   閱讀中: {reading_count}")
    print(f"   未開始: {not_started_count}")


if __name__ == "__main__":
    books = get_all_books()
    print_books(books)
