"""
List All Notes - 讀取 Apple Books annotations (highlights & notes)
"""
import sqlite3
from pathlib import Path
from datetime import datetime
from collections import defaultdict


def convert_apple_time(timestamp):
    """Apple 的時間戳記轉換函數"""
    if not timestamp:
        return None
    apple_epoch = datetime(2001, 1, 1)
    unix_epoch = datetime(1970, 1, 1)
    offset = (apple_epoch - unix_epoch).total_seconds()
    created_datetime = datetime.fromtimestamp(timestamp + offset)
    return created_datetime.strftime("%Y-%m-%d %H:%M:%S")


def get_annotation_db_path() -> Path:
    """取得 AEAnnotation sqlite 路徑"""
    base = Path.home() / "Library/Containers/com.apple.iBooksX/Data/Documents/AEAnnotation"
    db_files = list(base.glob("AEAnnotation*.sqlite"))
    
    if not db_files:
        raise RuntimeError("找不到 AEAnnotation sqlite，請確認 Apple Books 有同步完成")
    
    return db_files[0]


def get_library_db_path() -> Path:
    """取得 BKLibrary sqlite 路徑"""
    library_base = Path.home() / "Library/Containers/com.apple.iBooksX/Data/Documents/BKLibrary"
    library_files = list(library_base.glob("BKLibrary*.sqlite"))
    
    if not library_files:
        raise RuntimeError("找不到 BKLibrary sqlite")
    
    return library_files[0]


def get_all_annotations() -> dict[str, list[dict]]:
    """
    取得所有 annotations，按 asset_id 分組
    
    Returns:
        dict: key 為 asset_id，value 為該書的 annotations 列表
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
    取得指定書籍的 annotations
    
    Args:
        asset_id: 書籍 Asset ID
        
    Returns:
        該書的 annotations 列表
    """
    all_annotations = get_all_annotations()
    return all_annotations.get(asset_id, [])


def print_annotations(annotations_by_book: dict[str, list[dict]]) -> None:
    """顯示所有 annotations"""
    if not annotations_by_book:
        print("沒有找到任何 annotations")
        return
    
    total_count = sum(len(anns) for anns in annotations_by_book.values())
    print(f"總共找到 {total_count} 筆 annotations，來自 {len(annotations_by_book)} 本書\n")
    print("=" * 100)
    
    for book_idx, (asset_id, annotations) in enumerate(annotations_by_book.items(), 1):
        if not annotations:
            continue
            
        title = annotations[0].get("title", "未知書籍")
        author = annotations[0].get("author", "未知作者")
        
        print(f"\n📚 [{book_idx}] {title}")
        print(f"   作者: {author}")
        print(f"   Asset ID: {asset_id}")
        print(f"   共 {len(annotations)} 筆 annotations")
        print("=" * 100)
        
        for ann_idx, ann in enumerate(annotations, 1):
            created_str = ann.get("created_at", "N/A")
            
            print(f"\n  [{ann_idx}] 建立時間: {created_str}")
            
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
