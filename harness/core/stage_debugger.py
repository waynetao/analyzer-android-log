"""
StageDebugger - 单阶段调试机制
支持独立运行每个技能阶段，查看输入输出，持久化调试数据
"""
import os
import json
import time
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from harness.core.paths import WorkflowPaths

logger = logging.getLogger(__name__)


class StageDebugger:
    """单阶段调试器
    
    功能:
    1. 独立运行指定阶段（技能）
    2. 捕获并持久化每个阶段的输入/输出到 debug/ 目录
    3. 支持加载前一阶段的输出作为当前阶段的输入
    4. 提供调试摘要，方便查看每个阶段做了什么
    5. 支持从已有 workflow 的状态加载中间数据
    
    目录结构:
    workflows/{id}/debug/
    ├── {stage_name}/
    │   ├── input.json       ← 阶段输入
    │   ├── output.json      ← 阶段输出
    │   └── summary.md       ← 人类可读的调试摘要
    └── pipeline_summary.md  ← 整体流水线摘要
    """
    
    def __init__(self, workflow_id: str = None, workflow_paths: WorkflowPaths = None):
        if workflow_paths:
            self.workflow_paths = workflow_paths
        elif workflow_id:
            self.workflow_paths = WorkflowPaths(workflow_id)
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.workflow_paths = WorkflowPaths(f"debug_{timestamp}")
        
        self.debug_dir = self.workflow_paths.debug_dir
        os.makedirs(self.debug_dir, exist_ok=True)
    
    def execute_stage(
        self,
        skill,
        inputs: Dict[str, Any],
        stage_name: str = None,
        save_debug: bool = True
    ) -> Dict[str, Any]:
        """独立执行单个阶段并保存调试数据
        
        Args:
            skill: 技能实例（必须有 execute 方法）
            inputs: 阶段输入
            stage_name: 阶段名称（默认使用 skill.name）
            save_debug: 是否保存调试数据
        
        Returns:
            包含 success/data/message/debug_info 的字典
        """
        stage_name = stage_name or getattr(skill, 'name', 'unknown')
        stage_dir = os.path.join(self.debug_dir, stage_name)
        
        start_time = time.time()
        
        try:
            result = skill.execute(inputs)
            duration_ms = (time.time() - start_time) * 1000
            
            output_data = {
                "success": result.success,
                "data": result.data,
                "message": result.message,
            }
            
            debug_info = {
                "stage_name": stage_name,
                "success": result.success,
                "duration_ms": round(duration_ms, 2),
                "timestamp": datetime.now().isoformat(),
            }
            
            if save_debug:
                os.makedirs(stage_dir, exist_ok=True)
                self._save_json(os.path.join(stage_dir, "input.json"), inputs)
                self._save_json(os.path.join(stage_dir, "output.json"), output_data)
                self._save_stage_summary(stage_dir, stage_name, inputs, output_data, debug_info)
            
            return {
                **output_data,
                "debug_info": debug_info,
            }
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            error_output = {
                "success": False,
                "data": {},
                "message": f"阶段执行异常: {str(e)}",
            }
            
            debug_info = {
                "stage_name": stage_name,
                "success": False,
                "duration_ms": round(duration_ms, 2),
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
            }
            
            if save_debug:
                os.makedirs(stage_dir, exist_ok=True)
                self._save_json(os.path.join(stage_dir, "input.json"), inputs)
                self._save_json(os.path.join(stage_dir, "output.json"), error_output)
                self._save_stage_summary(stage_dir, stage_name, inputs, error_output, debug_info)
            
            return {
                **error_output,
                "debug_info": debug_info,
            }
    
    def load_stage_output(self, stage_name: str) -> Optional[Dict[str, Any]]:
        """加载指定阶段的输出（用于阶段间数据传递）
        
        Args:
            stage_name: 阶段名称
        
        Returns:
            阶段输出数据，如果不存在返回 None
        """
        output_path = os.path.join(self.debug_dir, stage_name, "output.json")
        if os.path.exists(output_path):
            return self._load_json(output_path)
        return None
    
    def load_stage_input(self, stage_name: str) -> Optional[Dict[str, Any]]:
        """加载指定阶段的输入
        
        Args:
            stage_name: 阶段名称
        
        Returns:
            阶段输入数据，如果不存在返回 None
        """
        input_path = os.path.join(self.debug_dir, stage_name, "input.json")
        if os.path.exists(input_path):
            return self._load_json(input_path)
        return None
    
    def list_stages(self) -> List[Dict[str, Any]]:
        """列出所有已调试的阶段
        
        Returns:
            阶段信息列表，包含名称、状态、时间等
        """
        stages = []
        if not os.path.exists(self.debug_dir):
            return stages
        
        for name in sorted(os.listdir(self.debug_dir)):
            stage_dir = os.path.join(self.debug_dir, name)
            if not os.path.isdir(stage_dir):
                continue
            
            info = {"name": name}
            
            output_path = os.path.join(stage_dir, "output.json")
            if os.path.exists(output_path):
                output = self._load_json(output_path)
                if output:
                    info["success"] = output.get("success")
                    info["message"] = output.get("message", "")
            
            input_path = os.path.join(stage_dir, "input.json")
            if os.path.exists(input_path):
                info["has_input"] = True
            
            stages.append(info)
        
        return stages
    
    def get_stage_summary(self, stage_name: str) -> Optional[str]:
        """获取指定阶段的调试摘要
        
        Args:
            stage_name: 阶段名称
        
        Returns:
            Markdown 格式的摘要，如果不存在返回 None
        """
        summary_path = os.path.join(self.debug_dir, stage_name, "summary.md")
        if os.path.exists(summary_path):
            with open(summary_path, 'r', encoding='utf-8') as f:
                return f.read()
        return None
    
    def generate_pipeline_summary(self) -> str:
        """生成整体流水线调试摘要
        
        Returns:
            Markdown 格式的流水线摘要
        """
        stages = self.list_stages()
        
        lines = [
            f"# 调试流水线摘要",
            f"",
            f"- 工作流ID: {self.workflow_paths.workflow_id}",
            f"- 调试目录: {self.debug_dir}",
            f"- 阶段数量: {len(stages)}",
            f"- 生成时间: {datetime.now().isoformat()}",
            f"",
            f"## 阶段列表",
            f"",
        ]
        
        for stage in stages:
            status = "✅" if stage.get("success") else "❌"
            name = stage.get("name", "unknown")
            msg = stage.get("message", "")
            lines.append(f"### {status} {name}")
            if msg:
                lines.append(f"- 消息: {msg}")
            lines.append(f"- 有输入: {'是' if stage.get('has_input') else '否'}")
            lines.append("")
        
        summary = "\n".join(lines)
        
        summary_path = os.path.join(self.debug_dir, "pipeline_summary.md")
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(summary)
        
        return summary
    
    def _save_stage_summary(
        self,
        stage_dir: str,
        stage_name: str,
        inputs: Dict[str, Any],
        outputs: Dict[str, Any],
        debug_info: Dict[str, Any]
    ):
        """保存阶段调试摘要（人类可读的 Markdown 格式）"""
        lines = [
            f"# 阶段调试摘要: {stage_name}",
            f"",
            f"- 状态: {'✅ 成功' if outputs.get('success') else '❌ 失败'}",
            f"- 耗时: {debug_info.get('duration_ms', 0):.2f}ms",
            f"- 时间: {debug_info.get('timestamp', '')}",
            f"",
            f"## 输入概要",
            f"",
        ]
        
        input_keys = list(inputs.keys()) if isinstance(inputs, dict) else []
        lines.append(f"- 输入参数: {', '.join(input_keys)}")
        
        for key in input_keys:
            val = inputs[key]
            if isinstance(val, dict):
                sub_keys = list(val.keys())[:10]
                lines.append(f"  - `{key}`: dict with keys {sub_keys}")
            elif isinstance(val, str):
                preview = val[:100] + "..." if len(val) > 100 else val
                lines.append(f"  - `{key}`: \"{preview}\"")
            elif isinstance(val, list):
                lines.append(f"  - `{key}`: list with {len(val)} items")
            else:
                lines.append(f"  - `{key}`: {type(val).__name__}")
        
        lines.append("")
        lines.append("## 输出概要")
        lines.append("")
        
        output_data = outputs.get("data", {})
        if isinstance(output_data, dict):
            for key, val in output_data.items():
                if isinstance(val, list):
                    lines.append(f"- `{key}`: {len(val)} 条")
                elif isinstance(val, dict):
                    lines.append(f"- `{key}`: dict with keys {list(val.keys())[:5]}")
                elif isinstance(val, str):
                    preview = val[:200] + "..." if len(val) > 200 else val
                    lines.append(f"- `{key}`: \"{preview}\"")
                else:
                    lines.append(f"- `{key}`: {val}")
        else:
            lines.append(f"- 数据类型: {type(output_data).__name__}")
        
        message = outputs.get("message", "")
        if message:
            lines.append("")
            lines.append(f"## 消息")
            lines.append("")
            lines.append(message)
        
        if debug_info.get("error"):
            lines.append("")
            lines.append("## 错误详情")
            lines.append("")
            lines.append(f"```\n{debug_info['error']}\n```")
        
        summary_path = os.path.join(stage_dir, "summary.md")
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))
    
    def _save_json(self, path: str, data: Any):
        """保存 JSON 数据"""
        try:
            serializable = self._make_serializable(data)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(serializable, f, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            logger.warning(f"保存调试数据失败 {path}: {e}")
    
    def _load_json(self, path: str) -> Optional[Dict]:
        """加载 JSON 数据"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"加载调试数据失败 {path}: {e}")
            return None
    
    def _make_serializable(self, obj: Any) -> Any:
        """将对象转换为可 JSON 序列化的格式"""
        if obj is None:
            return None
        if isinstance(obj, (str, int, float, bool)):
            return obj
        if isinstance(obj, dict):
            return {str(k): self._make_serializable(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [self._make_serializable(item) for item in obj]
        if hasattr(obj, '__dict__'):
            return self._make_serializable(obj.__dict__)
        return str(obj)
