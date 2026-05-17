from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class BugDescription:
    raw_text: str
    summary: Optional[str] = None
    package_name: Optional[str] = None
    app_version: Optional[str] = None
    android_version: Optional[str] = None
    device_model: Optional[str] = None
    time_points: List[str] = field(default_factory=list)
    reproduction_steps: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    user_scenarios: List[str] = field(default_factory=list)
    expected_behavior: Optional[str] = None
    actual_behavior: Optional[str] = None
    frequency: Optional[str] = None


@dataclass
class StandardizedBugData:
    bug_id: str
    created_at: datetime
    bug_description: BugDescription
    log_metadata: Dict[str, Any] = field(default_factory=dict)
    analysis_results: Dict[str, Any] = field(default_factory=dict)
    final_report: Optional[str] = None


@dataclass
class ScenarioQuery:
    query: str
    context: Optional[str] = None
    relevant_logs: List[Any] = field(default_factory=list)
    analysis_result: Optional[str] = None
