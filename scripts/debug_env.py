import os
import sys

# 检查项目根目录
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)

print(f"📂 项目根目录: {project_root}")
print(f"📂 当前工作目录: {os.getcwd()}")

# 检查 .env 文件
env_file = os.path.join(project_root, ".env")
print(f"\n📄 检查 .env 文件: {env_file}")

if os.path.exists(env_file):
    print(f"✅ .env 文件存在")

    # 尝试加载
    try:
        from dotenv import load_dotenv
        result = load_dotenv(env_file)
        print(f"📥 load_dotenv 返回: {result}")

        # 打印关键环境变量
        print(f"\n🔍 环境变量检查:")
        print(f"LLM_API_KEY: {'✓ 已配置' if os.environ.get('LLM_API_KEY') else '✗ 未配置'}")
        print(f"LLM_MODEL: {os.environ.get('LLM_MODEL', '未设置')}")
        print(f"LLM_BASE_URL: {os.environ.get('LLM_BASE_URL', '未设置')}")
        print(f"LLM_ANALYSIS_MODEL: {os.environ.get('LLM_ANALYSIS_MODEL', '未设置')}")
        print(f"OPENAI_API_KEY: {'✓ 已配置' if os.environ.get('OPENAI_API_KEY') else '✗ 未配置'}")
        print(f"OPENAI_MODEL: {os.environ.get('OPENAI_MODEL', '未设置')}")

        # 尝试读取配置文件内容（脱敏）
        print(f"\n📝 .env 文件内容预览:")
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if 'API_KEY' in line or 'password' in line.lower():
                        print(f"  {line.split('=')[0]}=********")
                    else:
                        print(f"  {line}")
    except Exception as e:
        print(f"❌ 加载失败: {e}")
        import traceback
        print(traceback.format_exc())
else:
    print(f"❌ .env 文件不存在")
