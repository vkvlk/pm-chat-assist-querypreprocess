from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from .models import Task, TaskImpact, AnalysisResponse
from .date_utils import DateUtils
import logging

logger = logging.getLogger(__name__)

class ProjectAnalyzer:
    """Class for analyzing project tasks for holiday and weekend impacts"""
    
    def __init__(self):
        """Initialize the analyzer with date utilities"""
        self.date_utils = DateUtils()
    
    def find_holiday_tasks(self, tasks: List[Task]) -> List[TaskImpact]:
        """Find tasks that start or end on holidays
        
        Args:
            tasks: List of project tasks to analyze
            
        Returns:
            List[TaskImpact]: List of impacted tasks with impact details
        """
        impacted_tasks = []
        
        for task in tasks:
            start_holiday = self.date_utils.is_holiday(task.start_date)
            end_holiday = self.date_utils.is_holiday(task.end_date)
            
            if start_holiday or end_holiday:
                impact_desc = []
                
                if start_holiday:
                    holiday_name = self.date_utils.get_holiday_name(task.start_date)
                    impact_desc.append(f"Task starts on holiday: {holiday_name} ({task.start_date.strftime('%Y-%m-%d')})")
                
                if end_holiday:
                    holiday_name = self.date_utils.get_holiday_name(task.end_date)
                    impact_desc.append(f"Task ends on holiday: {holiday_name} ({task.end_date.strftime('%Y-%m-%d')})")
                
                impact = TaskImpact(
                    task=task,
                    impact_type="holiday",
                    impact_description="; ".join(impact_desc),
                    delay_days=1 if start_holiday else 0  # Assuming 1 day delay if start date is holiday
                )
                
                impacted_tasks.append(impact)
        
        return impacted_tasks
    
    def find_weekend_tasks(self, tasks: List[Task]) -> List[TaskImpact]:
        """Find tasks that start or end on weekends
        
        Args:
            tasks: List of project tasks to analyze
            
        Returns:
            List[TaskImpact]: List of impacted tasks with impact details
        """
        impacted_tasks = []
        
        for task in tasks:
            start_weekend = self.date_utils.is_weekend(task.start_date)
            end_weekend = self.date_utils.is_weekend(task.end_date)
            
            if start_weekend or end_weekend:
                impact_desc = []
                
                if start_weekend:
                    impact_desc.append(f"Task starts on weekend ({task.start_date.strftime('%Y-%m-%d')})")
                
                if end_weekend:
                    impact_desc.append(f"Task ends on weekend ({task.end_date.strftime('%Y-%m-%d')})")
                
                impact = TaskImpact(
                    task=task,
                    impact_type="weekend",
                    impact_description="; ".join(impact_desc),
                    delay_days=2 if start_weekend and task.start_date.weekday() == 5 else 1 if start_weekend else 0
                    # 2 days delay if starting on Saturday, 1 day if Sunday
                )
                
                impacted_tasks.append(impact)
        
        return impacted_tasks
    
    def find_tasks_impacted_by_date(self, tasks: List[Task], target_date: datetime) -> List[TaskImpact]:
        """Find tasks impacted by a specific date (e.g., July 4th)
        
        Args:
            tasks: List of project tasks to analyze
            target_date: The specific date to check for impact
            
        Returns:
            List[TaskImpact]: List of impacted tasks with impact details
        """
        impacted_tasks = []
        
        # Check if target date is a holiday
        is_holiday = self.date_utils.is_holiday(target_date)
        holiday_name = self.date_utils.get_holiday_name(target_date) if is_holiday else ""
        
        for task in tasks:
            # Check if target date falls within task duration
            if task.start_date <= target_date <= task.end_date:
                impact_type = "holiday" if is_holiday else "weekend" if self.date_utils.is_weekend(target_date) else "general_query"
                
                impact_desc = f"Task is active on {target_date.strftime('%Y-%m-%d')}"
                if is_holiday:
                    impact_desc += f" which is a holiday: {holiday_name}"
                elif self.date_utils.is_weekend(target_date):
                    impact_desc += " which is a weekend"
                
                impact = TaskImpact(
                    task=task,
                    impact_type=impact_type,
                    impact_description=impact_desc,
                    delay_days=1 if is_holiday or self.date_utils.is_weekend(target_date) else 0
                )
                
                impacted_tasks.append(impact)
        
        return impacted_tasks
    
    def calculate_weekend_impact(self, tasks: List[Task]) -> AnalysisResponse:
        """Calculate the impact of no weekend work on project timeline
        
        Args:
            tasks: List of project tasks to analyze
            
        Returns:
            AnalysisResponse: Analysis of weekend impact on project
        """
        impacted_tasks = []
        total_delay = 0
        
        for task in tasks:
            # Count weekends within task duration
            weekend_days = 0
            current_date = task.start_date
            
            while current_date <= task.end_date:
                if self.date_utils.is_weekend(current_date):
                    weekend_days += 1
                current_date += timedelta(days=1)
            
            if weekend_days > 0:
                impact = TaskImpact(
                    task=task,
                    impact_type="weekend",
                    impact_description=f"Task spans {weekend_days} weekend days",
                    delay_days=weekend_days
                )
                
                impacted_tasks.append(impact)
                total_delay = max(total_delay, weekend_days)  # Simplified; actual calculation would need dependency analysis
        
        # Sort tasks by delay impact
        impacted_tasks.sort(key=lambda x: x.delay_days or 0, reverse=True)
        
        return AnalysisResponse(
            impacted_tasks=impacted_tasks,
            total_project_delay=total_delay,
            analysis_summary=f"Project would be delayed by approximately {total_delay} days if no weekend work is allowed."
        )
    
    def analyze_query(self, query_type: str, tasks: List[Task], specific_date: Optional[datetime] = None) -> AnalysisResponse:
        """Analyze tasks based on query type
        
        Args:
            query_type: Type of analysis to perform
            tasks: List of tasks to analyze
            specific_date: Specific date for date-based queries
            
        Returns:
            AnalysisResponse: Analysis results
        """
        if query_type == "holiday_impact":
            impacted_tasks = self.find_holiday_tasks(tasks)
            summary = f"Found {len(impacted_tasks)} tasks impacted by holidays"
            return AnalysisResponse(
                impacted_tasks=impacted_tasks,
                analysis_summary=summary
            )
            
        elif query_type == "weekend_impact":
            return self.calculate_weekend_impact(tasks)
            
        elif query_type == "specific_date" and specific_date:
            impacted_tasks = self.find_tasks_impacted_by_date(tasks, specific_date)
            date_str = specific_date.strftime("%Y-%m-%d")
            summary = f"Found {len(impacted_tasks)} tasks impacted by date {date_str}"
            return AnalysisResponse(
                impacted_tasks=impacted_tasks,
                analysis_summary=summary
            )
            
        else:
            return AnalysisResponse(
                impacted_tasks=[],
                analysis_summary="Invalid query type or missing required parameters"
            )