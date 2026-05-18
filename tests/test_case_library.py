#!/usr/bin/env python3
"""
测试 CaseLibrarySkill - MVP 记忆系统
"""
import sys
import os
import json
import tempfile
import shutil
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from harness.skills.case_library_skill import CaseLibrarySkill


def test_save_and_search():
    """测试保存和检索案例"""
    print("="*60)
    print("测试 1: 保存和检索案例")
    print("="*60)
    
    test_dir = tempfile.mkdtemp()
    try:
        skill = CaseLibrarySkill(library_path=test_dir)
        
        # 保存第一个案例 (Crash)
        save_result = skill.execute({
            "action": "save_case",
            "bug_summary": "应用启动时崩溃",
            "keywords": ["crash", "startup", "NullPointerException"],
            "l0_summary": "用户启动APP时遇到NullPointerException崩溃",
            "l1_overview": {
                "crash_count": 1,
                "exception_types": ["NullPointerException"]
            },
            "bug_type": "crash",
            "root_cause": "View 未正确初始化",
            "fix_suggestion": "添加空值检查",
            "tags": ["crash", "startup", "NullPointerException"],
            "device": "Pixel 6",
            "android_version": "12"
        })
        
        assert save_result.success, f"保存失败: {save_result.message}"
        case_id_1 = save_result.data["case_id"]
        print(f"✅ 案例1已保存: {case_id_1}")
        
        # 保存第二个案例 (ANR)
        save_result2 = skill.execute({
            "action": "save_case",
            "bug_summary": "应用无响应",
            "keywords": ["anr", "ui", "blocking"],
            "l0_summary": "用户操作时应用无响应5秒",
            "l1_overview": {
                "anr_count": 1
            },
            "bug_type": "anr",
            "root_cause": "主线程被阻塞",
            "fix_suggestion": "将耗时操作移到后台线程",
            "tags": ["anr", "ui", "blocking"],
            "device": "Pixel 6",
            "android_version": "12"
        })
        
        assert save_result2.success, f"保存失败: {save_result2.message}"
        case_id_2 = save_result2.data["case_id"]
        print(f"✅ 案例2已保存: {case_id_2}")
        
        # 测试相似案例检索 - 搜索 crash
        search_result = skill.execute({
            "action": "search_similar",
            "query": "crash startup app",
            "bug_type": "crash",
            "top_k": 5
        })
        
        assert search_result.success, f"搜索失败: {search_result.message}"
        assert search_result.data["count"] >= 1, "应该找到至少1个相似案例"
        print(f"✅ 搜索结果: 找到 {search_result.data['count']} 个相似案例")
        
        for case in search_result.data["results"]:
            print(f"   - {case['case_id']}: {case['analysis']['bug_type']}")
        
        # 测试按标签查询
        tag_result = skill.execute({
            "action": "get_by_tag",
            "tag": "crash",
            "top_k": 10
        })
        
        assert tag_result.success, f"标签查询失败: {tag_result.message}"
        print(f"✅ 标签查询: 找到 {tag_result.data['count']} 个 'crash' 标签案例")
        
        # 测试获取统计信息
        stats_result = skill.execute({
            "action": "get_statistics"
        })
        
        assert stats_result.success, f"统计查询失败: {stats_result.message}"
        print(f"✅ 统计信息: 总计 {stats_result.data['total_cases']} 个案例")
        print(f"   Bug类型分布: {stats_result.data['bug_type_distribution']}")
        
        print("\n✅ 测试 1 通过!\n")
        return True
        
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_update_case():
    """测试更新案例"""
    print("="*60)
    print("测试 2: 更新案例")
    print("="*60)
    
    test_dir = tempfile.mkdtemp()
    try:
        skill = CaseLibrarySkill(library_path=test_dir)
        
        # 保存案例
        save_result = skill.execute({
            "action": "save_case",
            "bug_summary": "测试案例",
            "keywords": ["test"],
            "bug_type": "crash",
            "tags": ["test"]
        })
        
        case_id = save_result.data["case_id"]
        
        # 更新案例状态
        update_result = skill.execute({
            "action": "update_case",
            "case_id": case_id,
            "status": "validated",
            "success_count": 1
        })
        
        assert update_result.success, f"更新失败: {update_result.message}"
        assert update_result.data["status"] == "validated"
        print(f"✅ 案例状态已更新: {update_result.data['status']}")
        
        # 获取案例验证
        get_result = skill.execute({
            "action": "get_case",
            "case_id": case_id
        })
        
        assert get_result.data["status"] == "validated"
        assert get_result.data["success_count"] == 1
        print(f"✅ 案例已正确更新")
        
        print("\n✅ 测试 2 通过!\n")
        return True
        
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_empty_search():
    """测试空搜索"""
    print("="*60)
    print("测试 3: 空搜索和边界情况")
    print("="*60)
    
    test_dir = tempfile.mkdtemp()
    try:
        skill = CaseLibrarySkill(library_path=test_dir)
        
        # 搜索不存在的案例
        search_result = skill.execute({
            "action": "search_similar",
            "query": "xyz123 nonexistent",
            "top_k": 5
        })
        
        assert search_result.success
        assert search_result.data["count"] == 0
        print(f"✅ 空搜索返回 0 结果 (符合预期)")
        
        # 获取不存在的标签
        tag_result = skill.execute({
            "action": "get_by_tag",
            "tag": "nonexistent_tag"
        })
        
        assert tag_result.success
        assert tag_result.data["count"] == 0
        print(f"✅ 不存在标签返回 0 结果 (符合预期)")
        
        # 获取不存在的案例
        get_result = skill.execute({
            "action": "get_case",
            "case_id": "nonexistent_case_id"
        })
        
        assert not get_result.success
        print(f"✅ 不存在案例返回失败 (符合预期)")
        
        print("\n✅ 测试 3 通过!\n")
        return True
        
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("CaseLibrarySkill 测试套件")
    print("="*60 + "\n")
    
    try:
        test_save_and_search()
        test_update_case()
        test_empty_search()
        
        print("="*60)
        print("🎉 所有测试通过!")
        print("="*60)
        return 0
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
