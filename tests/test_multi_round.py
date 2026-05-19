"""
多轮分析功能测试
"""
import sys
sys.path.insert(0, '/workspace')

from harness.skills.multi_round_analysis import MultiRoundAnalysisSkill

# 模拟输入
bug_desc = {
    "raw_text": "应用打开主页面时崩溃",
    "summary": "应用启动崩溃"
}

log_analysis = {
    "crashes": 1,
    "anrs": 0,
    "low_memory": 2,
    "exceptions": 5,
    "critical_logs": [
        {
            "type": "crash",
            "timestamp": "11-29 11:25:32.894",
            "level": "F",
            "tag": "AndroidRuntime",
            "message": "FATAL EXCEPTION: main\njava.lang.NullPointerException: Attempt to invoke virtual method 'void android.view.View.setVisibility(int)' on a null object reference"
        }
    ]
}

# 测试多轮分析
skill = MultiRoundAnalysisSkill()
result = skill.execute({
    "bug_description": bug_desc,
    "advanced_log_analysis": log_analysis
})

if result.success:
    print("✅ 多轮分析成功！")
    print(f"分析轮数: {result.data.get('total_rounds', 0)}")
    print(f"\n第一轮分析预览:")
    rounds = result.data.get("rounds", [])
    if rounds:
        print(rounds[0]["analysis"][:500] + "...")
else:
    print(f"❌ 多轮分析失败: {result.message}")
