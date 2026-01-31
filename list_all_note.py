"""
List All Notes - Read Apple Books annotations (highlights & notes)
"""
import sqlite3
from pathlib import Path
from datetime import datetime
from collections import defaultdict


def convert_apple_time(timestamp):
    """Apple timestamp conversion function"""
    if not timestamp:
        return None
    apple_epoch = datetime(2001, 1, 1)
    unix_epoch = datetime(1970, 1, 1)
    offset = (apple_epoch - unix_epoch).total_seconds()
    created_datetime = datetime.fromtimestamp(timestamp + offset)
    return created_datetime.strftime("%Y-%m-%d %H:%M:%S")


def get_annotation_db_path() -> Path:
    """Get AEAnnotation sqlite path"""
    base = Path.home() / "Library/Containers/com.apple.iBooksX/Data/Documents/AEAnnotation"
    db_files = list(base.glob("AEAnnotation*.sqlite"))
    
    if not db_files:
        raise RuntimeError("AEAnnotation sqlite not found, please ensure Apple Books sync is complete")
    
    return db_files[0]


def get_library_db_path() -> Path:
    """Get BKLibrary sqlite path"""
    library_base = Path.home() / "Library/Containers/com.apple.iBooksX/Data/Documents/BKLibrary"
    library_files = list(library_base.glob("BKLibrary*.sqlite"))
    
    if not library_files:
        raise RuntimeError("BKLibrary sqlite not found")
    
    return library_files[0]


def get_all_annotations() -> dict[str, list[dict]]:
    """
    Get all annotations, grouped by asset_id
    
    Returns:
        dict: Key is asset_id, value is the list of annotations for that book
    """
    annotation_db_path = get_annotation_db_path()
    library_db_path = get_library_db_path()
    
    conn = sqlite3.connect(annotation_db_path)
    cursor = conn.cursor()
    cursor.execute(f"ATTACH DATABASE '{library_db_path}' AS library")
    
    cursor.execute("""
        SELECT
            a.ZANNOTATIONSELECTEDTEXT,
            a.ZANNOTATIONNOTE,
            a.ZANNOTATIONCREATIONDATE,
            a.ZANNOTATIONASSETID,
            b.ZTITLE,
            b.ZAUTHOR
        FROM ZAEANNOTATION a
        LEFT JOIN library.ZBKLIBRARYASSET b
            ON a.ZANNOTATIONASSETID = b.ZASSETID
        WHERE a.ZANNOTATIONSELECTEDTEXT IS NOT NULL
           OR a.ZANNOTATIONNOTE IS NOT NULL
        ORDER BY a.ZANNOTATIONCREATIONDATE ASC
    """)
    
    rows = cursor.fetchall()
    conn.close()
    
    annotations_by_book = defaultdict(list)
    for row in rows:
        highlight, note, created_at, asset_id, title, author = row
        if asset_id:
            annotations_by_book[asset_id].append({
                "text": highlight or "",
                "note": note or "",
                "created_at": convert_apple_time(created_at),
                "title": title,
                "author": author,
            })
    
    return dict(annotations_by_book)


def get_annotations_by_asset_id(asset_id: str) -> list[dict]:
    """
    Get annotations for a specific book
    
    Args:
        asset_id: Book Asset ID
        
    Returns:
        List of annotations for that book
    """
    all_annotations = get_all_annotations()
    return all_annotations.get(asset_id, [])


def print_annotations(annotations_by_book: dict[str, list[dict]]) -> None:
    """Display all annotations"""
    if not annotations_by_book:
        print("No annotations found")
        return
    
    total_count = sum(len(anns) for anns in annotations_by_book.values())
    print(f"Total found {total_count} annotations from {len(annotations_by_book)} books\n")
    print("=" * 100)
    
    for book_idx, (asset_id, annotations) in enumerate(annotations_by_book.items(), 1):
        if not annotations:
            continue
            
        title = annotations[0].get("title", "Unknown Book")
        author = annotations[0].get("author", "Unknown Author")
        
        print(f"\n📚 [{book_idx}] {title}")
        print(f"   Author: {author}")
        print(f"   Asset ID: {asset_id}")
        print(f"   Total {len(annotations)} annotations")
        print("=" * 100)
        
        for ann_idx, ann in enumerate(annotations, 1):
            created_str = ann.get("created_at", "N/A")
            
            print(f"\n  [{ann_idx}] Created At: {created_str}")
            
            if ann.get("text"):
                print(f"  📝 Highlight:")
                for line in ann["text"].split('\n'):
                    print(f"     {line}")
            
            if ann.get("note"):
                print(f"  💭 Note:")
                for line in ann["note"].split('\n'):
                    print(f"     {line}")
            
            print("  " + "-" * 96)
        
        print("\n" + "=" * 100)


if __name__ == "__main__":
    annotations = get_all_annotations()
    print_annotations(annotations)
