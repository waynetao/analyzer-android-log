#!/usr/bin/env python3
"""
QMD 知识库集成测试脚本
验证知识文档结构和集成代码
"""
import os
import sys
sys.path.insert(0, '/workspace')

def test_knowledge_base_structure():
    """测试知识库目录结构"""
    print("=" * 60)
    print("1. 测试知识库目录结构")
    print("=" * 60)
    
    expected_structure = {
        "knowledge_base": {
            "meta.yaml": True,
            "config": {
                "qmd_config.yaml": True
            },
            "android_knowledge": {
                "_index.md": True,
                "event_log_tags": ["_index.md", "system_tags.md", "app_tags.md"],
                "anr_tombstone": ["_index.md", "anr_format.md", "tombstone_format.md"],
                "dumpsys": ["_index.md", "meminfo_sop.md", "battery_sop.md"],
                "sysprops": ["_index.md", "critical_props.md", "debug_props.md"],
                "gc_logs": ["_index.md", "gc_types.md", "format_parsing.md"]
            }
        }
    }
    
    errors = []
    
    def check_path(base, structure, path=""):
        for name, expected in structure.items():
            full_path = os.path.join(base, path, name)
            if isinstance(expected, dict):
                if not os.path.isdir(full_path):
                    errors.append(f"缺少目录: {full_path}")
                else:
                    check_path(base, expected, os.path.join(path, name))
            elif isinstance(expected, list):
                if not os.path.isdir(full_path):
                    errors.append(f"缺少目录: {full_path}")
                else:
                    for file in expected:
                        file_path = os.path.join(base, path, name, file)
                        if not os.path.isfile(file_path):
                            errors.append(f"缺少文件: {file_path}")
            else:
                if not os.path.isfile(full_path):
                    errors.append(f"缺少文件: {full_path}")
    
    check_path("/workspace", expected_structure)
    
    if errors:
        for error in errors:
            print(f"❌ {error}")
        return False
    else:
        print("✅ 知识库目录结构完整")
        return True

def test_knowledge_retrieval_skill():
    """测试知识检索技能"""
    print("\n" + "=" * 60)
    print("2. 测试知识检索技能")
    print("=" * 60)
    
    try:
        from harness.skills.knowledge_retrieval import KnowledgeRetrievalSkill
        
        skill = KnowledgeRetrievalSkill()
        assert skill is not None
        assert skill.name == "knowledge_retrieval"
        assert hasattr(skill, 'execute')
        assert hasattr(skill, 'version')
        assert hasattr(skill, 'description')
        
        print("✅ KnowledgeRetrievalSkill 实例化正常")
        print(f"   - 版本: {skill.version}")
        print(f"   - 名称: {skill.name}")
        print(f"   - 描述: {skill.description[:50]}...")
        
        return True
    except Exception as e:
        print(f"❌ KnowledgeRetrievalSkill 测试失败: {e}")
        return False

def test_qmd_memory_manager():
    """测试 QMD 内存管理器"""
    print("\n" + "=" * 60)
    print("3. 测试 QMD 内存管理器")
    print("=" * 60)
    
    try:
        from harness.memory.qmd_memory_manager import QMDMemoryManager
        
        manager = QMDMemoryManager()
        assert manager is not None
        assert hasattr(manager, 'search')
        assert hasattr(manager, 'get_document')
        assert hasattr(manager, 'query_by_type')
        assert hasattr(manager, 'health_check')
        
        print("✅ QMDMemoryManager 实例化正常")
        print("   - search(): 支持通用检索")
        print("   - get_document(): 获取文档详情")
        print("   - query_by_type(): 按类型检索")
        print("   - health_check(): 健康检查")
        
        # 测试健康检查（QMD Server 可能未运行，预期返回 False）
        health = manager.health_check()
        if health:
            print("   ✅ QMD Server 健康检查通过")
        else:
            print("   ⚠️ QMD Server 未运行（开发环境正常）")
        
        return True
    except Exception as e:
        print(f"❌ QMDMemoryManager 测试失败: {e}")
        return False

def test_document_content():
    """测试文档内容"""
    print("\n" + "=" * 60)
    print("4. 测试文档内容")
    print("=" * 60)
    
    docs_to_check = [
        "/workspace/knowledge_base/android_knowledge/event_log_tags/system_tags.md",
        "/workspace/knowledge_base/android_knowledge/anr_tombstone/anr_format.md",
        "/workspace/knowledge_base/android_knowledge/dumpsys/meminfo_sop.md",
        "/workspace/knowledge_base/android_knowledge/sysprops/critical_props.md",
        "/workspace/knowledge_base/android_knowledge/gc_logs/format_parsing.md"
    ]
    
    all_valid = True
    for doc_path in docs_to_check:
        if os.path.exists(doc_path):
            with open(doc_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if len(content) > 500:
                    print(f"✅ {os.path.basename(doc_path)}: 内容完整 ({len(content)} 字符)")
                else:
                    print(f"⚠️ {os.path.basename(doc_path)}: 内容较少 ({len(content)} 字符)")
        else:
            print(f"❌ {os.path.basename(doc_path)}: 不存在")
            all_valid = False
    
    return all_valid

def test_agent_integration():
    """测试 Agent 集成"""
    print("\n" + "=" * 60)
    print("5. 测试 Agent 集成")
    print("=" * 60)
    
    try:
        # 检查导入
        with open('/workspace/harness_agent_advanced.py', 'r') as f:
            content = f.read()
            assert 'KnowledgeRetrievalSkill' in content
            assert 'from harness.skills.knowledge_retrieval import' in content
            assert 'self.orchestrator.register_skill(KnowledgeRetrievalSkill())' in content
        
        print("✅ KnowledgeRetrievalSkill 已注册到 Agent")
        return True
    except Exception as e:
        print(f"❌ Agent 集成测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("QMD 知识库集成测试")
    print("=" * 60)
    print()
    
    tests = [
        ("知识库结构", test_knowledge_base_structure),
        ("知识检索技能", test_knowledge_retrieval_skill),
        ("QMD内存管理器", test_qmd_memory_manager),
        ("文档内容", test_document_content),
        ("Agent集成", test_agent_integration),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"\n❌ {test_name}测试异常: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if not passed:
            all_passed = False
    
    print()
    if all_passed:
        print("🎉 所有测试通过!")
        print("✅ QMD 知识库集成方案已完成")
    else:
        print("❌ 部分测试失败，请检查")
    
    print("=" * 60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
