"""
List Books - Read Apple Books book list
"""
import sqlite3
from pathlib import Path
from datetime import datetime


def convert_apple_time(timestamp):
    """Apple timestamp conversion function"""
    if not timestamp:
        return None
    apple_epoch = datetime(2001, 1, 1)
    unix_epoch = datetime(1970, 1, 1)
    offset = (apple_epoch - unix_epoch).total_seconds()
    created_datetime = datetime.fromtimestamp(timestamp + offset)
    return created_datetime.strftime("%Y-%m-%d %H:%M:%S")


def get_library_db_path() -> Path:
    """Get BKLibrary sqlite path"""
    library_base = Path.home() / "Library/Containers/com.apple.iBooksX/Data/Documents/BKLibrary"
    library_files = list(library_base.glob("BKLibrary*.sqlite"))
    
    if not library_files:
        raise RuntimeError("BKLibrary sqlite not found, please ensure Apple Books sync is complete")
    
    return library_files[0]


def get_all_books() -> list[dict]:
    """
    Get all books from Apple Books
    
    Returns:
        Book list, each containing asset_id, title, author, etc.
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
            "author": author or "Unknown",
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
    """Display book list"""
    if not books:
        print("No books found")
        return
    
    print(f"Total found {len(books)} books\n")
    print("=" * 120)
    
    for idx, book in enumerate(books, 1):
        print(f"\n📚 [{idx}] {book['title']}")
        print(f"   Author: {book['author']}")
        
        if book['kind']:
            print(f"   Kind: {book['kind']}")
        
        if book['language']:
            print(f"   Language: {book['language']}")
        
        if book['page_count']:
            print(f"   Page Count: {book['page_count']}")
        
        if book['reading_progress'] is not None:
            progress_percent = book['reading_progress'] * 100
            print(f"   Reading Progress: {progress_percent:.1f}%")
        
        if book['is_finished']:
            print(f"   Status: ✅ Finished")
        elif book['reading_progress'] and book['reading_progress'] > 0:
            print(f"   Status: 📖 Reading")
        else:
            print(f"   Status: 🆕 Not started")
        
        if book['last_open']:
            print(f"   Last Opened: {book['last_open']}")
        
        if book['genre']:
            print(f"   Genre: {book['genre']}")
        
        if book['year']:
            print(f"   Year: {book['year']}")
        
        print(f"   Asset ID: {book['asset_id']}")
        print("-" * 120)
    
    # Statistics
    print(f"\n\n📊 Statistics:")
    print(f"   Total Books: {len(books)}")
    
    finished_count = sum(1 for b in books if b['is_finished'])
    reading_count = sum(1 for b in books if b['reading_progress'] and b['reading_progress'] > 0 and not b['is_finished'])
    not_started_count = len(books) - finished_count - reading_count
    
    print(f"   Finished: {finished_count}")
    print(f"   Reading: {reading_count}")
    print(f"   Not Started: {not_started_count}")


if __name__ == "__main__":
    books = get_all_books()
    print_books(books)
