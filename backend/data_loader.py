import pandas as pd
from datetime import datetime
from typing import List, Dict, Any
from .models import Task
import logging

logger = logging.getLogger(__name__)

class DataLoader:
    """Class for loading and processing MS Project data from Excel"""
    
    def __init__(self, file_path: str):
        """Initialize with the path to the Excel file"""
        self.file_path = file_path
        self.raw_data = None
        self.tasks = []
    
    def load_data(self) -> bool:
        """Load data from Excel file
        
        Returns:
            bool: True if data loaded successfully, False otherwise
        """
        try:
            self.raw_data = pd.read_excel(self.file_path)
            logger.info(f"Successfully loaded data from {self.file_path}")
            return True
        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")
            return False
    
    def _process_duration(self, duration_str):
        """Process duration string into number of days"""
        if pd.isna(duration_str) or not duration_str:
            return 0
        
        try:
            # Handle case where duration is already a number
            if isinstance(duration_str, (int, float)):
                return int(duration_str)
                
            # Remove any non-numeric characters and extract the number
            duration_str = str(duration_str).strip().lower()
            
            # Handle different duration formats
            if 'wk' in duration_str:  # Handle both 'wk' and 'wks'
                # Extract the number before 'wk'
                weeks = float(duration_str.split('wk')[0].strip())
                return int(weeks * 5)  # Convert weeks to days
            elif 'day' in duration_str:
                # Extract the number before 'days'
                days = float(duration_str.split('day')[0].strip())
                return int(days)
            elif 'week' in duration_str:
                # Convert weeks to days (1 week = 5 working days)
                weeks = float(duration_str.split('week')[0].strip())
                return int(weeks * 5)
            elif 'hour' in duration_str:
                # Convert hours to days (8 hours = 1 day)
                hours = float(duration_str.split('hour')[0].strip())
                return int(hours / 8)
            else:
                # Try to convert directly to integer
                return int(float(duration_str))
        except Exception as e:
            logger.warning(f"Could not parse duration '{duration_str}': {str(e)}. Using 0.")
            return 0

    def process_data(self) -> List[Task]:
        """Process raw data into Task objects"""
        if self.raw_data is None:
            logger.warning("No data loaded. Call load_data() first.")
            return []
        
        try:
            tasks = []
            
            # Drop any completely empty rows
            self.raw_data = self.raw_data.dropna(how='all')
            
            # Ensure required columns exist
            required_columns = ['Index', 'Task Name', 'Duration', 'Start', 'Finish', 'Predecessors', 'Successors']  
            missing_columns = [col for col in required_columns if col not in self.raw_data.columns]
            if missing_columns:
                logger.error(f"Missing required columns: {missing_columns}")
                return []
                
            for _, row in self.raw_data.iterrows():
                # Skip rows where essential data is missing
                if pd.isna(row['Index']) or pd.isna(row['Task Name']):
                    continue
                    
                # Extract task data from row
                task_id = str(row['Index'])
                task_name = str(row['Task Name'])
                
                # Handle date parsing with validation
                start_date = self._parse_date(row['Start'])
                end_date = self._parse_date(row['Finish'])
                
                # Ensure end date is not before start date
                if end_date < start_date:
                    end_date = start_date
                
                # Get duration in days
                duration = self._process_duration(row['Duration'])
                
                # Extract dependencies
                predecessors = self._parse_dependencies(row.get('Predecessors', ''))
                successors = self._parse_dependencies(row.get('Successors', ''))
                
                task = Task(
                    id=task_id,
                    name=task_name,
                    start_date=start_date,
                    end_date=end_date,
                    duration=duration,
                    predecessors=predecessors,
                    successors=successors
                )
                
                tasks.append(task)
            
            self.tasks = tasks
            logger.info(f"Processed {len(tasks)} tasks from data")
            return tasks
                
        except Exception as e:
            logger.error(f"Error processing data: {str(e)}")
            return []
    
    def _parse_date(self, date_value) -> datetime:
        """Parse date from Excel format
        
        Args:
            date_value: Date value from Excel
            
        Returns:
            datetime: Parsed datetime object
        """
        if pd.isna(date_value):
            return datetime.now()  # Default to current date if missing
        
        if isinstance(date_value, datetime):
            return date_value
        
        try:
            return pd.to_datetime(date_value)
        except:
            logger.warning(f"Could not parse date: {date_value}, using current date")
            return datetime.now()
    
    def _parse_dependencies(self, deps_str) -> List[str]:
        """Parse dependency strings into list of task IDs
        
        Args:
            deps_str: String containing dependencies
            
        Returns:
            List[str]: List of task IDs
        """
        if pd.isna(deps_str) or not deps_str:
            return []
        
        # MS Project typically uses comma-separated IDs for dependencies
        # May need adjustment based on actual format
        try:
            return [dep.strip() for dep in str(deps_str).split(',')]
        except:
            return []
    
    def get_task_by_id(self, task_id: str) -> Task:
        """Get a task by its ID
        
        Args:
            task_id: ID of the task to retrieve
            
        Returns:
            Task: Task object if found, None otherwise
        """
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None
    
    def get_all_tasks(self) -> List[Task]:
        """Get all tasks
        
        Returns:
            List[Task]: All processed tasks
        """
        return self.tasks