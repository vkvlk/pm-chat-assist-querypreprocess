import instructor
import logging
from typing import Optional, Dict, Any, Union, List
from datetime import datetime
import re
from dateutil import parser as date_parser
from pydantic import BaseModel
import sys
import os
from openai import OpenAI

# Add the project root to the path to enable absolute imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.config import settings
from .schemas import TaskAnalysisResponse, ScheduleImpactResponse, GeneralQueryResponse

logger = logging.getLogger(__name__)

# Initialize OpenRouter client with Instructor for Gemini model
client = instructor.from_openai(OpenAI(
    api_key=settings.OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1"),
    mode=instructor.Mode.JSON,
    
)

class QueryProcessor:
    """Class for processing natural language queries using LLM"""
    
    def __init__(self):
        """Initialize the query processor"""
        self.client = client
    
    def process_query(self, query: str) -> Union[TaskAnalysisResponse, ScheduleImpactResponse, GeneralQueryResponse]:
        """Process a natural language query and return structured response
        
        Args:
            query: User's natural language query
            
        Returns:
            Union[TaskAnalysisResponse, ScheduleImpactResponse, GeneralQueryResponse]: Structured response
        """
        # Pre-process query to extract dates and other entities
        preprocessed_query = self._preprocess_query(query)
        
        # Determine query type based on content
        if self._is_holiday_query(preprocessed_query):
            return self._get_task_analysis_response(query, "holiday_impact")
        elif self._is_weekend_query(preprocessed_query):
            return self._get_schedule_impact_response(query, "weekend_impact")
        elif self._is_specific_date_query(preprocessed_query):
            date = self._extract_date(query)
            return self._get_task_analysis_response(query, "specific_date", date)
        else:
            return self._get_general_query_response(query)
    
    def _preprocess_query(self, query: str) -> str:
        """Preprocess the query for better entity extraction
        
        Args:
            query: Original query
            
        Returns:
            str: Preprocessed query
        """
        # Convert to lowercase for easier matching
        return query.lower()
    
    def _is_holiday_query(self, query: str) -> bool:
        """Check if query is about holiday impact
        
        Args:
            query: Preprocessed query
            
        Returns:
            bool: True if query is about holidays
        """
        holiday_keywords = ["holiday", "federal holiday", "national holiday"]
        return any(keyword in query for keyword in holiday_keywords)
    
    def _is_weekend_query(self, query: str) -> bool:
        """Check if query is about weekend impact
        
        Args:
            query: Preprocessed query
            
        Returns:
            bool: True if query is about weekends
        """
        weekend_keywords = ["weekend", "saturday", "sunday"]
        return any(keyword in query for keyword in weekend_keywords)
    
    def _is_specific_date_query(self, query: str) -> bool:
        """Check if query is about a specific date
        
        Args:
            query: Preprocessed query
            
        Returns:
            bool: True if query mentions a specific date
        """
        # Check for date patterns or holiday names
        date_patterns = [
            r'\b\d{1,2}/\d{1,2}(/\d{2,4})?\b',  # MM/DD/YYYY or MM/DD
            r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}(st|nd|rd|th)?(,\s+\d{4})?\b',
            r'\bjuly\s+4th\b',  # Special case for July 4th
            r'\bnew\s+year\b',
            r'\bchristmas\b',
            r'\bthanksgiving\b',
            r'\bmemorial\s+day\b',
            r'\blabor\s+day\b',
            r'\bindependence\s+day\b',
            r'\bveterans\s+day\b',
            r'\bmlk\s+day\b',
            r'\bmartin\s+luther\s+king\b'
        ]
        
        return any(re.search(pattern, query, re.IGNORECASE) for pattern in date_patterns)
    
    def _extract_date(self, query: str) -> Optional[datetime]:
        """Extract date from query
        
        Args:
            query: Original query
            
        Returns:
            Optional[datetime]: Extracted date if found
        """
        try:
            # Handle special cases first
            if re.search(r'\bjuly\s+4th\b', query, re.IGNORECASE):
                # Get current year
                current_year = datetime.now().year
                return datetime(current_year, 7, 4)
            
            # Try to extract date using dateutil parser
            # This is a simplified approach and might need refinement
            for word in query.split():
                try:
                    date = date_parser.parse(word, fuzzy=True)
                    return date
                except:
                    continue
            
            return None
        except Exception as e:
            logger.error(f"Error extracting date: {str(e)}")
            return None
    
    def _get_task_analysis_response(self, query: str, analysis_type: str, specific_date: Optional[datetime] = None) -> TaskAnalysisResponse:
        """Get structured task analysis response from LLM"""
        prompt = self._create_task_analysis_prompt(query, analysis_type, specific_date)
        
        try:
            # Add default values for the response
            default_response = TaskAnalysisResponse(
                response_type="task_analysis",
                query_understanding="Error processing query",
                analysis_type=analysis_type,
                specific_date=specific_date,
                impacted_tasks_count=0,
                impact_summary="No response from LLM"
            )
    
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a project management assistant that analyzes MS Project data."},
                    {"role": "user", "content": prompt}
                ],
                model=settings.MODEL_NAME,
                response_model=TaskAnalysisResponse,
                temperature=settings.TEMPERATURE,
                max_tokens=settings.MAX_TOKENS
            )
            
            return response if response is not None else default_response
            
        except Exception as e:
            logger.error(f"Error getting LLM response: {str(e)}")
            return default_response
    
    # Similarly update _get_schedule_impact_response and _get_general_query_response with the same pattern
    def _get_schedule_impact_response(self, query: str, analysis_type: str) -> ScheduleImpactResponse:
        """Get structured schedule impact response from LLM
        
        Args:
            query: Original query
            analysis_type: Type of analysis
            
        Returns:
            ScheduleImpactResponse: Structured response
        """
        prompt = self._create_schedule_impact_prompt(query, analysis_type)
        
        try:
            response = self.client.chat.completions.create(
                model=settings.MODEL_NAME,
                response_model=ScheduleImpactResponse,
                messages=[
                    {"role": "system", "content": "You are a project management assistant that analyzes MS Project data."},
                    {"role": "user", "content": prompt}
                ],
                temperature=settings.TEMPERATURE,
                max_tokens=settings.MAX_TOKENS
            )
            return response
        except Exception as e:
            logger.error(f"Error getting LLM response: {str(e)}")
            # Return a fallback response
            return ScheduleImpactResponse(
                response_type="schedule_impact",
                query_understanding="Error processing query",
                analysis_type=analysis_type,
                total_delay_days=0,
                impact_summary=f"Error: {str(e)}"
            )
    
    def _get_general_query_response(self, query: str) -> GeneralQueryResponse:
        """Get structured general query response from LLM
        
        Args:
            query: Original query
            
        Returns:
            GeneralQueryResponse: Structured response
        """
        prompt = self._create_general_query_prompt(query)
        
        try:
            response = self.client.chat.completions.create(
                model=settings.MODEL_NAME,
                response_model=GeneralQueryResponse,
                messages=[
                    {"role": "system", "content": "You are a project management assistant that analyzes MS Project data."},
                    {"role": "user", "content": prompt}
                ],
                temperature=settings.TEMPERATURE,
                max_tokens=settings.MAX_TOKENS
            )
            return response
        except Exception as e:
            logger.error(f"Error getting LLM response: {str(e)}")
            # Return a fallback response
            return GeneralQueryResponse(
                response_type="general_query",
                query_understanding="Error processing query",
                analysis_type="general_query",
                answer=f"Error: {str(e)}",
                confidence=0.0
            )
    
    def _create_task_analysis_prompt(self, query: str, analysis_type: str, specific_date: Optional[datetime] = None) -> str:
        """Create prompt for task analysis
        
        Args:
            query: Original query
            analysis_type: Type of analysis
            specific_date: Specific date if applicable
            
        Returns:
            str: Formatted prompt
        """
        prompt = f"""Analyze the following query about project tasks: "{query}"
        
        Analysis type: {analysis_type}
        """
        
        if specific_date:
            prompt += f"\nSpecific date mentioned: {specific_date.strftime('%Y-%m-%d')}"
        
        prompt += """\n\nProvide a structured response with:
        1. Your understanding of the query
        2. The type of analysis needed
        3. Any specific dates or entities mentioned
        4. A summary of the potential impact
        5. Suggested follow-up questions
        
        Format your response according to the TaskAnalysisResponse schema.
        """
        
        return prompt
    
    def _create_schedule_impact_prompt(self, query: str, analysis_type: str) -> str:
        """Create prompt for schedule impact analysis
        
        Args:
            query: Original query
            analysis_type: Type of analysis
            
        Returns:
            str: Formatted prompt
        """
        prompt = f"""Analyze the following query about project schedule impact: "{query}"
        
        Analysis type: {analysis_type}
        
        Provide a structured response with:
        1. Your understanding of the query
        2. The type of impact analysis needed
        3. An estimate of the total delay in days
        4. A summary of the schedule impact
        5. Any key milestones that might be affected
        6. Suggested follow-up questions
        
        Format your response according to the ScheduleImpactResponse schema.
        """
        
        return prompt
    
    def _create_general_query_prompt(self, query: str) -> str:
        """Create prompt for general queries
        
        Args:
            query: Original query
            
        Returns:
            str: Formatted prompt
        """
        prompt = f"""Answer the following general query about project management: "{query}"
        
        Provide a structured response with:
        1. Your understanding of the query
        2. A direct answer to the question
        3. Your confidence level in the answer (0.0 to 1.0)
        4. Any relevant entities extracted from the query
        5. Suggested follow-up questions
        
        Format your response according to the GeneralQueryResponse schema.
        """
        
        return prompt