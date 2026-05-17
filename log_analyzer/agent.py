import os
from datetime import datetime
from typing import List, Optional

from log_analyzer.models import BugDescription, StandardizedBugData, ScenarioQuery
from log_analyzer.parser.log_parser import LogEntry
from log_analyzer.extractor.extractor import LogExtractor
from log_analyzer.bugreport.bugreport_parser import BugReportParser
from log_analyzer.cleaner.log_cleaner import LogCleaner
from log_analyzer.analyzer.log_analyzer import LogAnalyzer, AnalysisResult
from log_analyzer.storage.storage_handler import StorageHandler
from log_analyzer.llm.llm_client import LLMClient
from log_analyzer.llm.bug_description_parser import BugDescriptionParser
from log_analyzer.llm.report_generator import ReportGenerator
from log_analyzer.llm.scenario_analyzer import ScenarioAnalyzer


class LogAnalysisAgent:
    """Android 日志分析 AI Agent"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "gpt-4o-mini",
        storage_dir: str = "./bug_data"
    ):
        # 初始化LLM客户端
        self.llm_client = LLMClient(api_key, base_url, model)
        
        # 初始化各模块
        self.bug_parser = BugDescriptionParser(self.llm_client)
        self.report_gen = ReportGenerator(self.llm_client)
        self.scenario_analyzer = ScenarioAnalyzer(self.llm_client)
        self.storage = StorageHandler(storage_dir)
        
        # 内部状态
        self.current_bug_data: Optional[StandardizedBugData] = None
        self.all_logs: List[LogEntry] = []
        self.cleaned_logs: List[LogEntry] = []
        self.analysis_result: Optional[AnalysisResult] = None

    def process_bug(
        self,
        bug_description: str,
        log_path: str,
        output_report: str = "bug_report.md"
    ) -> StandardizedBugData:
        """完整的bug处理流程"""
        
        print("=" * 60)
        print("Android 日志分析 AI Agent")
        print("=" * 60)
        
        # 步骤1: 解析bug描述
        print("\n[1/6] 解析bug描述...")
        bug_desc = self.bug_parser.parse(bug_description)
        print(f"  - 摘要: {bug_desc.summary}")
        print(f"  - 关键词: {bug_desc.keywords}")
        
        # 步骤2: 创建标准化数据对象
        print("\n[2/6] 初始化标准化数据...")
        bug_id = self.storage.generate_bug_id()
        self.current_bug_data = StandardizedBugData(
            bug_id=bug_id,
            created_at=datetime.now(),
            bug_description=bug_desc
        )
        print(f"  - Bug ID: {bug_id}")
        
        # 步骤3: 提取和解析日志
        print("\n[3/6] 提取并解析日志文件...")
        extractor = LogExtractor()
        log_dir = extractor.extract(log_path)
        
        # 使用bugreport解析器
        parser = BugReportParser(log_dir)
        self.all_logs = parser.parse_all()
        print(f"  - 解析到 {len(self.all_logs)} 条日志")
        
        # 提取日志元数据
        self.current_bug_data.log_metadata = parser.extract_metadata()
        
        # 步骤4: 清洗日志
        print("\n[4/6] 清洗日志...")
        cleaner = LogCleaner(self.all_logs)
        self.cleaned_logs = cleaner.clean_all()
        print(f"  - 清洗后剩余 {len(self.cleaned_logs)} 条日志")
        
        # 保存所有清洗后的日志用于分析，不过度过滤
        # 但可以另外保存一份关键词过滤后的用于场景化分析
        self.keyword_filtered_logs = []
        if bug_desc.keywords:
            self.keyword_filtered_logs = cleaner.filter_by_keyword(bug_desc.keywords)
            print(f"  - 关键词过滤结果: {len(self.keyword_filtered_logs)} 条相关日志")
        
        # 步骤5: 分析日志
        print("\n[5/6] 分析日志...")
        analyzer = LogAnalyzer(self.cleaned_logs)
        self.analysis_result = analyzer.analyze()
        
        # 保存分析结果
        self.current_bug_data.analysis_results = {
            'crashes': len(self.analysis_result.crashes),
            'anrs': len(self.analysis_result.anrs),
            'low_memory': len(self.analysis_result.low_memory),
            'exceptions': len(self.analysis_result.exceptions),
            'other_issues': len(self.analysis_result.other_issues)
        }
        print(f"  - 发现 {self.current_bug_data.analysis_results['crashes']} 个崩溃")
        print(f"  - 发现 {self.current_bug_data.analysis_results['anrs']} 个ANR")
        
        # 步骤6: 生成报告
        print("\n[6/6] 生成分析报告...")
        relevant_logs = (
            self.analysis_result.crashes +
            self.analysis_result.anrs +
            self.analysis_result.low_memory +
            self.analysis_result.exceptions
        )
        report = self.report_gen.generate_report(
            self.current_bug_data,
            self.analysis_result,
            relevant_logs
        )
        
        self.current_bug_data.final_report = report
        
        # 保存报告
        with open(output_report, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"  - 报告已保存到: {output_report}")
        
        # 保存标准化数据
        self.storage.save_bug_data(self.current_bug_data)
        print(f"  - 数据已保存到: bug_data/{bug_id}.json")
        
        # 清理临时文件
        extractor.cleanup()
        
        print("\n" + "=" * 60)
        print("处理完成!")
        print("=" * 60)
        
        return self.current_bug_data

    def ask_scenario_question(self, question: str) -> str:
        """针对场景化问题进行分析"""
        if not self.current_bug_data or not self.cleaned_logs:
            return "请先处理一个bug，然后再问问题。"
        
        print(f"\n分析场景化问题: {question}")
        context = f"Bug ID: {self.current_bug_data.bug_id}\nBug描述: {self.current_bug_data.bug_description.summary}"
        
        result = self.scenario_analyzer.analyze(
            query=question,
            logs=self.cleaned_logs,
            context=context
        )
        
        print(f"  - 找到 {len(result.relevant_logs)} 条相关日志")
        return result.analysis_result

    def get_bug_info(self) -> Optional[StandardizedBugData]:
        """获取当前处理的bug信息"""
        return self.current_bug_data
