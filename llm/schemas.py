from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any
from datetime import datetime

class DateQuery(BaseModel):
    """Model for date-specific queries"""
    date: datetime = Field(..., description="The specific date to analyze")
    query_type: Literal["holiday", "weekend", "specific_date"] = Field(..., description="Type of date query")

class TaskQuery(BaseModel):
    """Model for task-specific queries"""
    task_id: Optional[str] = Field(None, description="Specific task ID to analyze")
    task_name: Optional[str] = Field(None, description="Task name or keyword to search for")

class ScheduleImpactQuery(BaseModel):
    """Model for schedule impact queries"""
    impact_type: Literal["holiday", "weekend", "both"] = Field(..., description="Type of impact to analyze")
    calculate_delay: bool = Field(True, description="Whether to calculate total project delay")

class LLMResponse(BaseModel):
    """Model for structured LLM responses"""
    response_type: Literal["task_analysis", "schedule_impact", "general_query"] = Field(
        ..., description="Type of response being provided"
    )
    query_understanding: str = Field(
        ..., description="LLM's understanding of the user's query"
    )
    analysis_type: Literal["holiday_impact", "weekend_impact", "specific_date", "general_query"] = Field(
        ..., description="Type of analysis performed"
    )
    specific_date: Optional[datetime] = Field(
        None, description="Specific date mentioned in the query, if any"
    )
    extracted_entities: Dict[str, Any] = Field(
        default_factory=dict, description="Entities extracted from the query"
    )
    follow_up_questions: List[str] = Field(
        default_factory=list, description="Suggested follow-up questions"
    )

class TaskAnalysisResponse(LLMResponse):
    """Model for task analysis responses"""
    response_type: Literal["task_analysis"] = "task_analysis"
    impacted_tasks_count: int = Field(..., description="Number of tasks impacted")
    impact_summary: str = Field(..., description="Summary of the impact")

class ScheduleImpactResponse(LLMResponse):
    """Model for schedule impact responses"""
    response_type: Literal["schedule_impact"] = "schedule_impact"
    total_delay_days: int = Field(..., description="Total project delay in days")
    impact_summary: str = Field(..., description="Summary of the schedule impact")
    affected_milestones: List[str] = Field(
        default_factory=list, description="Key milestones affected by the impact"
    )

class GeneralQueryResponse(LLMResponse):
    """Model for general query responses"""
    response_type: Literal["general_query"] = "general_query"
    answer: str = Field(..., description="Answer to the general query")
    confidence: float = Field(..., description="Confidence score for the answer", ge=0, le=1)