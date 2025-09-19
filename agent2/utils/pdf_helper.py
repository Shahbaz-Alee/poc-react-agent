import base64
import streamlit as st
import logging
import os

logger = logging.getLogger(__name__)

def display_pdf(pdf_file):
    """Display a PDF file in the Streamlit app with a fallback download link
    
    Args:
        pdf_file (str): Path to the PDF file
        
    Returns:
        None
    """
    # Make sure the file exists
    if not os.path.exists(pdf_file):
        st.warning(f"PDF file not found: {pdf_file}")
        return
    
    try:
        with open(pdf_file, "rb") as f:
            base64_pdf = base64.b64encode(f.read()).decode('utf-8')
        
        # Embed PDF viewer using an iframe
        pdf_display = f"""
            <iframe
                src="data:application/pdf;base64,{base64_pdf}"
                width="100%"
                height="600"
                type="application/pdf"
            ></iframe>
        """
        st.markdown(pdf_display, unsafe_allow_html=True)
        
        # Provide a fallback message
        st.caption("If the PDF doesn't display correctly in your browser, you can download it using the button below.")
        
    except Exception as e:
        logger.error(f"Error displaying PDF: {str(e)}")
        st.error(f"Error displaying PDF: {str(e)}")
        st.info("Please use the download button below to view the PDF.")
