"""
OpenVikingMemorySkill - OpenViking 集成记忆系统
支持自动降级到 CaseLibrarySkill
"""
import sys
import os
import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

from harness.skills.base import BaseSkill, SkillResult
from harness.core.logging import get_logger
from harness.core.paths import PROJECT_ROOT_STR, OUTPUTS_OPENVIKING_DIR_STR

logger = get_logger(__name__)


class OpenVikingMemorySkill(BaseSkill):
    """
    OpenViking 记忆系统 Skill
    与 CaseLibrarySkill 保持相同接口，可通过 Feature Flag 切换
    
    支持通过环境变量配置嵌入模型和 VLM 模型：
    - OPENVIKING_EMBEDDING_BACKEND: 嵌入模型后端（如 volcengine）
    - OPENVIKING_EMBEDDING_API_KEY: 嵌入模型 API Key
    - OPENVIKING_EMBEDDING_MODEL: 嵌入模型名称
    - OPENVIKING_EMBEDDING_API_BASE: 嵌入模型 API 地址
    - OPENVIKING_VLM_BACKEND: VLM 后端（如 volcengine）
    - OPENVIKING_VLM_API_KEY: VLM API Key
    - OPENVIKING_VLM_MODEL: VLM 模型名称
    - OPENVIKING_VLM_API_BASE: VLM API 地址
    """

    @property
    def name(self) -> str:
        return "openviking_memory"

    def __init__(self, workspace_path: Optional[str] = None):
        self.feature_sdk = None
        self.viking_client = None
        self.is_available = False
        
        # 读取 OpenViking 配置（从环境变量）
        self.embedding_backend = os.environ.get("OPENVIKING_EMBEDDING_BACKEND", "")
        self.embedding_api_key = os.environ.get("OPENVIKING_EMBEDDING_API_KEY", "")
        self.embedding_model = os.environ.get("OPENVIKING_EMBEDDING_MODEL", "")
        self.embedding_api_base = os.environ.get("OPENVIKING_EMBEDDING_API_BASE", "")
        
        self.vlm_backend = os.environ.get("OPENVIKING_VLM_BACKEND", "")
        self.vlm_api_key = os.environ.get("OPENVIKING_VLM_API_KEY", "")
        self.vlm_model = os.environ.get("OPENVIKING_VLM_MODEL", "")
        self.vlm_api_base = os.environ.get("OPENVIKING_VLM_API_BASE", "")
        self.vlm_temperature = float(os.environ.get("OPENVIKING_VLM_TEMPERATURE", "0.1"))
        
        # 使用统一路径配置
        if workspace_path is None:
            workspace_path = OUTPUTS_OPENVIKING_DIR_STR
        self.workspace_path = workspace_path

        # 尝试初始化 OpenViking
        self._init_viking()

    def _init_viking(self):
        """
        初始化 OpenViking
        如果 OpenViking 不可用，设置标记，允许降级使用
        
        支持配置：
        - embedding: 嵌入模型（用于语义搜索）
        - vlm: 视觉语言模型（用于多模态处理）
        """
        try:
            import openviking
            from openviking import OpenViking

            # 创建工作目录
            Path(self.workspace_path).mkdir(parents=True, exist_ok=True)

            # 构建配置字典
            config = {
                "storage": {
                    "workspace": self.workspace_path
                },
                "log": {
                    "level": "INFO",
                    "output": "stdout"
                }
            }

            # 添加嵌入模型配置（如果有）
            if self.embedding_backend:
                config["embedding"] = {
                    "dense": {
                        "backend": self.embedding_backend,
                        "api_key": self.embedding_api_key,
                        "model": self.embedding_model,
                        "api_base": self.embedding_api_base,
                        "dimension": 1024,
                        "input": "multimodal"
                    }
                }
                logger.info(f"OpenViking: 使用嵌入模型 {self.embedding_model}")

            # 添加 VLM 配置（如果有）
            if self.vlm_backend:
                config["vlm"] = {
                    "backend": self.vlm_backend,
                    "api_key": self.vlm_api_key,
                    "model": self.vlm_model,
                    "api_base": self.vlm_api_base,
                    "temperature": self.vlm_temperature,
                    "max_retries": 3
                }
                logger.info(f"OpenViking: 使用 VLM 模型 {self.vlm_model}")

            # 初始化客户端（支持配置参数）
            try:
                # 尝试带配置初始化
                self.viking_client = OpenViking(path=self.workspace_path, config=config)
            except TypeError:
                # 如果 OpenViking SDK 不支持 config 参数，使用基础初始化
                self.viking_client = OpenViking(path=self.workspace_path)
                if self.embedding_backend or self.vlm_backend:
                    logger.warning("OpenViking SDK 版本不支持配置参数，跳过模型配置")
            
            self.is_available = True
            logger.info("OpenVikingMemorySkill: OpenViking 已成功初始化")

        except ImportError:
            logger.warning("OpenVikingMemorySkill: OpenViking 未安装，降级到 simple 模式")
        except Exception as e:
            logger.warning(f"OpenVikingMemorySkill: 初始化失败 ({str(e)})，降级到 simple 模式")

    def _build_uri(self, bug_type: str, case_id: str) -> str:
        """构建 Viking URI"""
        date_str = datetime.now().strftime("%Y/%m")
        return f"viking://agent/memories/cases/{bug_type}/{date_str}/{case_id}"

    def execute(self, inputs: Dict[str, Any]) -> SkillResult:
        """
        执行记忆系统操作
        与 CaseLibrarySkill 保持相同的接口
        """
        action = inputs.get("action", "search_similar")

        if not self.is_available:
            # 如果 OpenViking 不可用，返回失败信息
            return SkillResult(
                False,
                {},
                "OpenViking 不可用，请切换到 simple 模式或检查配置"
            )

        if action == "save_case":
            return self._save_case(inputs)
        elif action == "search_similar":
            return self._search_similar(inputs)
        elif action == "get_by_tag":
            return self._get_by_tag(inputs)
        elif action == "get_case":
            return self._get_case(inputs)
        elif action == "update_case":
            return self._update_case(inputs)
        elif action == "get_statistics":
            return self._get_statistics(inputs)
        else:
            return SkillResult(False, {}, f"Unknown action: {action}")

    def _save_case(self, inputs: Dict) -> SkillResult:
        """保存案例到 OpenViking"""
        try:
            case_id = inputs.get("case_id", f"case_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}")
            bug_type = inputs.get("bug_type", "unknown")
            bug_summary = inputs.get("bug_summary", "")
            l0_summary = inputs.get("l0_summary", bug_summary)
            l1_overview = inputs.get("l1_overview", {})
            root_cause = inputs.get("root_cause", "")
            tags = inputs.get("tags", [])

            # 构建完整内容
            full_content = self._format_case_content(
                bug_summary, l0_summary, l1_overview,
                root_cause, tags
            )

            # 写入到 OpenViking (分层)
            uri = self._build_uri(bug_type, case_id)

            # L0: 摘要（约100 tokens）
            self.viking_client.write(uri, content=l0_summary[:150], level="L0")

            # L1: 概览（约2000 tokens）
            l1_content = f"""Bug类型: {bug_type}
摘要: {bug_summary}
标签: {', '.join(tags) if tags else '无'}
根因: {root_cause}
关键信息: {json.dumps(l1_overview, ensure_ascii=False)}
"""
            self.viking_client.write(uri, content=l1_content, level="L1")

            # L2: 完整内容（按需加载）
            self.viking_client.write(uri, content=full_content, level="L2")

            logger.info(f"OpenViking: 案例 {case_id} 已保存到 {uri}")

            return SkillResult(
                True,
                {"case_id": case_id, "uri": uri},
                "案例已保存到 OpenViking"
            )

        except Exception as e:
            return SkillResult(
                False,
                {},
                f"保存案例失败: {str(e)}"
            )

    def _search_similar(self, inputs: Dict) -> SkillResult:
        """搜索相似案例"""
        try:
            query = inputs.get("query", "")
            bug_type = inputs.get("bug_type")
            top_k = inputs.get("top_k", 3)

            # 构建搜索路径
            search_uri = "viking://agent/memories/cases/"
            if bug_type:
                search_uri += f"{bug_type}/"

            # 搜索相似案例
            results = self.viking_client.find(
                query=query,
                path=search_uri,
                max_results=top_k,
                level="L1"  # 使用 L1 层级进行搜索
            )

            # 格式化结果
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "case_id": result.uri.split("/")[-1],
                    "content": result.content,
                    "uri": result.uri
                })

            logger.info(f"OpenViking: 找到 {len(formatted_results)} 个相似案例")

            return SkillResult(
                True,
                {
                    "results": formatted_results,
                    "mode": "openviking",
                    "count": len(formatted_results)
                },
                f"找到 {len(formatted_results)} 个相似案例"
            )

        except Exception as e:
            return SkillResult(
                False,
                {},
                f"搜索失败: {str(e)}"
            )

    def _get_by_tag(self, inputs: Dict) -> SkillResult:
        """按标签获取案例"""
        try:
            tag = inputs.get("tag", "")
            top_k = inputs.get("top_k", 10)

            # 使用 tag 作为查询词
            results = self.viking_client.find(
                query=tag,
                path="viking://agent/memories/cases/",
                max_results=top_k
            )

            formatted_results = []
            for result in results:
                formatted_results.append({
                    "case_id": result.uri.split("/")[-1],
                    "content": result.content,
                    "uri": result.uri
                })

            return SkillResult(
                True,
                {
                    "results": formatted_results,
                    "tag": tag,
                    "count": len(formatted_results)
                },
                f"找到 {len(formatted_results)} 个相关案例"
            )

        except Exception as e:
            return SkillResult(False, {}, f"按标签查询失败: {str(e)}")

    def _get_case(self, inputs: Dict) -> SkillResult:
        """获取单个案例"""
        try:
            case_id = inputs.get("case_id")
            if not case_id:
                return SkillResult(False, {}, "缺少 case_id 参数")

            # 需要构建 URI 或使用搜索
            results = self.viking_client.find(
                query=case_id,
                path="viking://agent/memories/cases/",
                max_results=1
            )

            if results:
                result = results[0]
                return SkillResult(
                    True,
                    {
                        "case_id": case_id,
                        "content": result.content,
                        "uri": result.uri
                    },
                    "案例已加载"
                )
            else:
                return SkillResult(False, {}, f"未找到案例: {case_id}")

        except Exception as e:
            return SkillResult(False, {}, f"获取案例失败: {str(e)}")

    def _update_case(self, inputs: Dict) -> SkillResult:
        """更新案例（OpenViking 是 append-only 模型）"""
        try:
            case_id = inputs.get("case_id")
            status = inputs.get("status")

            # 在 OpenViking 中，我们通过添加新的层级内容来更新
            if case_id:
                uri = f"viking://agent/memories/cases/_updates/{case_id}"
                update_content = f"更新时间: {datetime.now().isoformat()}\n状态: {status}"
                self.viking_client.write(uri, content=update_content, level="L0")

                return SkillResult(
                    True,
                    {"case_id": case_id, "status": status},
                    "案例状态已更新"
                )
            else:
                return SkillResult(False, {}, "缺少 case_id 参数")

        except Exception as e:
            return SkillResult(False, {}, f"更新案例失败: {str(e)}")

    def _get_statistics(self, inputs: Dict) -> SkillResult:
        """获取统计信息"""
        try:
            # 简单统计（可以后续优化）
            return SkillResult(
                True,
                {
                    "mode": "openviking",
                    "total_cases": -1,  # OpenViking 需要遍历计算
                    "workspace": self.workspace_path
                },
                "OpenViking 模式的完整统计需要进一步实现"
            )
        except Exception as e:
            return SkillResult(False, {}, f"获取统计失败: {str(e)}")

    def _format_case_content(
        self,
        bug_summary: str,
        l0_summary: str,
        l1_overview: dict,
        root_cause: str,
        tags: List[str]
    ) -> str:
        """格式化案例完整内容"""
        return f"""# 案例分析

## 摘要
{bug_summary}

## L0 摘要
{l0_summary}

## L1 概览
{json.dumps(l1_overview, indent=2, ensure_ascii=False)}

## 根因分析
{root_cause}

## 标签
{', '.join(tags) if tags else '无标签'}

## 创建时间
{datetime.now().isoformat()}
"""

