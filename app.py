import streamlit as st
from agent1.main import ScenarioClarificationAgent
import agent2.app
from agent3.main import Tax_Stratigies_Agent
import os
from dotenv import load_dotenv
import json
import io
# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Tax Scenario Assistant",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state variables
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []
if "clarifications" not in st.session_state:
    st.session_state.clarifications = []
if "scenario_submitted" not in st.session_state:
    st.session_state.scenario_submitted = False
if "user_scenario" not in st.session_state:
    st.session_state.user_scenario = ""
if "final_json" not in st.session_state:
    st.session_state.final_json = None
if "question_list" not in st.session_state:
    st.session_state.question_list = None
if "current_stage" not in st.session_state:
    st.session_state.current_stage = "question_generation"
if "all_questions" not in st.session_state:
    st.session_state.all_questions = []
if "file_answers" not in st.session_state:
    st.session_state.file_answers = None
if "submit_clicked" not in st.session_state:
    st.session_state.submit_clicked = False
if "switch_to_agent2" not in st.session_state:
    st.session_state.switch_to_agent2 = False
if "agent2_json_payload" not in st.session_state:
    st.session_state.agent2_json_payload = None
# Add initialization for the tax strategies variables
if "tax_strategies_processed" not in st.session_state:
    st.session_state.tax_strategies_processed = False
if "tax_strategies_result" not in st.session_state:
    st.session_state.tax_strategies_result = None

# Define the callback function for file submission
def handle_file_submit():
    """Sets the submit_clicked flag to trigger processing of file answers"""
    st.session_state.submit_clicked = True

# Initialize the agents
@st.cache_resource
def get_agent():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.error("OpenAI API key not found. Please check your .env file.")
        st.stop()
    return ScenarioClarificationAgent(openai_api_key=api_key)

@st.cache_resource
def get_tax_strategies_agent():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.error("OpenAI API key not found. Please check your .env file.")
        st.stop()
    return Tax_Stratigies_Agent(openai_api_key=api_key)

agent = get_agent()
tax_strategies_agent = get_tax_strategies_agent()

# Function to process text file with answers
def process_answers_file(file):
    content = file.getvalue().decode("utf-8")
    lines = content.split('\n')
    answers = []
    
    # Parse answers - look for lines with answers
    current_answer = ""
    for line in lines:
        line = line.strip()
        if line.startswith(('Q', 'Question', '#')) or not line:
            # If we hit a question marker or empty line and have a current answer, save it
            if current_answer:
                answers.append(current_answer.strip())
                current_answer = ""
        else:
            # Otherwise, this is part of an answer
            if current_answer:
                current_answer += "\n" + line
            else:
                current_answer = line
    
    # Add the last answer if there is one
    if current_answer:
        answers.append(current_answer.strip())
    
    return answers

# Function to generate sample answer file
def generate_sample_answer_file(questions):
    buffer = io.StringIO()
    for i, question in enumerate(questions, 1):
        # Extract just the question text (remove numbering if present)
        if '.' in question:
            question_text = question.split('.', 1)[1].strip()
        else:
            question_text = question
        
        buffer.write(f"Question {i}: {question_text}\n")
        buffer.write("Your answer here\n\n")
    
    return buffer.getvalue()

# Custom CSS for better UI
st.markdown("""
<style>
    .agent-header {
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
        font-weight: bold;
    }
    .agent1 {
        background-color: #e6f7ff;
        border-left: 5px solid #1890ff;
        color: #003a70;
    }
    .agent2 {
        background-color: #f6ffed;
        border-left: 5px solid #52c41a;
        color: #1f5c1f;
    }
    .agent3 {
        background-color: #fff7e6;
        border-left: 5px solid #fa8c16;
        color: #8b4513;
    }
    .tax-strategy {
        background-color: #f9f0ff;
        border-left: 5px solid #722ed1;
        padding: 10px;
        margin-bottom: 10px;
        color: #4b0082;
    }
    .strategy-card {
        border: 1px solid #ddd;
        border-radius: 5px;
        padding: 15px;
        margin-bottom: 15px;
        background-color: #f5f5f5;
        color: #333;
    }
    .strategy-card h4 {
        margin-top: 0;
        color: #1890ff;
    }
    .strategy-savings {
        font-weight: bold;
        color: #52c41a;
    }
    .strategy-steps {
        margin-top: 10px;
        color: #333;
    }
    .stage-indicator {
        display: flex;
        justify-content: space-between;
        margin-bottom: 20px;
    }
    .stage-step {
        flex: 1;
        text-align: center;
        padding: 10px;
        border-radius: 5px;
        margin: 0 5px;
    }
    .stage-active {
        background-color: #1890ff;
        color: white;
        font-weight: bold;
    }
    .stage-complete {
        background-color: #52c41a;
        color: white;
    }
    .stage-inactive {
        background-color: #f0f0f0;
        color: #666;
    }
</style>
""", unsafe_allow_html=True)

# App header
st.title("📊 Tax Scenario Assistant")

# Stage indicator bar
col1, col2, col3 = st.columns(3)
with col1:
    if st.session_state.current_stage == "question_generation":
        st.markdown('<div class="stage-step stage-active">Agent 1: Question Generation</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="stage-step stage-complete">Agent 1: Question Generation</div>', unsafe_allow_html=True)

with col2:
    if st.session_state.current_stage == "validation":
        st.markdown('<div class="stage-step stage-active">Agent 2: Response Validation</div>', unsafe_allow_html=True)
    elif st.session_state.current_stage == "question_generation":
        st.markdown('<div class="stage-step stage-inactive">Agent 2: Response Validation</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="stage-step stage-complete">Agent 2: Response Validation</div>', unsafe_allow_html=True)

with col3:
    if st.session_state.current_stage == "json_generation":
        st.markdown('<div class="stage-step stage-active">Agent 3: JSON Generation</div>', unsafe_allow_html=True)
    elif st.session_state.current_stage == "question_generation" or st.session_state.current_stage == "validation":
        st.markdown('<div class="stage-step stage-inactive">Agent 3: JSON Generation</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="stage-step stage-complete">Agent 3: JSON Generation</div>', unsafe_allow_html=True)

# Main interaction area
if st.session_state.current_stage == "json_generation":
    st.subheader("Tax Analysis Results")
    
    # Agent 1 conversation section at the top
    st.markdown('<div class="agent-header agent1">📋 Questions & Responses Summary</div>', unsafe_allow_html=True)
    
    # Remove unnecessary outer container and use Streamlit's native layout
    # Only show the Q&A summary if there is content
    if st.session_state.conversation_history:
        #print(st.session_state.conversation_history)
        question_count = 0
        current_question = None
        with st.container():
            for entry in st.session_state.conversation_history:
                # Stop displaying when we reach Agent 3 responses
                if "Agent 3" in entry.get("message", ""):
                    break
                if entry["role"] == "agent" and not ("Agent 3" in entry.get("message", "")):
                    if "Here are the questions" in entry.get("message", "") or any(entry.get("message", "")[:20].strip().startswith(f"{i}.") for i in range(1, 50)):
                        questions = entry["message"].split("\n")
                        for q in questions:
                            if any(q.strip().startswith(f"{i}.") for i in range(1, 50)):
                                #question_count += 1
                                display_q = q.strip()
                                if len(display_q) > 80:
                                    display_q = display_q[:80] + "..."
                                #st.markdown(f"**Q{question_count}:** {display_q}")
                    else:
                        current_question = entry["message"]
                        question_count += 1
                        display_q = current_question
                        # if len(display_q) > 80:
                        #     display_q = display_q[:80] + "..."
                        st.markdown(f"{display_q}")
                elif entry["role"] == "user":
                    response_text = entry["message"]
                    # if len(response_text) > 100:
                    #     response_text = response_text[:100] + "..."
                    st.markdown(f"**User:** {response_text}")
                    st.markdown("---")
    else:
        st.info("No conversation history available.")
    
    # Agent 3 analysis section below
    st.markdown('<div class="agent-header agent3">🎯 Tax Strategy Analysis</div>', unsafe_allow_html=True)
    
    # Process tax strategies if not already done
    if st.session_state.final_json and not st.session_state.tax_strategies_processed:
        try:
            with st.spinner("🔍 Analyzing your tax strategies..."):
                # Parse the JSON if it's a string
                json_data = st.session_state.final_json
                if isinstance(json_data, str):
                    try:
                        json_data = json.loads(json_data)
                    except json.JSONDecodeError:
                        # Try to clean the JSON string
                        json_text = json_data.strip()
                        if json_text.startswith("```json"):
                            json_text = json_text.split("```json", 1)[1]
                        if json_text.startswith("```"):
                            json_text = json_text.split("```", 1)[1]
                        if "```" in json_text:
                            json_text = json_text.split("```")[0]
                        json_text = json_text.strip()
                        json_data = json.loads(json_text)

                # Process the JSON data with Tax Strategies Agent
                tax_strategies_result = tax_strategies_agent.process_tax_scenario(json_data)
                st.session_state.tax_strategies_result = tax_strategies_result
                st.session_state.tax_strategies_processed = True

                # Add to conversation history
                st.session_state.conversation_history.append({
                    "role": "agent",
                    "message": "**Agent 3**: I've analyzed your tax scenario and identified optimal tax strategies."
                })
        except Exception as e:
            st.error(f"❌ Error processing tax strategies: {str(e)}")
    
    # Display tax strategies analysis in a full-width layout
    if st.session_state.tax_strategies_processed and st.session_state.tax_strategies_result:
        result = st.session_state.tax_strategies_result
        #print(result)
        
        # Create tabs for better organization of Agent 3 content
        analysis_tab, strategies_tab, export_tab = st.tabs(["📊 Analysis", "📋 Strategy Details", "💾 Export"])
        
        with analysis_tab:
            # Display human-readable tax analysis in a scrollable container only if there is content
            if "tax_analysis" in result and result["tax_analysis"] and result["tax_analysis"].strip():
                # Remove unnecessary outer <div> container
                analysis_text = result["tax_analysis"]
                sections = analysis_text.split("##")
                for i, section in enumerate(sections):
                    if section.strip():
                        if i == 0:
                            st.markdown(f"## {section.strip()}")
                        else:
                            lines = section.strip().split("\n")
                            if lines:
                                section_title = lines[0].strip()
                                section_content = "\n".join(lines[1:]).strip()
                                if "Strategy" in section_title:
                                    with st.expander(f"📊 {section_title}", expanded=True):
                                        st.markdown(section_content)
                                elif "Client Overview" in section_title:
                                    st.markdown(f"### 👤 {section_title}")
                                    st.markdown(section_content)
                                elif "Summary" in section_title:
                                    st.markdown(f"### 📈 {section_title}")
                                    st.markdown(section_content)
                                else:
                                    st.markdown(f"### {section_title}")
                                    st.markdown(section_content)
            else:
                st.info("Tax analysis not available.")
        
        with strategies_tab:
            # Display detailed strategy information
            if "applicable_strategies" in result and result["applicable_strategies"]:
                strategies = result["applicable_strategies"]
                
                if isinstance(strategies, list) and len(strategies) > 0:
                    st.markdown("### 📋 Detailed Strategy Information")
                    
                    for i, strategy in enumerate(strategies, 1):
                        if isinstance(strategy, dict) and "title" in strategy:
                            with st.expander(f"Strategy {i}: {strategy.get('title', 'Strategy')}", expanded=False):
                                
                                # Create two columns for strategy details
                                col_a, col_b = st.columns(2)
                                
                                with col_a:
                                    st.markdown(f"**Relevance Score**: {strategy.get('relevance_score', 'N/A')}/10")
                                    st.markdown("**Strategy Details**:")
                                    st.markdown(strategy.get('details', 'No details available'))
                                
                                with col_b:
                                    # Show pitfalls if available
                                    if strategy.get('pitfalls'):
                                        st.markdown("**⚠️ Common Pitfalls to Avoid**:")
                                        st.markdown(strategy['pitfalls'])
                                
                                if i < len(strategies):
                                    st.markdown("---")
            else:
                st.info("No specific strategies identified.")
        
        with export_tab:
            # Export and action buttons
            st.markdown("### 💾 Export Options")
            
            # Create action buttons in columns
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Download analysis button
                if "tax_analysis" in result and result["tax_analysis"]:
                    st.download_button(
                        label="📄 Download Analysis",
                        data=result["tax_analysis"],
                        file_name="tax_strategy_analysis.txt",
                        mime="text/plain",
                        use_container_width=True
                    )
            
            with col2:
                # Download JSON button
                if st.session_state.final_json:
                    try:
                        if isinstance(st.session_state.final_json, str):
                            json_data = json.loads(st.session_state.final_json)
                        else:
                            json_data = st.session_state.final_json
                        pretty_json = json.dumps(json_data, indent=2)
                    except:
                        pretty_json = str(st.session_state.final_json)
                    
                    st.download_button(
                        label="📋 Download JSON",
                        data=pretty_json,
                        file_name="tax_scenario.json",
                        mime="application/json",
                        use_container_width=True
                    )
            
            with col3:
                # Proceed to Agent 2 button
                if st.button("🔍 Analyze with Agent 2", key="to_agent2_from_agent3", use_container_width=True):
                    st.session_state.switch_to_agent2 = True
                    st.session_state.agent2_json_payload = pretty_json if 'pretty_json' in locals() else st.session_state.final_json
                    
                    if "agent2_user_scenario_override" in st.session_state:
                        del st.session_state["agent2_user_scenario_override"]
                    st.rerun()
            
            # Display JSON in export tab as well
            if st.session_state.final_json:
                st.markdown("---")
                st.markdown("### 📋 JSON Data Preview")
                
                try:
                    if isinstance(st.session_state.final_json, str):
                        json_data = json.loads(st.session_state.final_json)
                        pretty_json = json.dumps(json_data, indent=2)
                    else:
                        pretty_json = json.dumps(st.session_state.final_json, indent=2)
                except:
                    pretty_json = str(st.session_state.final_json)
                
                st.code(pretty_json, language="json")
        
        # --- AUTO-LOAD AGENT 2 AFTER AGENT 3 COMPLETES ---
        # Set switch_to_agent2 and rerun after Agent 3 finishes
        if not st.session_state.get("switch_to_agent2", False):
            # Prepare JSON payload for Agent 2
            if st.session_state.final_json:
                try:
                    if isinstance(st.session_state.final_json, str):
                        json_data = json.loads(st.session_state.final_json)
                    else:
                        json_data = st.session_state.final_json
                    pretty_json = json.dumps(json_data, indent=2)
                except:
                    pretty_json = str(st.session_state.final_json)
                st.session_state.switch_to_agent2 = True
                st.session_state.agent2_json_payload = pretty_json
                st.rerun()
    else:
        # Show loading state or instructions
        st.info("🔄 Waiting for tax strategy analysis...")
        
        if st.session_state.final_json:
            st.markdown("### Ready to Analyze")
            st.markdown("Your tax scenario has been structured. Click below to start the analysis.")
            
            if st.button("🚀 Start Tax Strategy Analysis", use_container_width=True):
                st.rerun()

# --- REMOVE the prominent button for Agent 2 ---
# (Remove the block that starts with: if st.session_state.tax_strategies_processed and st.session_state.tax_strategies_result:)
else:
    # For other stages, use the original layout
    main_col1, main_col2 = st.columns([2, 1])

    with main_col1:
        # Display conversation history with clear agent attribution
        st.subheader("Conversation")
        if st.session_state.conversation_history:
            # Create a container with scrollable height
            chat_container = st.container()
            with chat_container:
                # Add separators between different agent sections
                current_agent = "Agent 1"
                last_agent = None
                
                for i, entry in enumerate(st.session_state.conversation_history):
                    # Add visual separator when transitioning between agents
                    if i > 0 and entry["role"] == "agent" and "**Agent" in entry.get("message", ""):
                        agent_marker = entry["message"].split("**")[1].split(" ")[0]
                        if agent_marker != last_agent:
                            st.markdown("---")
                            last_agent = agent_marker
                    
                    if entry["role"] == "user":
                        st.markdown(f"**You**: {entry['message']}")
                    else:
                        # Check if this message has an agent identifier
                        if "**Agent" in entry["message"]:
                            # Message already has agent identifier, display as is
                            st.markdown(f"**Assistant**: {entry['message']}")
                        elif st.session_state.current_stage == "validation" and current_agent == "Agent 1":
                            # First response in validation stage is from Agent 1
                            st.markdown(f"**Assistant (Agent 1)**: {entry['message']}")
                            current_agent = "Agent 2"
                        elif st.session_state.current_stage == "validation":
                            # Subsequent responses in validation stage are from Agent 2
                            st.markdown(f"**Assistant (Agent 2)**: {entry['message']}")
                        elif st.session_state.current_stage == "json_generation":
                            # Responses in json_generation stage are from Agent 3
                            st.markdown(f"**Assistant (Agent 3)**: {entry['message']}")
                        else:
                            # Default case
                            st.markdown(f"**Assistant**: {entry['message']}")
        else:
            st.info("Start by describing your tax scenario below.")

    with main_col2:
        # Right sidebar for current stage info and actions
        if st.session_state.current_stage == "question_generation":
            st.markdown('<div class="agent-header agent1">Agent 1: Question Generation</div>', unsafe_allow_html=True)
            st.markdown("""
            This agent will analyze your tax scenario and generate a comprehensive list of questions needed for proper tax filing.
            """)
            
            # Create tabs for different scenario input methods
            scenario_tab1, scenario_tab2 = st.tabs(["Enter Scenario", "Upload Scenario File"])
            
            with scenario_tab1:
                if not st.session_state.scenario_submitted:
                    # Initial scenario input
                    scenario = st.text_area(
                        "Describe your tax scenario:",
                        value=st.session_state.user_scenario,
                        height=150,
                        key="scenario_input"
                    )
                    
                    submit_scenario = st.button("Generate Questions", key="submit_scenario", use_container_width=True)
                    
                    if submit_scenario and scenario.strip():
                        st.session_state.user_scenario = scenario
                        st.session_state.scenario_submitted = True
                        
                        # Add to conversation history
                        st.session_state.conversation_history.append({
                            "role": "user",
                            "message": scenario
                        })
                        
                        # Get questions from Agent 1
                        with st.spinner("Agent 1 is analyzing your scenario..."):
                            response = agent.clarify_and_structure(scenario)
                            
                        if response["status"] == "needs_clarification":
                            # Store the question list and display
                            st.session_state.question_list = response["response"]
                            st.session_state.conversation_history.append({
                                "role": "agent",
                                "message": "Here are the questions I'll need answered to properly file your taxes:\n\n" + response["response"]
                            })
                            
                            # Extract questions for future use
                            questions = response["response"].split("\n")
                            st.session_state.all_questions = [q.strip() for q in questions if q.strip() and any(q.strip().startswith(str(i)) for i in range(1, 30))]
                            
                            # Update the current stage in both agent and session state
                            st.session_state.current_stage = "validation"
                            
                        st.rerun()
            
            with scenario_tab2:
                st.markdown("### Upload a file with your tax scenario")
                scenario_file = st.file_uploader("Upload your scenario", type=["txt"], key="scenario_file")
                
                if scenario_file is not None and not st.session_state.scenario_submitted:
                    # Read the scenario from the file
                    scenario_content = scenario_file.getvalue().decode("utf-8")
                    if scenario_content.strip():
                        st.success("Scenario loaded from file!")
                        st.text_area("Scenario preview:", value=scenario_content, height=100, disabled=True)
                        
                        submit_scenario_file = st.button("Generate Questions from File", use_container_width=True)
                        
                        if submit_scenario_file:
                            st.session_state.user_scenario = scenario_content
                            st.session_state.scenario_submitted = True
                            
                            # Add to conversation history
                            st.session_state.conversation_history.append({
                                "role": "user",
                                "message": scenario_content
                            })
                            
                            # Get questions from Agent 1
                            with st.spinner("Agent 1 is analyzing your scenario..."):
                                response = agent.clarify_and_structure(scenario_content)
                                
                            if response["status"] == "needs_clarification":
                                # Store the question list and display
                                st.session_state.question_list = response["response"]
                                st.session_state.conversation_history.append({
                                    "role": "agent",
                                    "message": "Here are the questions I'll need answered to properly file your taxes:\n\n" + response["response"]
                                })
                                
                                # Extract questions for future use
                                questions = response["response"].split("\n")
                                st.session_state.all_questions = [q.strip() for q in questions if q.strip() and any(q.strip().startswith(str(i)) for i in range(1, 30))]
                                
                                # Update the current stage in both agent and session state
                                st.session_state.current_stage = "validation"
                                

        elif st.session_state.current_stage == "validation":
            st.markdown('<div class="agent-header agent2">Agent 2: Response Validation</div>', unsafe_allow_html=True)
            st.markdown("""
            This agent validates your answers and determines if more information is needed.
            """)
            
            # Create tabs for different answer methods
            tab1, tab2 = st.tabs(["Answer Individually", "Upload Answers File"])
            
            with tab1:
                # Show the question list for reference
                with st.expander("Review All Questions", expanded=False):
                    st.markdown(st.session_state.question_list)
                
                # Get user's reply to individual questions
                user_reply = st.text_area("Your answer:", key="user_reply")
                submit_reply = st.button("Submit Answer", key="submit_answer", use_container_width=True)
                
                if submit_reply and user_reply.strip():
                    # Add user's reply to history
                    st.session_state.clarifications.append(user_reply)
                    st.session_state.conversation_history.append({
                        "role": "user",
                        "message": user_reply
                    })
                    
                    # Get next response from Agent 2
                    with st.spinner("Agent 2 is validating your response..."):
                        response = agent.clarify_and_structure(
                            st.session_state.user_scenario, 
                            st.session_state.clarifications
                        )
                    
                    if response["status"] == "needs_clarification":
                        # Agent 2 needs more information - ask another question
                        next_question = response["response"]
                        st.session_state.clarifications.append(next_question)
                        st.session_state.conversation_history.append({
                            "role": "agent",
                            "message": next_question
                        })
                    else:
                        # Agent 2 has enough information - move to Agent 3
                        st.session_state.final_json = response["response"]
                        st.session_state.conversation_history.append({
                            "role": "agent",
                            "message": "Thank you for providing all the necessary information. Here's a structured representation of your tax scenario:"
                        })
                        st.session_state.current_stage = "json_generation"
                    
                    st.rerun()
            
            with tab2:
                st.markdown("### Upload a text file with your answers to all questions")
                
                # Provide a sample file for download
                if st.session_state.all_questions:
                    sample_file = generate_sample_answer_file(st.session_state.all_questions)
                    st.download_button(
                        "Download Answer Template",
                        sample_file,
                        file_name="tax_answers_template.txt",
                        mime="text/plain",
                        help="Download this template, fill in your answers, and upload it below."
                    )
                
                # File uploader
                uploaded_file = st.file_uploader("Upload your answers file", type=["txt"], key="answers_file")
                
                if uploaded_file is not None:
                    # Process the uploaded file
                    answers = process_answers_file(uploaded_file)
                    
                    if len(answers) > 0:
                        st.success(f"Successfully extracted {len(answers)} answers from your file!")
                        
                        # Store answers in session state
                        st.session_state.file_answers = answers
                        
                        # Show preview of extracted answers
                        with st.expander("Preview of extracted answers", expanded=False):
                            for i, answer in enumerate(answers[:5]):  # Show first 5 answers
                                st.markdown(f"**Answer {i+1}:** {answer[:100]}{'...' if len(answer) > 100 else ''}")
                            if len(answers) > 5:
                                st.markdown(f"...and {len(answers) - 5} more answers")
                        
                        # Submit button
                        if st.button("Submit All Answers", 
                                   key="submit_all_answers",
                                   use_container_width=True,
                                   type="primary"):
                            st.session_state.submit_clicked = True
                            st.rerun()
                    else:
                        st.error("No valid answers found in the uploaded file. Please check the file format.")

# Process the submission in a separate code block
if st.session_state.submit_clicked and st.session_state.file_answers:
    answers = st.session_state.file_answers
    st.info("Processing your answers...")
    
    # Update conversation history with all answers
    combined_clarifications = []
    
    for i, answer in enumerate(answers):
        question_text = f"Question {i+1}"
        if i < len(st.session_state.all_questions):
            question_text = st.session_state.all_questions[i]
        
        # Add question and answer to clarifications
        combined_clarifications.append(question_text)
        combined_clarifications.append(answer)
        
        # Add to conversation history with clear agent attribution
        st.session_state.conversation_history.append({
            "role": "agent",
            "message": f"**Agent 1 Question**: {question_text}"
        })
        
        st.session_state.conversation_history.append({
            "role": "user",
            "message": answer
        })
    # Process all answers with Agent 2
    with st.spinner("Agent 2 is validating all your answers..."):
        try:
            # Pass memory from Agent 1 to Agent 2 by maintaining the same scenario
            response = agent.clarify_and_structure(
                st.session_state.user_scenario,
                combined_clarifications
            )
            
            if response["status"] == "complete":
                # Final JSON response - move to Agent 3
                st.session_state.final_json = response["response"]
                st.session_state.conversation_history.append({
                    "role": "agent",
                    "message": "**Agent 2**: All necessary information provided. Here's your structured tax scenario."
                })
                st.session_state.current_stage = "json_generation"
            else:
                # Need more information - clearly indicate this is from Agent 2
                st.session_state.clarifications = combined_clarifications
                st.session_state.clarifications.append(response["response"])
                
                next_question = response["response"]
                
                st.session_state.conversation_history.append({
                    "role": "agent",
                    "message": f"**Agent 2**: Thanks for your answers. I need one more piece of information: {next_question}"
                })
            
            # Reset the submit flag and clear file answers to prevent re-processing
            st.session_state.submit_clicked = False
            st.session_state.file_answers = None
            # Force a rerun to update the UI
            st.rerun()
        except Exception as e:
            st.error(f"Error processing answers: {str(e)}")
            st.session_state.submit_clicked = False
            st.session_state.file_answers = None

# --- Render Agent 2 UI if switch_to_agent2 is set ---
if st.session_state.get("switch_to_agent2", False):
    st.markdown("---")
    st.header("Agent 2: Baseline Tax Comparision")
    import agent2.app # Ensure agent2.app is imported

    # Directly call Agent 2's main function without preparing or passing a JSON payload
    agent2.app.main(set_page_config=False)

    # Optionally, add a button to go back to Agent 1
    if st.button("Back to Agent 1", key="back_to_agent1"):
        st.session_state.switch_to_agent2 = False
        # Clear Agent 2 specific states if needed when going back
        if "agent2_user_scenario_override" in st.session_state:
            del st.session_state["agent2_user_scenario_override"]
        if "uploaded_scenario_auto" in st.session_state: # Clean up old state if any
            del st.session_state["uploaded_scenario_auto"]
        st.rerun()
