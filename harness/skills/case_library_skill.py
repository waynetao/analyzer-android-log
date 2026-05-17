"""
CaseLibrarySkill - 轻量级案例库 Skill (MVP)
使用本地 JSON 文件存储，无需外部依赖
"""
import sys
import os
import json
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

sys.path.insert(0, '/workspace')

from harness.skills.base import BaseSkill, SkillResult
from harness.core.feature_flags import FeatureSDK


class CaseLibrarySkill(BaseSkill):
    """轻量级案例库 Skill (MVP)
    
    使用本地 JSON 文件存储案例，支持：
    - 案例保存 (save_case)
    - 相似案例检索 (search_similar)
    - 按标签查询 (get_by_tag)
    """
    
    @property
    def name(self) -> str:
        return "case_library"
    
    def __init__(self, library_path: str = "/workspace/case_library"):
        self.feature_sdk = FeatureSDK()
        self.library_path = Path(library_path)
        self._ensure_directory_structure()
    
    def _ensure_directory_structure(self):
        """确保目录结构存在"""
        cases_dir = self.library_path / "cases"
        tags_dir = self.library_path / "tags"
        
        cases_dir.mkdir(parents=True, exist_ok=True)
        tags_dir.mkdir(parents=True, exist_ok=True)
        
        index_file = self.library_path / "index.json"
        if not index_file.exists():
            index_file.write_text(json.dumps({"cases": {}}, ensure_ascii=False))
        
        metadata_file = self.library_path / "metadata.json"
        if not metadata_file.exists():
            metadata_file.write_text(json.dumps({
                "created_at": datetime.now().isoformat(),
                "total_cases": 0,
                "last_updated": None
            }, ensure_ascii=False))
    
    def execute(self, inputs: Dict[str, Any]) -> SkillResult:
        """
        根据 action 执行不同操作：
        - save_case: 保存新案例
        - search_similar: 搜索相似案例
        - get_by_tag: 按标签获取案例
        - get_case: 获取单个案例
        - update_case: 更新案例
        - get_statistics: 获取统计信息
        """
        action = inputs.get("action", "search_similar")
        
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
    
    def _generate_case_id(self) -> str:
        """生成唯一案例ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        short_uuid = uuid.uuid4().hex[:8]
        return f"case_{timestamp}_{short_uuid}"
    
    def _load_index(self) -> Dict:
        """加载索引文件"""
        index_file = self.library_path / "index.json"
        try:
            with open(index_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {"cases": {}}
    
    def _save_index(self, index: Dict):
        """保存索引文件"""
        index_file = self.library_path / "index.json"
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2, ensure_ascii=False)
    
    def _update_metadata(self, delta: int = 0):
        """更新元数据"""
        metadata_file = self.library_path / "metadata.json"
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            metadata = {"created_at": datetime.now().isoformat(), "total_cases": 0}
        
        metadata["total_cases"] = metadata.get("total_cases", 0) + delta
        metadata["last_updated"] = datetime.now().isoformat()
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    def _save_case(self, inputs: Dict) -> SkillResult:
        """保存案例"""
        try:
            case_id = self._generate_case_id()
            now = datetime.now().isoformat()
            
            case_data = {
                "case_id": case_id,
                "created_at": now,
                "updated_at": now,
                
                "bug_description": {
                    "summary": inputs.get("bug_summary", ""),
                    "keywords": inputs.get("keywords", [])
                },
                
                "l0_summary": inputs.get("l0_summary", ""),
                
                "l1_overview": inputs.get("l1_overview", {}),
                
                "analysis": {
                    "bug_type": inputs.get("bug_type", "unknown"),
                    "root_cause": inputs.get("root_cause", ""),
                    "fix_suggestion": inputs.get("fix_suggestion", ""),
                    "confidence": inputs.get("confidence", 0.0)
                },
                
                "tags": inputs.get("tags", []),
                
                "metadata": {
                    "device": inputs.get("device", ""),
                    "android_version": inputs.get("android_version", ""),
                    "analyzer_version": "1.0.0"
                },
                
                "status": "active",
                "validation_count": 0,
                "success_count": 0,
                "failure_count": 0
            }
            
            case_path = self.library_path / "cases" / case_id
            with open(case_path, 'w', encoding='utf-8') as f:
                json.dump(case_data, f, indent=2, ensure_ascii=False)
            
            self._update_index(case_data)
            self._update_tags(case_data)
            self._update_metadata(delta=1)
            
            print(f"✅ 案例已保存: {case_id}")
            
            return SkillResult(True, {"case_id": case_id}, "案例已保存")
            
        except Exception as e:
            return SkillResult(False, {}, f"保存案例失败: {str(e)}")
    
    def _update_index(self, case_data: Dict):
        """更新索引"""
        index = self._load_index()
        
        case_id = case_data["case_id"]
        index["cases"][case_id] = {
            "bug_type": case_data["analysis"]["bug_type"],
            "tags": case_data["tags"],
            "keywords": case_data["bug_description"]["keywords"],
            "created_at": case_data["created_at"],
            "device": case_data["metadata"]["device"],
            "android_version": case_data["metadata"]["android_version"],
            "status": case_data["status"]
        }
        
        self._save_index(index)
    
    def _update_tags(self, case_data: Dict):
        """更新标签索引"""
        tags_dir = self.library_path / "tags"
        
        for tag in case_data["tags"]:
            tag_file = tags_dir / f"{tag}.json"
            
            try:
                if tag_file.exists():
                    with open(tag_file, 'r', encoding='utf-8') as f:
                        tag_data = json.load(f)
                else:
                    tag_data = {"cases": []}
            except json.JSONDecodeError:
                tag_data = {"cases": []}
            
            if case_data["case_id"] not in tag_data["cases"]:
                tag_data["cases"].append(case_data["case_id"])
            
            with open(tag_file, 'w', encoding='utf-8') as f:
                json.dump(tag_data, f, indent=2, ensure_ascii=False)
    
    def _search_similar(self, inputs: Dict) -> SkillResult:
        """搜索相似案例"""
        try:
            query = inputs.get("query", "")
            bug_type = inputs.get("bug_type")
            top_k = inputs.get("top_k", 3)
            
            results = self._simple_search(query, bug_type, top_k)
            
            print(f"🔍 找到 {len(results)} 个相似案例")
            
            return SkillResult(True, {
                "results": results,
                "mode": "simple",
                "count": len(results)
            }, f"找到 {len(results)} 个相似案例")
            
        except Exception as e:
            return SkillResult(False, {}, f"搜索失败: {str(e)}")
    
    def _simple_search(self, query: str, bug_type: Optional[str], top_k: int) -> List[Dict]:
        """
        简单搜索算法 (MVP阶段)
        后续可升级为向量检索
        """
        index = self._load_index()
        scores = []
        
        query_lower = query.lower()
        query_keywords = set(query_lower.split())
        
        for case_id, case_meta in index.get("cases", {}).items():
            if case_meta.get("status") != "active":
                continue
            
            score = 0
            
            if bug_type and case_meta.get("bug_type") == bug_type:
                score += 5
            
            case_tags = set(tag.lower() for tag in case_meta.get("tags", []))
            overlap = query_keywords & case_tags
            score += len(overlap) * 2
            
            case_keywords = set(keyword.lower() for keyword in case_meta.get("keywords", []))
            overlap = query_keywords & case_keywords
            score += len(overlap)
            
            if query_lower in str(case_meta.get("keywords", [])):
                score += 3
            
            if score > 0:
                scores.append((score, case_id))
        
        scores.sort(reverse=True)
        top_results = []
        
        for _, case_id in scores[:top_k]:
            case = self._load_case(case_id)
            if case:
                top_results.append(case)
        
        return top_results
    
    def _load_case(self, case_id: str) -> Optional[Dict]:
        """加载单个案例"""
        case_path = self.library_path / "cases" / case_id
        if case_path.exists():
            with open(case_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def _get_by_tag(self, inputs: Dict) -> SkillResult:
        """按标签获取案例"""
        try:
            tag = inputs.get("tag", "")
            top_k = inputs.get("top_k", 10)
            
            tag_file = self.library_path / "tags" / f"{tag}.json"
            
            if not tag_file.exists():
                return SkillResult(True, {
                    "results": [],
                    "count": 0,
                    "tag": tag
                }, f"未找到标签: {tag}")
            
            with open(tag_file, 'r', encoding='utf-8') as f:
                tag_data = json.load(f)
            
            case_ids = tag_data.get("cases", [])[:top_k]
            results = []
            
            for case_id in case_ids:
                case = self._load_case(case_id)
                if case:
                    results.append(case)
            
            return SkillResult(True, {
                "results": results,
                "tag": tag,
                "count": len(results)
            }, f"找到 {len(results)} 个案例")
            
        except Exception as e:
            return SkillResult(False, {}, f"查询失败: {str(e)}")
    
    def _get_case(self, inputs: Dict) -> SkillResult:
        """获取单个案例"""
        try:
            case_id = inputs.get("case_id")
            
            if not case_id:
                return SkillResult(False, {}, "缺少 case_id 参数")
            
            case = self._load_case(case_id)
            
            if not case:
                return SkillResult(False, {}, f"未找到案例: {case_id}")
            
            return SkillResult(True, case, "案例已加载")
            
        except Exception as e:
            return SkillResult(False, {}, f"获取案例失败: {str(e)}")
    
    def _update_case(self, inputs: Dict) -> SkillResult:
        """更新案例"""
        try:
            case_id = inputs.get("case_id")
            
            if not case_id:
                return SkillResult(False, {}, "缺少 case_id 参数")
            
            case = self._load_case(case_id)
            
            if not case:
                return SkillResult(False, {}, f"未找到案例: {case_id}")
            
            if "status" in inputs:
                case["status"] = inputs["status"]
            if "validation_count" in inputs:
                case["validation_count"] = inputs["validation_count"]
            if "success_count" in inputs:
                case["success_count"] = inputs["success_count"]
            if "failure_count" in inputs:
                case["failure_count"] = inputs["failure_count"]
            
            case["updated_at"] = datetime.now().isoformat()
            
            case_path = self.library_path / "cases" / case_id
            with open(case_path, 'w', encoding='utf-8') as f:
                json.dump(case, f, indent=2, ensure_ascii=False)
            
            return SkillResult(True, case, "案例已更新")
            
        except Exception as e:
            return SkillResult(False, {}, f"更新案例失败: {str(e)}")
    
    def _get_statistics(self, inputs: Dict) -> SkillResult:
        """获取统计信息"""
        try:
            metadata_file = self.library_path / "metadata.json"
            
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            index = self._load_index()
            
            bug_type_counts = {}
            tag_counts = {}
            
            for case_id, case_meta in index.get("cases", {}).items():
                bug_type = case_meta.get("bug_type", "unknown")
                bug_type_counts[bug_type] = bug_type_counts.get(bug_type, 0) + 1
                
                for tag in case_meta.get("tags", []):
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
            
            return SkillResult(True, {
                "total_cases": metadata.get("total_cases", 0),
                "bug_type_distribution": bug_type_counts,
                "top_tags": sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10],
                "last_updated": metadata.get("last_updated")
            }, "统计信息已加载")
            
        except Exception as e:
            return SkillResult(False, {}, f"获取统计失败: {str(e)}")
