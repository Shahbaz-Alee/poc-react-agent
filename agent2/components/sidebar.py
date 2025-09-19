import streamlit as st

def render_sidebar():
    st.sidebar.title("Agent 2")
    st.sidebar.markdown("---")
    st.sidebar.title("Navigation")
    st.sidebar.markdown("Upload a JSON file with tax parameters.")
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("## How to use")
    st.sidebar.markdown("""
    1. Upload your tax parameters JSON file
    2. The system will extract and print required parameters
    3. Required parameters:
       - country (2-letter code, e.g., US, CA)
       - region (state/province code)
       - income (annual amount)
       - filing_status (for US only)
    4. Optional parameters:
       - deductions (total amount)
       - credits (total amount)
       - self_employed (boolean, US only)
    """)
    
    st.sidebar.markdown("---")
    st.sidebar.info("This tool extracts tax calculation parameters from a JSON file and prints them to the terminal.")
