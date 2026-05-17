#!/usr/bin/env python3
"""
测试高级Agent的脚本
"""
import os
import sys

sys.path.insert(0, '/workspace')

# 简化版本，直接调用技能链，避免复杂的Orchestrator问题
from harness.skills.log_extraction import LogExtractionSkill
from harness.skills.log_analysis_advanced import AdvancedLogAnalysisSkill
from harness.skills.llm_analysis import LLMAnalysisSkill
from harness.skills.report import ReportGenerationSkill

def main():
    print("="*60)
    print("Android 日志分析 - 高质量分析演示")
    print("="*60)
    
    # 测试文件
    log_path = "/workspace/test_log.txt"
    bug_desc = {
        "raw_text": "应用在打开主页面时崩溃",
        "summary": "应用启动崩溃",
        "keywords": ["crash"]
    }
    
    print(f"\n📂 日志文件: {log_path}")
    print(f"📝 Bug描述: {bug_desc['summary']}")
    
    # 步骤1: 日志提取
    print("\n🔧 步骤1: 提取和解析日志...")
    extract_skill = LogExtractionSkill()
    extract_result = extract_skill.execute({"log_path": log_path})
    
    if not extract_result.success:
        print(f"❌ 失败: {extract_result.message}")
        return
    
    print(f"✅ 成功: {extract_result.message}")
    
    # 步骤2: 高级分析
    print("\n🔬 步骤2: 高级日志分析...")
    advanced_skill = AdvancedLogAnalysisSkill()
    advanced_result = advanced_skill.execute({
        "log_path": log_path, 
        "bug_description": bug_desc
    })
    
    if not advanced_result.success:
        print(f"❌ 失败: {advanced_result.message}")
        return
    
    analysis_data = advanced_result.data
    print(f"✅ 成功: {advanced_result.message}")
    print(f"   - 崩溃: {analysis_data['crashes']}")
    print(f"   - ANR: {analysis_data['anrs']}")
    print(f"   - 关键日志: {len(analysis_data['critical_logs'])}条")
    
    # 步骤3: LLM分析
    print("\n🤖 步骤3: LLM智能分析...")
    llm_skill = LLMAnalysisSkill()
    llm_result = llm_skill.execute({
        "bug_description": bug_desc,
        "advanced_log_analysis": {"data": analysis_data}
    })
    
    if not llm_result.success:
        print(f"❌ 失败: {llm_result.message}")
    else:
        print(f"✅ 成功: {llm_result.message}")
        llm_data = llm_result.data
        print(f"   - 模型: {llm_data.get('model', 'mock')}")
    
    # 步骤4: 生成报告
    print("\n📄 步骤4: 生成分析报告...")
    report_skill = ReportGenerationSkill()
    report_result = report_skill.execute({
        "bug_description": bug_desc,
        "advanced_log_analysis": {"data": analysis_data},
        "llm_analysis": {"data": llm_result.data},
        "output_format": "all"
    })
    
    if not report_result.success:
        print(f"❌ 失败: {report_result.message}")
    else:
        print(f"✅ 成功: {report_result.message}")
        print(f"\n📂 生成的报告文件:")
        for f in report_result.data['report_files']:
            print(f"   - {f}")
    
    print("\n" + "="*60)
    print("🎉 高质量分析完成!")
    print("="*60)
    print("\n📊 主要特性:")
    print("1. 关键日志证据提取")
    print("2. 设备状态变化追踪")
    print("3. 精准问题定位")
    print("4. 有日志支撑的修复建议")
    print("5. 多格式报告输出")

if __name__ == "__main__":
    main()
