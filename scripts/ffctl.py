#!/usr/bin/env python3
"""Feature Flag 管理工具 - 参考 Harness FME 设计"""

import argparse
import yaml
import os
import sys
sys.path.insert(0, '/workspace')

from harness.core.feature_flags import FeatureSDK, FeatureFlag

def load_flags():
    """加载所有 flags"""
    sdk = FeatureSDK()
    return sdk.get_all_flags()

def list_flags(args):
    """列出所有 flags"""
    flags = load_flags()
    
    print("=" * 70)
    print("Feature Flags 列表")
    print("=" * 70)
    
    if not flags:
        print("  暂无 Feature Flags")
        return
    
    # 按名称排序
    sorted_flags = sorted(flags.values(), key=lambda x: x.name)
    
    for flag in sorted_flags:
        status = "✅" if flag.enabled else "❌"
        print(f"\n{status} {flag.name}")
        print(f"   描述: {flag.description}")
        print(f"   类型: {flag.flag_type}")
        print(f"   环境: {', '.join(flag.environments)}")
        print(f"   灰度: {flag.percentage_rollout}%")
        
        if flag.flag_type == "multivariate":
            print(f"   默认值: {flag.default_value}")
            print(f"   变体:")
            for name, variant in flag.variants.items():
                print(f"     - {name}: {variant.get('description', '')}")

def show_flag(args):
    """显示单个 flag 详情"""
    sdk = FeatureSDK()
    flag = sdk.get_flag(args.name)
    
    if not flag:
        print(f"❌ 错误: Flag '{args.name}' 不存在")
        sys.exit(1)
    
    print("=" * 70)
    print(f"Feature Flag: {flag.name}")
    print("=" * 70)
    print(f"描述:    {flag.description}")
    print(f"类型:    {flag.flag_type}")
    print(f"状态:    {'启用' if flag.enabled else '禁用'}")
    print(f"环境:    {', '.join(flag.environments)}")
    print(f"灰度:    {flag.percentage_rollout}%")
    print(f"默认值:  {flag.default_value}")
    print(f"创建时间: {flag.created_at}")
    print(f"更新时间: {flag.updated_at}")
    
    if flag.variants:
        print("\n变体配置:")
        for name, variant in flag.variants.items():
            print(f"  {name}:")
            print(f"    描述: {variant.get('description', '')}")
            print(f"    值:   {variant.get('value', '')}")
    
    if flag.targeting_rules:
        print("\n目标规则:")
        for i, rule in enumerate(flag.targeting_rules, 1):
            print(f"  规则 {i}: {rule}")

def set_flag(args):
    """设置 Flag 状态"""
    sdk = FeatureSDK()
    
    if not sdk.get_flag(args.name):
        print(f"❌ 错误: Flag '{args.name}' 不存在")
        sys.exit(1)
    
    updates = {}
    if args.enable is not None:
        updates['enabled'] = args.enable
    
    if args.percentage is not None:
        if args.percentage < 0 or args.percentage > 100:
            print("❌ 错误: 灰度百分比必须在 0-100 之间")
            sys.exit(1)
        updates['percentage_rollout'] = args.percentage
    
    if args.default_value is not None:
        updates['default_value'] = args.default_value
    
    if updates:
        sdk.update_flag(args.name, **updates)
        print(f"✅ Flag '{args.name}' 已更新")
    else:
        print("⚠️ 未指定任何更新参数")

def create_flag(args):
    """创建新 Flag"""
    sdk = FeatureSDK()
    
    if sdk.get_flag(args.name):
        print(f"❌ 错误: Flag '{args.name}' 已存在")
        sys.exit(1)
    
    # 解析变体配置（如果提供）
    variants = {}
    if args.variants:
        for v in args.variants:
            parts = v.split('=')
            if len(parts) == 2:
                name, value = parts[0], parts[1]
                variants[name] = {"description": name, "value": value}
    
    # 解析环境列表
    environments = args.environments.split(',') if args.environments else ["dev", "prod"]
    
    flag = FeatureFlag(
        name=args.name,
        description=args.description,
        flag_type=args.type,
        enabled=args.enable,
        variants=variants,
        percentage_rollout=args.percentage,
        environments=environments,
        default_value=args.default_value
    )
    
    sdk.engine.add_flag(flag)
    print(f"✅ Flag '{args.name}' 已创建")

def delete_flag(args):
    """删除 Flag"""
    sdk = FeatureSDK()
    
    if not sdk.get_flag(args.name):
        print(f"❌ 错误: Flag '{args.name}' 不存在")
        sys.exit(1)
    
    sdk.engine.remove_flag(args.name)
    print(f"✅ Flag '{args.name}' 已删除")

def evaluate_flag(args):
    """测试 Flag 求值"""
    sdk = FeatureSDK()
    
    # 构建上下文
    context = {}
    if args.user_id:
        context['user_id'] = args.user_id
    if args.environment:
        context['environment'] = args.environment
    
    value = sdk.get_variant(args.name, context)
    enabled = sdk.is_enabled(args.name, context)
    
    print(f"Flag '{args.name}' 求值结果:")
    print(f"  值:     {value}")
    print(f"  启用:   {enabled}")
    print(f"  上下文: {context}")

def main():
    parser = argparse.ArgumentParser(
        description="Feature Flag 管理工具 - 参考 Harness FME 设计",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # list 命令
    subparsers.add_parser('list', help='列出所有 flags')
    
    # show 命令
    show_parser = subparsers.add_parser('show', help='显示单个 flag 详情')
    show_parser.add_argument('name', help='flag 名称')
    
    # set 命令
    set_parser = subparsers.add_parser('set', help='设置 flag 属性')
    set_parser.add_argument('name', help='flag 名称')
    set_parser.add_argument('--enable', action='store_true', default=None, help='启用 flag')
    set_parser.add_argument('--disable', dest='enable', action='store_false', help='禁用 flag')
    set_parser.add_argument('--percentage', type=int, help='灰度百分比 (0-100)')
    set_parser.add_argument('--default-value', help='默认值')
    
    # create 命令
    create_parser = subparsers.add_parser('create', help='创建新 flag')
    create_parser.add_argument('name', help='flag 名称')
    create_parser.add_argument('--description', required=True, help='描述')
    create_parser.add_argument('--type', choices=['boolean', 'multivariate'], default='boolean', help='类型')
    create_parser.add_argument('--enable', action='store_true', default=True, help='启用')
    create_parser.add_argument('--disable', dest='enable', action='store_false', help='禁用')
    create_parser.add_argument('--percentage', type=int, default=100, help='灰度百分比')
    create_parser.add_argument('--environments', default='dev,prod', help='环境列表，逗号分隔')
    create_parser.add_argument('--default-value', help='默认值')
    create_parser.add_argument('--variant', dest='variants', action='append', help='变体配置（格式: name=value）')
    
    # delete 命令
    delete_parser = subparsers.add_parser('delete', help='删除 flag')
    delete_parser.add_argument('name', help='flag 名称')
    
    # evaluate 命令
    eval_parser = subparsers.add_parser('evaluate', help='测试 flag 求值')
    eval_parser.add_argument('name', help='flag 名称')
    eval_parser.add_argument('--user-id', help='用户 ID（用于灰度计算）')
    eval_parser.add_argument('--environment', help='环境')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        if args.command == 'list':
            list_flags(args)
        elif args.command == 'show':
            show_flag(args)
        elif args.command == 'set':
            set_flag(args)
        elif args.command == 'create':
            create_flag(args)
        elif args.command == 'delete':
            delete_flag(args)
        elif args.command == 'evaluate':
            evaluate_flag(args)
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
