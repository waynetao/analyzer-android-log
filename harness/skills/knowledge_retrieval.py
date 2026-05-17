"""知识检索技能 - 从 QMD 知识库检索相关知识"""

from typing import Dict, Any
from .base import BaseSkill, SkillResult

class KnowledgeRetrievalSkill(BaseSkill):
    """知识检索技能 - 从 QMD 知识库检索相关知识"""
    
    @property
    def name(self) -> str:
        return "knowledge_retrieval"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "从 QMD 知识库检索 Android 日志分析相关知识，包括 Event Log Tags、ANR/Tombstone、dumpsys、GC 日志、系统属性等"
    
    @property
    def dependencies(self) -> List[str]:
        return ["qmd_memory_manager"]
    
    def execute(self, inputs: Dict[str, Any]) -> SkillResult:
        """
        执行知识检索
        
        Args:
            inputs: 包含以下字段
                - query: 检索查询词（必填）
                - doc_type: 文档类型过滤（可选）
                - top_k: 返回数量（可选，默认5）
        
        Returns:
            检索结果
        """
        # 验证输入
        valid, msg = self._validate_inputs(inputs, ["query"])
        if not valid:
            return SkillResult(False, {}, msg)
        
        # 导入依赖（延迟导入避免循环依赖）
        from harness.memory.qmd_memory_manager import QMDMemoryManager
        
        try:
            manager = QMDMemoryManager()
            
            # 获取参数
            query = inputs["query"]
            doc_type = inputs.get("doc_type", "")
            top_k = inputs.get("top_k", 5)
            
            # 执行检索
            if doc_type:
                results = manager.query_by_type(doc_type, query, top_k)
            else:
                results = manager.search(query, top_k)
            
            # 构建结果
            return SkillResult(
                success=True,
                data={
                    "results": results,
                    "query": query,
                    "doc_type": doc_type,
                    "count": len(results),
                    "knowledge_base": "android_knowledge"
                },
                message=f"检索到 {len(results)} 条相关知识"
            )
        
        except Exception as e:
            # 降级处理：返回空结果，不影响主流程
            logger = __import__('logging').getLogger(__name__)
            logger.error(f"知识检索失败: {e}")
            return SkillResult(
                success=True,
                data={
                    "results": [],
                    "query": query,
                    "doc_type": doc_type,
                    "count": 0,
                    "knowledge_base": "android_knowledge",
                    "warning": "QMD 知识库暂不可用，将使用内置知识"
                },
                message="QMD 知识库暂不可用，将使用内置知识"
            )
    
    def _validate_inputs(self, inputs: Dict[str, Any], required: List[str]) -> tuple:
        """验证输入参数"""
        for field in required:
            if field not in inputs:
                return False, f"缺少必需参数: {field}"
            if not inputs[field]:
                return False, f"参数 {field} 不能为空"
        
        # 验证 top_k
        if "top_k" in inputs:
            try:
                top_k = int(inputs["top_k"])
                if top_k <= 0:
                    return False, "top_k 必须大于0"
                if top_k > 50:
                    return False, "top_k 不能超过50"
            except ValueError:
                return False, "top_k 必须是整数"
        
        # 验证 doc_type
        valid_types = ["", "event_tags", "anr", "dumpsys", "gc", "sysprops"]
        if "doc_type" in inputs and inputs["doc_type"] not in valid_types:
            return False, f"无效的 doc_type，有效值: {', '.join(valid_types)}"
        
        return True, ""

# 为了兼容旧版本，导入 List 类型
try:
    from typing import List
except ImportError:
    pass
