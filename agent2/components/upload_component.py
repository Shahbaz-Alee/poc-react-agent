import streamlit as st
import logging

logger = logging.getLogger(__name__)

def upload_files(default_scenario_from_agent1=None):
    """
    Show file upload widget in main content area and handle file selection logic.
    
    Args:
        default_scenario_from_agent1: File object from Agent 1 (optional)
        
    Returns:
        dict: Dictionary containing file objects and source info
    """
    st.subheader("Upload Tax Files")

    # Key for storing the user's explicit scenario upload within Agent 2's context
    user_override_key = "agent2_user_scenario_override"

    # File uploader widget for scenario JSON - always visible
    user_uploaded_scenario = st.file_uploader(
        "Upload Client Scenario (JSON)",
        type=["json"],
        key="agent2_scenario_uploader_widget"  # Unique key for the widget
    )

    # Handle scenario file logic - prioritize user uploads over default
    if user_uploaded_scenario is not None:
        # User uploaded a new file in this session - use it and store in session state
        st.session_state[user_override_key] = user_uploaded_scenario
        scenario_to_use = user_uploaded_scenario
        scenario_source = "(User uploaded)"
        logger.info(f"Using user uploaded scenario: {getattr(scenario_to_use, 'name', 'user_scenario.json')}")
        
        # Show success message for user upload
        st.success(f"Using scenario: {getattr(scenario_to_use, 'name', 'scenario.json')} {scenario_source}")
        
        return {
            "tax_parameters": scenario_to_use, 
            "source": "user_upload"
        }
    
    # If no new upload, check for previously used file in session state
    elif user_override_key in st.session_state and st.session_state[user_override_key] is not None:
        # Use previously uploaded file
        scenario_to_use = st.session_state[user_override_key]
        scenario_source = "(Previously uploaded)"
        logger.info(f"Using previously uploaded scenario: {getattr(scenario_to_use, 'name', 'previous_scenario.json')}")
        
        # Show success message for previous upload
        st.success(f"Using scenario: {getattr(scenario_to_use, 'name', 'scenario.json')} {scenario_source}")
        
        return {
            "tax_parameters": scenario_to_use,
            "source": "user_upload"
        }
    
    # If no user upload (new or previous), use Agent 1 scenario if available
    elif default_scenario_from_agent1 is not None:
        # Use default from Agent 1
        scenario_to_use = default_scenario_from_agent1
        scenario_source = "(From Agent 1)"
        logger.info(f"Using scenario from Agent 1: {getattr(scenario_to_use, 'name', 'agent1_scenario.json')}")
        
        # Show info about using Agent 1 scenario
        st.success(f"Using scenario: {getattr(scenario_to_use, 'name', 'scenario.json')} {scenario_source}")
        
        return {
            "tax_parameters": scenario_to_use,
            "source": "agent1"
        }
    
    # If no scenario available, provide instructions
    else:
        st.warning("No scenario file available. Please upload a JSON file.")
        return None