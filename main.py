import os
import sys
import logging
from backend.config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def main():
    """Main entry point for the application"""
    try:
        # Add the current directory to the path so we can import modules
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        
        # Import here to avoid circular imports
        from frontend.app import main as run_app
        
        # Run the Streamlit app
        run_app()
        
    except Exception as e:
        logger.error(f"Error starting application: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    # Run the main function
    main()