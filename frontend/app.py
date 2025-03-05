import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import os
from datetime import datetime, timedelta
import logging

# Add parent directory to path to import from backend and llm
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.data_loader import DataLoader
from backend.analyzer import ProjectAnalyzer
from llm.query_processor import QueryProcessor
from backend.config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize session state
def init_session_state():
    if 'data_loaded' not in st.session_state:
        st.session_state.data_loaded = False
    if 'tasks' not in st.session_state:
        st.session_state.tasks = []
    if 'data_loader' not in st.session_state:
        st.session_state.data_loader = None
    if 'analyzer' not in st.session_state:
        st.session_state.analyzer = ProjectAnalyzer()
    if 'query_processor' not in st.session_state:
        st.session_state.query_processor = QueryProcessor()
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

# Load data function
def load_data(file_path):
    try:
        data_loader = DataLoader(file_path)
        success = data_loader.load_data()
        
        if success:
            tasks = data_loader.process_data()
            st.session_state.data_loaded = True
            st.session_state.tasks = tasks
            st.session_state.data_loader = data_loader
            return True, f"Successfully loaded {len(tasks)} tasks"
        else:
            return False, "Failed to load data"
    except Exception as e:
        logger.error(f"Error loading data: {str(e)}")
        return False, f"Error: {str(e)}"

# Process user query
def process_query(query):
    try:
        # Process query using LLM
        llm_response = st.session_state.query_processor.process_query(query)
        
        # Based on response type, perform appropriate analysis
        if llm_response.response_type == "task_analysis":
            if llm_response.analysis_type == "holiday_impact":
                analysis = st.session_state.analyzer.find_holiday_tasks(st.session_state.tasks)
                return format_task_impact_response(llm_response, analysis)
            
            elif llm_response.analysis_type == "specific_date" and llm_response.specific_date:
                analysis = st.session_state.analyzer.find_tasks_impacted_by_date(
                    st.session_state.tasks, llm_response.specific_date
                )
                return format_task_impact_response(llm_response, analysis)
        
        elif llm_response.response_type == "schedule_impact":
            if llm_response.analysis_type == "weekend_impact":
                analysis = st.session_state.analyzer.calculate_weekend_impact(st.session_state.tasks)
                return format_schedule_impact_response(llm_response, analysis)
        
        # For general queries or fallbacks
        return {
            "text": llm_response.answer if hasattr(llm_response, 'answer') else llm_response.query_understanding,
            "follow_up": llm_response.follow_up_questions,
            "data": None,
            "chart": None
        }
        
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        return {"text": f"Error processing your query: {str(e)}", "follow_up": [], "data": None, "chart": None}

# Format task impact response
def format_task_impact_response(llm_response, analysis):
    # Create a DataFrame for visualization
    if analysis and len(analysis) > 0:
        data = [{
            "Task ID": impact.task.id,
            "Task Name": impact.task.name,
            "Start Date": impact.task.start_date,
            "End Date": impact.task.end_date,
            "Impact Type": impact.impact_type,
            "Impact Description": impact.impact_description,
            "Delay (Days)": impact.delay_days or 0
        } for impact in analysis]
        
        df = pd.DataFrame(data)
        
        # Create a Gantt chart
        fig = px.timeline(
            df, 
            x_start="Start Date", 
            x_end="End Date", 
            y="Task Name",
            color="Impact Type",
            hover_data=["Task ID", "Impact Description", "Delay (Days)"]
        )
        
        fig.update_layout(
            title="Tasks Impacted by Holidays/Weekends",
            xaxis_title="Date",
            yaxis_title="Task",
            height=600
        )
        
        return {
            "text": llm_response.impact_summary if hasattr(llm_response, 'impact_summary') else 
                   f"Found {len(analysis)} impacted tasks.",
            "follow_up": llm_response.follow_up_questions,
            "data": df,
            "chart": fig
        }
    else:
        return {
            "text": "No tasks found matching your query.",
            "follow_up": llm_response.follow_up_questions,
            "data": None,
            "chart": None
        }

# Format schedule impact response
def format_schedule_impact_response(llm_response, analysis):
    if analysis and len(analysis.impacted_tasks) > 0:
        data = [{
            "Task ID": impact.task.id,
            "Task Name": impact.task.name,
            "Start Date": impact.task.start_date,
            "End Date": impact.task.end_date,
            "Impact Type": impact.impact_type,
            "Impact Description": impact.impact_description,
            "Delay (Days)": impact.delay_days or 0
        } for impact in analysis.impacted_tasks]
        
        df = pd.DataFrame(data)
        
        # Create a bar chart showing delay by task
        fig = px.bar(
            df.sort_values("Delay (Days)", ascending=False).head(10),
            x="Task Name",
            y="Delay (Days)",
            color="Impact Type",
            title="Top 10 Tasks with Highest Delay"
        )
        
        return {
            "text": llm_response.impact_summary if hasattr(llm_response, 'impact_summary') else analysis.analysis_summary,
            "follow_up": llm_response.follow_up_questions,
            "data": df,
            "chart": fig
        }
    else:
        return {
            "text": "No schedule impact found for your query.",
            "follow_up": llm_response.follow_up_questions,
            "data": None,
            "chart": None
        }

# Main app
def main():
    st.set_page_config(page_title="Project Q&A Assistant", page_icon="📊", layout="wide")
    
    # Initialize session state
    init_session_state()
    
    # App title and description
    st.title("📊 Project Q&A Assistant")
    st.markdown(
        """This app analyzes MS Project data to answer questions about holiday and weekend impacts on your project schedule.
        Upload your project data and ask questions like:
        - Which tasks start on a holiday?
        - Which tasks are impacted by July 4th?
        - How many days would we prolong project delivery if no task can be completed during weekends?
        """
    )
    
    # Sidebar for data upload
    with st.sidebar:
        st.header("Data Upload")
        uploaded_file = st.file_uploader("Upload MS Project Excel file", type=["xlsx"])
        
        if uploaded_file is not None:
            # Save the uploaded file temporarily
            with open("temp_project_data.xlsx", "wb") as f:
                f.write(uploaded_file.getvalue())
            
            if st.button("Load Data"):
                success, message = load_data("temp_project_data.xlsx")
                if success:
                    st.success(message)
                else:
                    st.error(message)
        
        # Display data stats if loaded
        if st.session_state.data_loaded:
            st.subheader("Data Statistics")
            st.write(f"Total tasks: {len(st.session_state.tasks)}")
            
            # Count tasks with weekend/holiday impacts
            holiday_tasks = len(st.session_state.analyzer.find_holiday_tasks(st.session_state.tasks))
            weekend_tasks = len(st.session_state.analyzer.find_weekend_tasks(st.session_state.tasks))
            
            st.write(f"Tasks affected by holidays: {holiday_tasks}")
            st.write(f"Tasks affected by weekends: {weekend_tasks}")
    
    # Main content area
    if not st.session_state.data_loaded:
        st.info("Please upload and load your project data to begin.")
    else:
        # Chat interface
        st.subheader("Ask about your project schedule")
        
        # Query input
        query = st.text_input("Enter your question:")
        
        if query:
            # Add user query to chat history
            st.session_state.chat_history.append({"role": "user", "content": query})
            
            # Process query
            response = process_query(query)
            
            # Add assistant response to chat history
            st.session_state.chat_history.append({"role": "assistant", "content": response})
        
        # Display chat history
        st.subheader("Conversation")
        for idx, message in enumerate(st.session_state.chat_history):
            if message["role"] == "user":
                st.markdown(f"**You:** {message['content']}")
            else:
                st.markdown(f"**Assistant:** {message['content']['text']}")
                
                # Display data table if available
                if message['content']['data'] is not None:
                    with st.expander("View Data"):
                        st.dataframe(message['content']['data'])
                
                # Display chart if available
                if message['content']['chart'] is not None:
                    st.plotly_chart(message['content']['chart'], use_container_width=True, key=f"chart_{idx}")
                
                # Display follow-up suggestions
                if message['content']['follow_up'] and len(message['content']['follow_up']) > 0:
                    st.subheader("Follow-up Questions")
                    for i, question in enumerate(message['content']['follow_up']):
                        if st.button(question, key=f"follow_up_{idx}_{i}"):
                            # Add follow-up to chat history
                            st.session_state.chat_history.append({"role": "user", "content": question})
                            
                            # Process follow-up
                            follow_up_response = process_query(question)
                            
                            # Add assistant response
                            st.session_state.chat_history.append({"role": "assistant", "content": follow_up_response})
                            
                            # Rerun to update UI
                            st.rerun()

if __name__ == "__main__":
    main()