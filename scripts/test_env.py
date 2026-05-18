#!/usr/bin/env python3
"""
简单的 LLM 配置测试脚本
在项目根目录运行: python scripts/test_env.py
"""
import os
import sys

# 添加项目路径
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

# 加载 .env
from dotenv import load_dotenv
dotenv_path = os.path.join(project_root, ".env")
load_dotenv(dotenv_path, override=True)

print("=" * 60)
print("🔧 LLM 配置测试")
print("=" * 60)

# 检查必需配置
api_key = os.environ.get("LLM_API_KEY")
base_url = os.environ.get("LLM_BASE_URL")
model = os.environ.get("LLM_MODEL")

print(f"\n📋 当前配置:")
print(f"   LLM_API_KEY:  {'✓ 已设置' if api_key and api_key != 'your_api_key_here' else '✗ 未设置或占位符'}")
print(f"   LLM_BASE_URL: {base_url if base_url else '✗ 未设置'}")
print(f"   LLM_MODEL:    {model if model else '✗ 未设置'}")

# 验证 API Key 不是占位符
if not api_key or api_key == "your_api_key_here" or len(api_key) < 10:
    print("\n❌ API Key 未正确配置！")
    print("   请在 .env 文件中填入真实的 API Key")
    sys.exit(1)

if not model:
    print("\n❌ 模型名称未配置！")
    print("   请在 .env 文件中设置 LLM_MODEL")
    sys.exit(1)

print(f"\n✅ 配置检查通过")
print(f"\n🚀 测试 LLM 连接...")

# 测试 LLM 连接
try:
    from log_analyzer.llm.llm_client import LLMClient
    
    client = LLMClient(
        api_key=api_key,
        base_url=base_url,
        model=model
    )
    
    if client.use_mock:
        print("❌ LLM 客户端初始化失败（使用了模拟模式）")
        print(f"   API Key: {api_key[:8]}...")
        print(f"   Base URL: {base_url}")
        sys.exit(1)
    
    print(f"✅ LLM 客户端初始化成功")
    print(f"   模型: {client.model}")
    print(f"   Base URL: {client.base_url}")
    
    # 发送测试请求
    print(f"\n📤 发送测试请求...")
    response = client.chat_completion(
        system_prompt="你是一个有用的助手",
        user_prompt="你好，回复 OK 即可",
        temperature=0.1
    )
    
    print(f"✅ LLM 调用成功！")
    print(f"   回复: {response[:100]}...")
    
    print("\n" + "=" * 60)
    print("🎉 所有测试通过！LLM 配置正确")
    print("=" * 60)
    
except Exception as e:
    print(f"\n❌ LLM 调用失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
