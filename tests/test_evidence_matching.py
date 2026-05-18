#!/usr/bin/env python3
"""
测试日志证据匹配功能
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from harness.skills.log_evidence_matcher import LogEvidenceMatcherSkill, TimelineBuilderSkill
from harness.skills.report import ReportGenerationSkill

# 模拟测试数据
def test_evidence_matcher():
    print("=== 测试日志证据匹配技能 ===")
    
    # 创建测试实例
    evidence_skill = LogEvidenceMatcherSkill()
    timeline_skill = TimelineBuilderSkill()
    
    # 测试数据
    test_inputs = {
        "bug_description": {
            "summary": "应用在打开主页面时崩溃",
            "keywords": ["crash"]
        },
        "critical_logs": [
            {
                "type": "crash",
                "timestamp": "11:25:32",
                "level": "E",
                "tag": "AndroidRuntime",
                "message": "FATAL EXCEPTION main java.lang.NullPointerException"
            },
            {
                "type": "app_start",
                "timestamp": "11:25:30",
                "level": "I",
                "tag": "ActivityManager",
                "message": "Start proc com.example.app"
            }
        ],
        "device_state": {}
    }
    
    # 测试证据匹配
    print("\n1. 测试 LogEvidenceMatcherSkill...")
    evidence_result = evidence_skill.execute(test_inputs)
    print(f"   成功: {evidence_result.success}")
    print(f"   消息: {evidence_result.message}")
    if evidence_result.success:
        print(f"   置信度: {evidence_result.data.get('confidence_score', 0):.0%}")
        print(f"   场景变化数: {len(evidence_result.data.get('scene_changes', []))}")
    
    # 测试时间线构建
    print("\n2. 测试 TimelineBuilderSkill...")
    timeline_inputs = {
        "log_entries": test_inputs["critical_logs"]
    }
    timeline_result = timeline_skill.execute(timeline_inputs)
    print(f"   成功: {timeline_result.success}")
    print(f"   消息: {timeline_result.message}")
    if timeline_result.success:
        print(f"   事件总数: {timeline_result.data.get('total_events', 0)}")
        print(f"   关键事件数: {len(timeline_result.data.get('critical_events', []))}")
    
    print("\n=== 测试完成 ===")
    return evidence_result, timeline_result

if __name__ == "__main__":
    test_evidence_matcher()
