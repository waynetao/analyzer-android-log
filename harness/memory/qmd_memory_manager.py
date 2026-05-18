"""QMD 知识库管理器 - 封装 QMD 客户端，提供统一接口"""

from typing import List, Dict, Any, Optional
import requests
import json

from harness.core.logging import get_logger

logger = get_logger(__name__)

class QMDMemoryManager:
    """QMD 知识库管理器"""
    
    def __init__(self, server_url: str = "http://localhost:8000"):
        self.server_url = server_url
        self.session = requests.Session()
        self.session.timeout = 10
    
    def search(self, 
               query: str, 
               top_k: int = 5, 
               collection: str = "android_knowledge") -> List[Dict[str, Any]]:
        """
        检索知识库
        
        Args:
            query: 检索查询
            top_k: 返回结果数量
            collection: 知识集合名称
        
        Returns:
            检索结果列表，包含文档片段和相关性评分
        """
        try:
            response = self.session.post(
                f"{self.server_url}/api/search",
                json={
                    "query": query,
                    "top_k": top_k,
                    "collection": collection
                }
            )
            response.raise_for_status()
            return response.json().get("results", [])
        except requests.exceptions.RequestException as e:
            logger.warning(f"QMD search failed: {e}")
            return []
        except json.JSONDecodeError as e:
            logger.warning(f"QMD response parse failed: {e}")
            return []
    
    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """获取完整文档内容"""
        try:
            response = self.session.get(
                f"{self.server_url}/api/documents/{document_id}"
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.warning(f"QMD get_document failed: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.warning(f"QMD response parse failed: {e}")
            return None
    
    def get_collections(self) -> List[str]:
        """获取所有知识集合"""
        try:
            response = self.session.get(
                f"{self.server_url}/api/collections"
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.warning(f"QMD get_collections failed: {e}")
            return []
        except json.JSONDecodeError as e:
            logger.warning(f"QMD response parse failed: {e}")
            return []
    
    def query_by_type(self, 
                      doc_type: str, 
                      query: str = "",
                      top_k: int = 5) -> List[Dict[str, Any]]:
        """
        按文档类型检索
        
        Args:
            doc_type: 文档类型 (event_tags, anr, dumpsys, gc, sysprops)
            query: 可选的查询词
            top_k: 返回数量
        
        Returns:
            检索结果
        """
        type_mapping = {
            "event_tags": "event_log_tags",
            "anr": "anr_tombstone",
            "dumpsys": "dumpsys",
            "gc": "gc_logs",
            "sysprops": "sysprops"
        }
        
        collection = type_mapping.get(doc_type, "android_knowledge")
        return self.search(query, top_k, collection)
    
    def health_check(self) -> bool:
        """检查 QMD Server 健康状态"""
        try:
            response = self.session.get(
                f"{self.server_url}/api/health"
            )
            response.raise_for_status()
            data = response.json()
            return data.get("status") == "healthy"
        except Exception as e:
            logger.warning(f"QMD health check failed: {e}")
            return False
    
    def get_document_summary(self, document_id: str) -> Optional[str]:
        """获取文档摘要"""
        doc = self.get_document(document_id)
        if doc and "content" in doc:
            content = doc["content"]
            # 返回前500字符作为摘要
            return content[:500] + "..." if len(content) > 500 else content
        return None
