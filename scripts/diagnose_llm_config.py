"""
在本地 Windows 项目根目录运行这个脚本
诊断 LLM 配置读取问题
"""
import os
import sys

# 1. 检查当前目录
print("="*60)
print("📂 1. 检查目录")
print("="*60)
print(f"当前脚本目录: {os.path.dirname(os.path.abspath(__file__))}")
print(f"当前工作目录: {os.getcwd()}")

# 假设项目根目录是当前目录往上一级（假设脚本在 scripts 目录）
project_root = os.getcwd()
print(f"假设项目根目录: {project_root}")

# 2. 检查 .env 文件
print("\n" + "="*60)
print("📄 2. 检查 .env 文件")
print("="*60)
env_file = os.path.join(project_root, ".env")
print(f"检查的路径: {env_file}")

if os.path.exists(env_file):
    print("✅ .env 文件存在！")

    # 读取并打印 .env 内容（脱敏）
    print("\n📝 .env 文件内容:")
    print("-"*40)
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                if 'API_KEY' in line or 'password' in line.lower():
                    key = line.split('=')[0]
                    print(f"{key}=********")
                else:
                    print(line)
    print("-"*40)

    # 尝试加载
    print("\n📥 尝试加载 .env...")
    try:
        from dotenv import load_dotenv
        result = load_dotenv(env_file, override=True)
        print(f"load_dotenv 返回: {result}")

        # 检查环境变量
        print("\n🔍 3. 检查环境变量")
        print("="*60)
        print(f"LLM_API_KEY: {'✓ 已配置' if os.environ.get('LLM_API_KEY') else '✗ 未配置'}")
        print(f"LLM_BASE_URL: {os.environ.get('LLM_BASE_URL', '未设置')}")
        print(f"LLM_MODEL: {os.environ.get('LLM_MODEL', '未设置')}")
        print(f"LLM_ANALYSIS_MODEL: {os.environ.get('LLM_ANALYSIS_MODEL', '未设置')}")
        print(f"OPENAI_API_KEY: {'✓ 已配置' if os.environ.get('OPENAI_API_KEY') else '✗ 未配置'}")
        print(f"OPENAI_MODEL: {os.environ.get('OPENAI_MODEL', '未设置')}")

        # 测试 LLM 技能的读取逻辑
        print("\n🧪 4. 测试 LLM 技能配置读取")
        print("="*60)

        scene = "analysis"
        model = os.environ.get(f"LLM_{scene.upper()}_MODEL") \
            or os.environ.get("LLM_MODEL") \
            or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

        print(f"LLM_{scene.upper()}_MODEL: {os.environ.get(f'LLM_{scene.upper()}_MODEL', '未设置')}")
        print(f"LLM_MODEL: {os.environ.get('LLM_MODEL', '未设置')}")
        print(f"最终使用的模型: {model}")

        print("\n✅ 完成！")
        print(f"  如果最终使用的模型不是你想要的，请检查:")
        print(f"  1. .env 文件中是否正确配置了 LLM_MODEL 或 LLM_ANALYSIS_MODEL")
        print(f"  2. .env 文件是否在项目根目录")
        print(f"  3. 配置的格式是否正确（不要有多余空格）")

    except Exception as e:
        print(f"❌ 加载失败: {e}")
        import traceback
        print(traceback.format_exc())
else:
    print("❌ .env 文件不存在！")
    print(f"  当前查找位置: {env_file}")
    print(f"  请确认:")
    print(f"  1. 你是否在项目根目录下运行此脚本？")
    print(f"  2. 是否有 .env 文件？")

    # 列出当前目录的文件
    print("\n📁 当前目录文件:")
    for item in os.listdir(project_root):
        print(f"  {item}")
