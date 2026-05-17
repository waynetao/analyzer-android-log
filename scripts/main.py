#!/usr/bin/env python3
import os
import sys
import argparse


def main():
    parser = argparse.ArgumentParser(
        description="Android 日志分析 AI Agent"
    )
    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # 分析bug命令
    analyze_parser = subparsers.add_parser('analyze', help='分析一个bug')
    analyze_parser.add_argument(
        '--bug', '-b', required=True,
        help='bug描述文件或文本'
    )
    analyze_parser.add_argument(
        '--log', '-l', required=True,
        help='日志文件/目录/压缩包路径'
    )
    analyze_parser.add_argument(
        '--output', '-o', default='bug_report.md',
        help='输出报告文件路径'
    )
    analyze_parser.add_argument(
        '--api-key', help='OpenAI API Key'
    )
    analyze_parser.add_argument(
        '--base-url', help='OpenAI API Base URL'
    )
    analyze_parser.add_argument(
        '--model', default='gpt-4o-mini',
        help='使用的模型'
    )

    # 交互式问答命令
    chat_parser = subparsers.add_parser('chat', help='交互式问答模式')
    chat_parser.add_argument(
        '--bug-id', help='已保存的Bug ID'
    )

    args = parser.parse_args()

    if args.command == 'analyze':
        # 读取bug描述
        bug_desc = ""
        if os.path.exists(args.bug):
            with open(args.bug, 'r', encoding='utf-8') as f:
                bug_desc = f.read()
        else:
            bug_desc = args.bug

        # 初始化Agent
        from log_analyzer.agent import LogAnalysisAgent
        agent = LogAnalysisAgent(
            api_key=args.api_key,
            base_url=args.base_url,
            model=args.model
        )

        # 处理bug
        agent.process_bug(
            bug_description=bug_desc,
            log_path=args.log,
            output_report=args.output
        )

        # 打印报告
        bug_info = agent.get_bug_info()
        if bug_info and bug_info.final_report:
            print("\n" + "=" * 60)
            print("分析报告预览:")
            print("=" * 60)
            print(bug_info.final_report[:2000] + "..." if len(bug_info.final_report) > 2000 else bug_info.final_report)

    elif args.command == 'chat':
        print("交互式问答模式 (输入 'quit' 退出)")
        print("=" * 60)
        
        from log_analyzer.agent import LogAnalysisAgent
        agent = LogAnalysisAgent()
        
        if args.bug_id:
            from log_analyzer.storage.storage_handler import StorageHandler
            storage = StorageHandler()
            bug_data = storage.load_bug_data(args.bug_id)
            if bug_data:
                agent.current_bug_data = bug_data
                print(f"已加载 Bug: {bug_data.bug_id}")
                print(f"摘要: {bug_data.bug_description.summary}")
        
        while True:
            try:
                question = input("\n请输入问题: ").strip()
                if question.lower() in ['quit', 'exit', 'q']:
                    break
                if not question:
                    continue
                
                answer = agent.ask_scenario_question(question)
                print("\n" + "=" * 60)
                print("回答:")
                print("=" * 60)
                print(answer)
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"错误: {e}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
