# Project Q&A Assistant

This project is a Streamlit-based web application designed to analyze MS Project data and answer questions about holiday and weekend impacts on your project schedule. The application leverages a Large Language Model (LLM) to process natural language queries and provide structured responses.

## Features

- **Data Upload**: Upload MS Project data in Excel format.
- **Task Analysis**: Identify tasks impacted by holidays and weekends.
- **Schedule Impact**: Calculate the impact of no weekend work on the project timeline.
- **Interactive Chat**: Ask questions about your project schedule and receive detailed responses.
- **Visualizations**: View data tables and charts for impacted tasks.

## Installation

1. Clone the repository:

   ```sh
   git clone https://github.com/yourusername/pm-chat-assist-querypreprocess.git
   cd pm-chat-assist-querypreprocess
   ```

2. Create and activate a virtual environment:

   ```sh
   python -m venv .venv
   .venv\Scripts\activate  # On Windows
   ```

3. Install the required dependencies:

   ```sh
   pip install -r requirements.txt
   ```

4. Create a [.env](http://_vscodecontentref_/0) file with your OpenRouter API key:
   ```env
   OPENROUTER_API_KEY=your_api_key_here
   ```

## Usage

1. Run the application:

   ```sh
   streamlit run frontend/app.py
   ```

2. Open your web browser and navigate to `http://localhost:8501`.

3. Upload your MS Project Excel file and start asking questions about your project schedule.

## Project Structure

- [frontend](http://_vscodecontentref_/1): Contains the Streamlit app code.
- [backend](http://_vscodecontentref_/2): Contains the data processing and analysis logic.
- [llm](http://_vscodecontentref_/3): Contains the query processing logic using LLM.
- [requirements.txt](http://_vscodecontentref_/4): Lists the required Python packages.
