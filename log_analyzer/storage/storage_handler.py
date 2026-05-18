import os
import json
import uuid
from datetime import datetime
from typing import Optional
from log_analyzer.models import StandardizedBugData

from harness.core.paths import BUG_DATA_DIR_STR


class StorageHandler:
    """标准化数据存储处理器"""
    
    def __init__(self, storage_dir: str = None):
        self.storage_dir = storage_dir or BUG_DATA_DIR_STR
        if not os.path.exists(storage_dir):
            os.makedirs(storage_dir)

    def save_bug_data(self, bug_data: StandardizedBugData) -> str:
        """保存bug数据"""
        file_path = os.path.join(self.storage_dir, f"{bug_data.bug_id}.json")
        data = self._bug_data_to_dict(bug_data)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return file_path

    def load_bug_data(self, bug_id: str) -> Optional[StandardizedBugData]:
        """加载bug数据"""
        file_path = os.path.join(self.storage_dir, f"{bug_id}.json")
        if not os.path.exists(file_path):
            return None
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return self._dict_to_bug_data(data)

    def generate_bug_id(self) -> str:
        """生成唯一bug ID"""
        return f"bug_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

    def _bug_data_to_dict(self, bug_data: StandardizedBugData) -> dict:
        return {
            'bug_id': bug_data.bug_id,
            'created_at': bug_data.created_at.isoformat(),
            'bug_description': {
                'raw_text': bug_data.bug_description.raw_text,
                'summary': bug_data.bug_description.summary,
                'package_name': bug_data.bug_description.package_name,
                'app_version': bug_data.bug_description.app_version,
                'android_version': bug_data.bug_description.android_version,
                'device_model': bug_data.bug_description.device_model,
                'time_points': bug_data.bug_description.time_points,
                'reproduction_steps': bug_data.bug_description.reproduction_steps,
                'keywords': bug_data.bug_description.keywords,
                'user_scenarios': bug_data.bug_description.user_scenarios,
                'expected_behavior': bug_data.bug_description.expected_behavior,
                'actual_behavior': bug_data.bug_description.actual_behavior,
                'frequency': bug_data.bug_description.frequency
            },
            'log_metadata': bug_data.log_metadata,
            'analysis_results': bug_data.analysis_results,
            'final_report': bug_data.final_report
        }

    def _dict_to_bug_data(self, data: dict) -> StandardizedBugData:
        from log_analyzer.models import BugDescription
        
        bug_desc = BugDescription(
            raw_text=data['bug_description']['raw_text'],
            summary=data['bug_description'].get('summary'),
            package_name=data['bug_description'].get('package_name'),
            app_version=data['bug_description'].get('app_version'),
            android_version=data['bug_description'].get('android_version'),
            device_model=data['bug_description'].get('device_model'),
            time_points=data['bug_description'].get('time_points', []),
            reproduction_steps=data['bug_description'].get('reproduction_steps', []),
            keywords=data['bug_description'].get('keywords', []),
            user_scenarios=data['bug_description'].get('user_scenarios', []),
            expected_behavior=data['bug_description'].get('expected_behavior'),
            actual_behavior=data['bug_description'].get('actual_behavior'),
            frequency=data['bug_description'].get('frequency')
        )
        
        return StandardizedBugData(
            bug_id=data['bug_id'],
            created_at=datetime.fromisoformat(data['created_at']),
            bug_description=bug_desc,
            log_metadata=data.get('log_metadata', {}),
            analysis_results=data.get('analysis_results', {}),
            final_report=data.get('final_report')
        )
