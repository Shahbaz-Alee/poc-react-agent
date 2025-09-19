import streamlit as st
import json
import base64

def display_report(structured_output, output_paths):
    st.header("📊 Tax Comparison Report")
    
    # Display reasoning if available
    if isinstance(structured_output, dict) and "reasoning" in structured_output:
        st.subheader("🧠 AI Reasoning")
        with st.expander("View AI's Analysis and Reasoning", expanded=True):
            st.markdown(structured_output["reasoning"])
        # Use the structured_data for the rest of the display
        data_for_display = structured_output["structured_data"]
    else:
        # Legacy format or sample data
        data_for_display = structured_output
    
    # Display PDF embedded in the UI
    st.subheader("📄 PDF Report")
    display_pdf(output_paths['pdf'])
    
    # Download section
    st.subheader("📥 Download Files")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.download_button("⬇️ Download PDF", open(output_paths['pdf'], "rb"), file_name="Tax_Comparison_Report.pdf")
    with col2:
        st.download_button("⬇️ Download Excel", open(output_paths['excel'], "rb"), file_name="Tax_Comparison.xlsx")
    with col3:
        st.download_button("⬇️ Download JSON", open(output_paths['json'], "rb"), file_name="Tax_Comparison.json")
    
    # Make JSON output collapsible
    with st.expander("View Raw JSON Data"):
        st.json(data_for_display)

def display_pdf(pdf_file):
    """Display a PDF file directly in the Streamlit app with a fallback download link"""
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
    
    # Provide a fallback message with a download link
    st.caption("If the PDF doesn't display correctly, you can download it using the button below.")
