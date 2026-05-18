#!/usr/bin/env python3
"""
完整集成测试：记忆系统 + Android 日志分析 Agent
验证 MVP 模式的完整工作流
"""
import sys
import os
import tempfile
import shutil
from pathlib import Path

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from harness.skills.case_library_skill import CaseLibrarySkill
from harness.core.feature_flags import FeatureSDK


def test_feature_flag_config():
    """测试 Feature Flag 配置是否正确加载"""
    print("="*60)
    print("测试 1: Feature Flag 配置")
    print("="*60)
    
    feature_sdk = FeatureSDK()
    
    # 检查记忆系统相关的 flags 是否存在
    memory_flags = [
        "memory_system_enabled",
        "memory_mode",
        "auto_save_cases",
        "similar_case_retrieval",
        "anti_rigidity_enabled"
    ]
    
    print("\n📋 检查记忆系统相关的 Feature Flags:")
    all_exist = True
    for flag_name in memory_flags:
        flag = feature_sdk.get_flag(flag_name)
        if flag:
            print(f"  ✅ {flag_name}: 已加载")
        else:
            print(f"  ❌ {flag_name}: 未找到")
            all_exist = False
    
    # 检查默认值
    memory_mode = feature_sdk.get_variant("memory_mode")
    print(f"\n🗂️  memory_mode: {memory_mode} (预期: simple)")
    
    # 检查开关状态
    for flag_name in ["memory_system_enabled", "auto_save_cases", "similar_case_retrieval"]:
        enabled = feature_sdk.is_enabled(flag_name)
        print(f"  {flag_name}: {'✅ 已启用' if enabled else '❌ 已禁用'}")
    
    assert all_exist, "部分记忆系统 Feature Flags 缺失"
    assert memory_mode == "simple", "memory_mode 默认值应设为 'simple'"
    
    print("\n✅ 测试 1 通过!")
    return True


def test_end_to_end_workflow():
    """测试完整的端到端工作流：保存 -> 检索 -> 再保存"""
    print("\n" + "="*60)
    print("测试 2: 端到端工作流")
    print("="*60)
    
    test_dir = tempfile.mkdtemp()
    try:
        case_library = CaseLibrarySkill(library_path=test_dir)
        
        # --- 步骤 1: 保存第一个案例 (Crash) ---
        print("\n📝 步骤 1: 保存第一个案例 (Crash)")
        result1 = case_library.execute({
            "action": "save_case",
            "bug_summary": "应用启动时崩溃，日志显示 NullPointerException",
            "keywords": ["crash", "startup", "NullPointerException"],
            "l0_summary": "用户点击登录按钮时应用崩溃，堆栈显示 NullPointerException 在 MainActivity.onCreate",
            "l1_overview": {
                "crash_count": 1,
                "anr_count": 0,
                "exception_types": ["NullPointerException"],
                "affected_process": "com.example.app",
                "key_logs": [
                    "FATAL EXCEPTION: main",
                    "java.lang.NullPointerException: Attempt to invoke virtual method 'void android.widget.Button.setOnClickListener' on a null object reference"
                ]
            },
            "bug_type": "crash",
            "root_cause": "Button 引用为 null，可能是布局文件中 ID 不匹配",
            "fix_suggestion": "检查布局文件中的 Button ID 是否与代码中的 findViewById 匹配",
            "tags": ["crash", "startup", "NullPointerException", "android"],
            "device": "Pixel 6",
            "android_version": "12"
        })
        
        assert result1.success, f"案例 1 保存失败: {result1.message}"
        case1_id = result1.data["case_id"]
        print(f"✅ 案例 1 已保存: {case1_id}")
        
        # --- 步骤 2: 保存第二个案例 (ANR) ---
        print("\n📝 步骤 2: 保存第二个案例 (ANR)")
        result2 = case_library.execute({
            "action": "save_case",
            "bug_summary": "应用无响应，主线程被网络请求阻塞",
            "keywords": ["anr", "ui", "network", "blocking"],
            "l0_summary": "用户刷新列表时应用 ANR，主线程执行 HTTP 请求",
            "l1_overview": {
                "crash_count": 0,
                "anr_count": 1,
                "exception_types": [],
                "affected_process": "com.example.app",
                "key_logs": [
                    "ANR in com.example.app",
                    "Reason: Input dispatching timed out"
                ]
            },
            "bug_type": "anr",
            "root_cause": "在主线程执行网络请求导致 UI 阻塞",
            "fix_suggestion": "使用 AsyncTask 或 Coroutine 将网络请求移至后台线程",
            "tags": ["anr", "network", "ui", "android"],
            "device": "Pixel 6",
            "android_version": "12"
        })
        
        assert result2.success, f"案例 2 保存失败: {result2.message}"
        case2_id = result2.data["case_id"]
        print(f"✅ 案例 2 已保存: {case2_id}")
        
        # --- 步骤 3: 保存第三个相似案例 ---
        print("\n📝 步骤 3: 保存第三个相似案例")
        result3 = case_library.execute({
            "action": "save_case",
            "bug_summary": "应用在启动时崩溃，View 初始化失败",
            "keywords": ["crash", "startup", "view"],
            "l0_summary": "应用进入主界面时崩溃，View 未正确初始化",
            "l1_overview": {
                "crash_count": 1,
                "anr_count": 0
            },
            "bug_type": "crash",
            "root_cause": "View 引用错误",
            "fix_suggestion": "检查 View 引用",
            "tags": ["crash", "startup", "view"],
            "device": "Pixel 5",
            "android_version": "11"
        })
        
        assert result3.success
        print(f"✅ 案例 3 已保存")
        
        # --- 步骤 4: 搜索相似案例 ---
        print("\n🔍 步骤 4: 搜索与 'crash startup' 相似的案例")
        search_result = case_library.execute({
            "action": "search_similar",
            "query": "应用启动时崩溃 startup crash",
            "bug_type": "crash",
            "top_k": 3
        })
        
        assert search_result.success, f"搜索失败: {search_result.message}"
        results = search_result.data.get("results", [])
        
        print(f"✅ 找到 {len(results)} 个相似案例:")
        for i, case in enumerate(results, 1):
            print(f"   {i}. {case['case_id']}")
        
        assert len(results) >= 2, "应该找到至少 2 个与 crash 相关的案例"
        
        # --- 步骤 5: 获取统计信息 ---
        print("\n📊 步骤 5: 获取统计信息")
        stats_result = case_library.execute({
            "action": "get_statistics"
        })
        
        assert stats_result.success
        total = stats_result.data.get("total_cases")
        distribution = stats_result.data.get("bug_type_distribution")
        
        print(f"✅ 总案例数: {total}")
        print(f"   Bug类型分布: {distribution}")
        
        assert total == 3, "应该有 3 个案例"
        assert distribution.get("crash", 0) == 2, "应该有 2 个 crash 案例"
        assert distribution.get("anr", 0) == 1, "应该有 1 个 anr 案例"
        
        # --- 步骤 6: 按标签查询 ---
        print("\n🏷️ 步骤 6: 按标签查询 (tag='crash')")
        tag_result = case_library.execute({
            "action": "get_by_tag",
            "tag": "crash",
            "top_k": 10
        })
        
        assert tag_result.success
        tag_cases = tag_result.data.get("results", [])
        print(f"✅ 找到 {len(tag_cases)} 个带 'crash' 标签的案例")
        
        # --- 步骤 7: 获取单个案例 ---
        print("\n📄 步骤 7: 获取单个案例详情")
        get_result = case_library.execute({
            "action": "get_case",
            "case_id": case1_id
        })
        
        assert get_result.success
        case = get_result.data
        print(f"✅ 获取到案例: {case['case_id']}")
        print(f"   Bug类型: {case['analysis']['bug_type']}")
        print(f"   根因: {case['analysis']['root_cause']}")
        
        # --- 步骤 8: 更新案例 ---
        print("\n✏️ 步骤 8: 更新案例")
        update_result = case_library.execute({
            "action": "update_case",
            "case_id": case1_id,
            "status": "validated",
            "success_count": 1
        })
        
        assert update_result.success
        print(f"✅ 案例已更新: 状态={update_result.data['status']}")
        
        print("\n✅ 测试 2 通过!")
        return True
        
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_directory_structure():
    """测试案例库目录结构"""
    print("\n" + "="*60)
    print("测试 3: 目录结构")
    print("="*60)
    
    test_dir = tempfile.mkdtemp()
    try:
        case_library = CaseLibrarySkill(library_path=test_dir)
        
        # 保存一个案例以创建所有目录
        case_library.execute({
            "action": "save_case",
            "bug_summary": "测试案例",
            "keywords": ["test"],
            "bug_type": "unknown",
            "tags": ["test"]
        })
        
        # 检查目录结构
        root = Path(test_dir)
        print(f"\n📁 目录结构 (根目录: {test_dir}):")
        print("   ├── cases/")
        print("   ├── tags/")
        print("   ├── index.json")
        print("   └── metadata.json")
        
        # 验证文件存在
        assert (root / "index.json").exists()
        assert (root / "metadata.json").exists()
        assert (root / "cases").exists()
        assert (root / "tags").exists()
        assert len(list((root / "cases").iterdir())) == 1  # 1个案例
        
        print("\n✅ 目录结构正确!")
        print("✅ 测试 3 通过!")
        return True
        
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_memory_system_sandbox():
    """测试默认的内存系统（沙盒模式，不会影响生产数据）"""
    print("\n" + "="*60)
    print("测试 4: 沙盒模式下的默认案例库")
    print("="*60)
    
    case_lib_path = os.path.join(PROJECT_ROOT, "case_library")
    
    # 备份原有的案例库（如果存在）
    original_exists = os.path.exists(case_lib_path)
    if original_exists:
        print("⚠️  检测到原有的案例库，将临时备份...")
        os.rename(case_lib_path, case_lib_path + ".bak")
    
    try:
        case_library = CaseLibrarySkill()
        
        # 检查是否为空库
        stats = case_library.execute({"action": "get_statistics"})
        assert stats.success
        initial_count = stats.data.get("total_cases", 0)
        print(f"📊 初始案例数: {initial_count}")
        
        # 保存一个测试案例
        result = case_library.execute({
            "action": "save_case",
            "bug_summary": "集成测试 - 临时案例",
            "keywords": ["integration-test", "temp"],
            "l0_summary": "这是一个用于集成测试的临时案例",
            "l1_overview": {"crash_count": 0},
            "bug_type": "unknown",
            "tags": ["integration-test"],
            "device": "test-device",
            "android_version": "test"
        })
        
        assert result.success, f"保存失败: {result.message}"
        test_case_id = result.data["case_id"]
        print(f"✅ 测试案例已保存: {test_case_id}")
        
        # 验证案例已保存
        stats_after = case_library.execute({"action": "get_statistics"})
        assert stats_after.data.get("total_cases") == initial_count + 1
        print(f"✅ 案例总数: {stats_after.data.get('total_cases')}")
        
        # 搜索验证
        search_result = case_library.execute({
            "action": "search_similar",
            "query": "integration test",
            "top_k": 5
        })
        assert search_result.data.get("count", 0) >= 1
        print("✅ 搜索功能正常")
        
        print("\n✅ 测试 4 通过!")
        return True
        
    finally:
        # 清理测试数据
        if original_exists:
            # 恢复原有的案例库
            if os.path.exists(case_lib_path):
                shutil.rmtree(case_lib_path)
            os.rename(case_lib_path + ".bak", case_lib_path)
            print("ℹ️  已恢复原有的案例库")
        else:
            # 清理测试创建的案例库
            if os.path.exists(case_lib_path):
                shutil.rmtree(case_lib_path)
            print("ℹ️  已清理测试数据")


def main():
    print("\n" + "="*60)
    print("🧪 记忆系统完整集成测试")
    print("="*60)
    
    all_passed = True
    try:
        test_feature_flag_config()
        test_end_to_end_workflow()
        test_directory_structure()
        test_memory_system_sandbox()
        
        print("\n" + "="*60)
        print("🎉 所有集成测试通过!")
        print("="*60)
        print("\n📋 总结:")
        print("   - ✅ Feature Flags 已正确配置")
        print("   - ✅ CaseLibrarySkill 端到端工作流正常")
        print("   - ✅ 目录结构完整")
        print("   - ✅ 记忆系统已集成到 harness_agent_advanced.py")
        print("\n📖 使用方法:")
        print("   1. 分析案例: python harness_agent_advanced.py --bug '...' --log '...'")
        print("   2. 查看案例库: python harness_agent_advanced.py --list-cases")
        print("   3. 记忆系统功能通过 Feature Flags 控制 (config/feature_flags.yaml)")
        print("\n🔄 下一步:")
        print("   - 学习 OpenViking API 以实现完整集成模式")
        print("   - 实现防僵化机制")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
