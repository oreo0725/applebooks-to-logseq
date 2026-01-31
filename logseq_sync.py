"""
Logseq Sync - Encapsulate Logseq API operations
"""
import os
import requests
from typing import Any
from pathlib import Path

try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / ".env"
    load_dotenv(dotenv_path=env_path)
except ImportError:
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
        """Call Logseq API"""
        payload = {
            "method": method,
            "args": list(args)
        }
        try:
            response = requests.post(self.url, headers=self.headers, json=payload, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError:
            print("❌ Unable to connect to Logseq API. Please ensure Logseq is running and the API is enabled.")
            return None
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                print("❌ Logseq API authentication failed. Please check your LOGSEQ_TOKEN environment variable.")
            else:
                print(f"❌ Logseq API error: {e}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"❌ Logseq API request failed: {e}")
            return None
    
    def check_connection(self) -> bool:
        """Check API connection"""
        result = self.call("logseq.App.getInfo")
        if result:
            print(f"✅ Connected to Logseq")
            return True
        return False
    
    def get_page(self, page_name: str) -> dict | None:
        """Get page info"""
        return self.call("logseq.Editor.getPage", page_name)
    
    def create_page(self, page_name: str, properties: dict | None = None) -> dict | None:
        """Create a new page"""
        return self.call(
            "logseq.Editor.createPage",
            page_name,
            properties or {},
            {"createFirstBlock": False}
        )
    
    def get_page_blocks(self, page_name: str) -> list | None:
        """Get all blocks of a page"""
        return self.call("logseq.Editor.getPageBlocksTree", page_name)
    
    def delete_block(self, block_uuid: str) -> bool:
        """Delete a block"""
        result = self.call("logseq.Editor.removeBlock", block_uuid)
        return result is not None
    
    def insert_block(self, page_name: str, content: str, properties: dict | None = None) -> dict | None:
        """Insert a block into a page"""
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
        Batch insert blocks, supporting nested sub-blocks
        
        Args:
            parent_uuid: UUID of the parent block or page
            batch_blocks: List of IBatchBlock, format like [{"content": "...", "children": [...]}]
            
        Returns:
            Created block info
        """
        return self.call(
            "logseq.Editor.insertBatchBlock",
            parent_uuid,
            batch_blocks,
            {"sibling": True}
        )
    
    def update_page_content(self, page_name: str, content: str) -> bool:
        """
        Update page content (overwrite)
        
        Supports using tab indentation for sub-blocks
        """
        page = self.get_page(page_name)
        if not page:
            page = self.create_page(page_name)
            if not page:
                print(f"❌ Unable to create page: {page_name}")
                return False
        
        blocks = self.get_page_blocks(page_name)
        if blocks:
            for block in blocks:
                if block.get("uuid"):
                    self.delete_block(block["uuid"])
        
        batch_blocks = self._parse_content_to_blocks(content)
        
        if batch_blocks:
            self.insert_batch_block(page.get("uuid"), batch_blocks)
        
        return True
    
    def _parse_content_to_blocks(self, content: str) -> list[dict]:
        """
        Parse markdown content into IBatchBlock structure
        
        Supports multi-level indentation (Tab or 2 spaces)
        """
        lines = content.strip().split("\n")
        root_blocks = []
        stack = [] 
        
        for line in lines:
            indent_level = 0
            leading_ws = line[:len(line) - len(line.lstrip())]
            
            if "\t" in leading_ws:
                indent_level = leading_ws.count("\t")
            else:
                indent_level = len(leading_ws) // 2
            
            # DEBUG: comments out after fix
            # print(f"DEBUG: Line='{leading_ws}{line.lstrip()[:20]}...', Level={indent_level}, StackLen={len(stack)}")
            
            stripped = line.lstrip()
            
            if stripped.startswith("- "):
                stripped = stripped[2:]
            
            if not stripped.strip():
                continue
            
            new_block = {"content": stripped, "children": []}
            
            if indent_level == 0:
                root_blocks.append(new_block)
                stack = [(0, new_block)]
            else:
                # When current level <= stack level, go back to find parent
                while stack and stack[-1][0] >= indent_level:
                    stack.pop()
                
                if stack:
                    # Found parent, add to children
                    parent_block = stack[-1][1]
                    parent_block["children"].append(new_block)
                    # Push self to stack as it might be a parent for the next level
                    stack.append((indent_level, new_block))
                else:
                    # Abnormal case: has indentation but no parent found, treat as root
                    root_blocks.append(new_block)
                    stack = [(indent_level, new_block)]
        
        # Cleanup empty children recursive
        self._cleanup_empty_children(root_blocks)
        
        return root_blocks

    def _cleanup_empty_children(self, blocks: list[dict]) -> None:
        """Recursively cleanup empty children fields"""
        for block in blocks:
            if "children" in block:
                if not block["children"]:
                    del block["children"]
                else:
                    self._cleanup_empty_children(block["children"])


def sync_book_to_logseq(client: LogseqClient, page_name: str, content: str) -> bool:
    """
    Sync book to Logseq
    
    Args:
        client: Logseq client
        page_name: Page name
        content: Page content
        
    Returns:
        Whether successful
    """
    print(f"📖 Syncing book: {page_name}")
    
    if client.update_page_content(page_name, content):
        print(f"  ✅ Sync success")
        return True
    else:
        print(f"  ❌ Sync failed")
        return False
