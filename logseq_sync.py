"""
Logseq Sync - 封裝 Logseq API 操作
"""
import os
import requests
from typing import Any
from pathlib import Path

# 載入 .env 檔案
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / ".env"
    load_dotenv(dotenv_path=env_path)
except ImportError:
    # 如果沒有安裝 python-dotenv，就跳過
    pass


class LogseqClient:
    """Logseq API Client"""
    
    def __init__(self, url: str | None = None, token: str | None = None):
        self.url = url or os.environ.get("LOGSEQ_URL", "http://127.0.0.1:12315/api")
        self.token = token or os.environ.get("LOGSEQ_TOKEN", "")
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}"
        }
    
    def call(self, method: str, *args) -> Any | None:
        """呼叫 Logseq API"""
        payload = {
            "method": method,
            "args": list(args)
        }
        try:
            response = requests.post(self.url, headers=self.headers, json=payload, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError:
            print("❌ 無法連接 Logseq API，請確認 Logseq 已啟動且 API 已開啟")
            return None
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                print("❌ Logseq API 認證失敗，請確認 LOGSEQ_TOKEN 環境變數")
            else:
                print(f"❌ Logseq API 錯誤: {e}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"❌ Logseq API 請求失敗: {e}")
            return None
    
    def check_connection(self) -> bool:
        """檢查 API 連線"""
        result = self.call("logseq.App.getInfo")
        if result:
            print(f"✅ 已連接 Logseq")
            return True
        return False
    
    def get_page(self, page_name: str) -> dict | None:
        """取得 page 資訊"""
        return self.call("logseq.Editor.getPage", page_name)
    
    def create_page(self, page_name: str, properties: dict | None = None) -> dict | None:
        """建立新 page"""
        return self.call(
            "logseq.Editor.createPage",
            page_name,
            properties or {},
            {"createFirstBlock": False}
        )
    
    def get_page_blocks(self, page_name: str) -> list | None:
        """取得 page 的所有 blocks"""
        return self.call("logseq.Editor.getPageBlocksTree", page_name)
    
    def delete_block(self, block_uuid: str) -> bool:
        """刪除 block"""
        result = self.call("logseq.Editor.removeBlock", block_uuid)
        return result is not None
    
    def insert_block(self, page_name: str, content: str, properties: dict | None = None) -> dict | None:
        """在 page 插入 block"""
        # 先取得 page
        page = self.get_page(page_name)
        if not page:
            return None
        
        return self.call(
            "logseq.Editor.insertBlock",
            page.get("uuid"),
            content,
            {"properties": properties} if properties else {}
        )
    
    def insert_batch_block(self, parent_uuid: str, batch_blocks: list[dict]) -> dict | None:
        """
        批量插入 blocks，支援嵌套子區塊
        
        Args:
            parent_uuid: 父 block 或 page 的 uuid
            batch_blocks: IBatchBlock 列表，格式如 [{"content": "...", "children": [...]}]
            
        Returns:
            建立的 block 資訊
        """
        return self.call(
            "logseq.Editor.insertBatchBlock",
            parent_uuid,
            batch_blocks,
            {"sibling": True}
        )
    
    def update_page_content(self, page_name: str, content: str) -> bool:
        """
        更新 page 內容（覆寫）
        
        支援使用 tab 縮排建立子區塊
        """
        # 確保 page 存在
        page = self.get_page(page_name)
        if not page:
            page = self.create_page(page_name)
            if not page:
                print(f"❌ 無法建立 page: {page_name}")
                return False
        
        # 刪除現有 blocks
        blocks = self.get_page_blocks(page_name)
        if blocks:
            for block in blocks:
                if block.get("uuid"):
                    self.delete_block(block["uuid"])
        
        # 解析內容為 batch blocks 結構
        batch_blocks = self._parse_content_to_blocks(content)
        
        if batch_blocks:
            # 使用 insertBatchBlock 批量插入
            self.insert_batch_block(page.get("uuid"), batch_blocks)
        
        return True
    
    def _parse_content_to_blocks(self, content: str) -> list[dict]:
        """
        解析 markdown 內容為 IBatchBlock 結構
        
        支援多層級縮排 (Tab 或 2空格)
        """
        lines = content.strip().split("\n")
        root_blocks = []
        # stack 儲存 (indent_level, block_reference)
        # 用來追蹤當前的父層級
        stack = [] 
        
        for line in lines:
            # 計算縮排層級
            indent_level = 0
            leading_ws = line[:len(line) - len(line.lstrip())]
            
            if "\t" in leading_ws:
                indent_level = leading_ws.count("\t")
            else:
                indent_level = len(leading_ws) // 2
            
            # DEBUG: comments out after fix
            # print(f"DEBUG: Line='{leading_ws}{line.lstrip()[:20]}...', Level={indent_level}, StackLen={len(stack)}")
            
            stripped = line.lstrip()
            
            # 移除 "- " 前綴
            if stripped.startswith("- "):
                stripped = stripped[2:]
            
            if not stripped.strip():
                continue
            
            new_block = {"content": stripped, "children": []}
            
            if indent_level == 0:
                # 頂層 block
                root_blocks.append(new_block)
                # 重置 stack，只保留這一個頂層
                stack = [(0, new_block)]
            else:
                # 尋找正確的父層級
                # 當 stack 頂端的層級 >= 目前層級，表示要往回找父層
                while stack and stack[-1][0] >= indent_level:
                    stack.pop()
                
                if stack:
                    # 找到父層，加入 children
                    parent_block = stack[-1][1]
                    parent_block["children"].append(new_block)
                    # 將自己推入 stack，因為自己可能是下一層的父層
                    stack.append((indent_level, new_block))
                else:
                    # 異常狀況：有縮排但找不到父層，視為頂層處理
                    root_blocks.append(new_block)
                    stack = [(indent_level, new_block)]
        
        # 遞迴清理空的 children (Logseq API prefer undefined/missing children over empty list sometimes, but empty list works too. 
        # API verification showed empty children list is fine, but cleaning up is cleaner structure)
        self._cleanup_empty_children(root_blocks)
        
        return root_blocks

    def _cleanup_empty_children(self, blocks: list[dict]) -> None:
        """遞迴清理空的 children 欄位"""
        for block in blocks:
            if "children" in block:
                if not block["children"]:
                    del block["children"]
                else:
                    self._cleanup_empty_children(block["children"])


def sync_book_to_logseq(client: LogseqClient, page_name: str, content: str) -> bool:
    """
    同步書籍到 Logseq
    
    Args:
        client: Logseq client
        page_name: Page 名稱
        content: Page 內容
        
    Returns:
        是否成功
    """
    print(f"📖 同步書籍: {page_name}")
    
    if client.update_page_content(page_name, content):
        print(f"  ✅ 同步成功")
        return True
    else:
        print(f"  ❌ 同步失敗")
        return False
