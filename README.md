# Tax Scenario Assistant

A multi-agent tax analysis system that helps users understand their tax scenarios and identify optimal tax strategies through a conversational AI interface.

![Tax Scenario Assistant](https://via.placeholder.com/800x400?text=Tax+Scenario+Assistant)

## 📑 Overview

The Tax Scenario Assistant is an interactive application that uses multiple specialized AI agents to process tax scenarios, generate relevant questions, validate responses, and provide customized tax strategy recommendations. The system helps users identify potential tax savings opportunities based on their specific financial situation.

## ✨ Features

- **Multi-Agent Architecture**: Three specialized agents working together for comprehensive tax analysis
- **Conversational Interface**: Natural language interaction for describing tax scenarios
- **Question Generation**: Automatic generation of relevant questions based on the user's initial scenario
- **File Upload Support**: Upload tax scenarios and answers via text files
- **Strategy Analysis**: Identification of applicable tax strategies with detailed explanations
- **Tax Savings Estimations**: Potential tax savings calculations for recommended strategies
- **Export Options**: Download analysis results and structured data in multiple formats

## 🏗️ System Architecture

The application employs a three-agent architecture:

1. **Agent 1: Question Generation**
   - Analyzes the initial tax scenario description
   - Generates comprehensive questions needed for proper tax filing
   - Structures the information gathering process

2. **Agent 2: Response Validation**
   - Validates user responses to questions
   - Determines if additional information is needed
   - Compares tax scenarios and provides baseline analysis

3. **Agent 3: Tax Strategy Analysis**
   - Processes the structured tax data
   - Identifies applicable tax strategies and optimization opportunities
   - Provides detailed tax strategy recommendations with estimated savings

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- OpenAI API key

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd poc-react-agent
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

### Running the Application

Start the Streamlit application:
```bash
streamlit run app.py
```

The application will be available at http://localhost:8501.

## 📖 Usage Guide

1. **Describe Your Tax Scenario**:
   - Enter your tax scenario in the text area or upload a text file with your scenario.
   - Click "Generate Questions" to proceed.

2. **Answer the Questions**:
   - Respond to each question individually or download the answer template.
   - Fill out the template and upload it to provide all answers at once.

3. **Review Tax Analysis**:
   - View the structured tax information.
   - Explore recommended tax strategies and potential savings.
   - Review detailed strategy information with implementation steps.

4. **Export Results**:
   - Download the complete tax analysis as a text file.
   - Export the structured tax data in JSON format.


