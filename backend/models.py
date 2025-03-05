from pydantic import BaseModel
from typing import List, Optional, Literal
from datetime import datetime

class Task(BaseModel):
    """Model representing a project task"""
    id: str
    name: str
    start_date: datetime
    end_date: datetime
    duration: int
    predecessors: Optional[List[str]] = None
    successors: Optional[List[str]] = None

class TaskAnalysisRequest(BaseModel):
    """Model for task analysis request"""
    query_type: Literal["holiday_impact", "weekend_impact", "general_query"]
    specific_date: Optional[datetime] = None
    include_dependencies: bool = False

class TaskImpact(BaseModel):
    """Model representing task impact analysis"""
    task: Task
    impact_type: Literal["holiday", "weekend"]
    impact_description: str
    delay_days: Optional[int] = None

class AnalysisResponse(BaseModel):
    """Model for analysis response"""
    impacted_tasks: List[TaskImpact]
    total_project_delay: Optional[int] = None
    analysis_summary: str