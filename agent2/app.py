import streamlit as st
import datetime
from agent2.utils.tax_file_reader import read_tax_calculation_file
from agent2.utils.pdf_helper import display_pdf
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Move this function outside the module scope and rename it to avoid showing the function name
@st.cache_resource(show_spinner=False)  # Hide the "Running..." message
def _get_cached_tax_calculation():
    return read_tax_calculation_file("base_tax_calculation.txt")

def main(default_scenario_from_agent1=None, set_page_config=True):
    """Main function that can be called from other modules or run directly"""
    # Set Streamlit page config only if requested (for standalone mode)
    if set_page_config:
        st.set_page_config(page_title="Agent 2", layout="wide")

    # Display header
    st.header("Tax Calculation Analysis")

    # Hide the cache access by using session state differently
    if "baseline_tax_calculation" not in st.session_state:
        # Use an empty spinner to hide the "Running..." message
        with st.spinner("💰 Loading tax calculation..."):
            st.session_state["baseline_tax_calculation"] = _get_cached_tax_calculation()
        # Show our own loading message after the cache access
        st.success("✅ Tax calculation loaded successfully")
    
    tax_calculation = st.session_state["baseline_tax_calculation"]

    if "error" not in tax_calculation:
        # Remove success message since we've already shown it above
        
        if "full_text" in tax_calculation:
            # Remove tab structure and display only Enhanced HTML View
            with st.container():
                # Add required CSS with improved color scheme
                st.markdown("""
                <style>
                .tax-html-container {
                    background-color: #f8f9fa;
                    padding: 25px;
                    border-radius: 8px;
                    border: 1px solid #d1e7dd;
                    color: #333333;
                    font-family: 'Segoe UI', Arial, sans-serif;
                    line-height: 1.6;
                    box-shadow: 0 2px 6px rgba(0,0,0,0.05);
                }
                /* Improved heading styles */
                .tax-html-container h1 {
                    color: #0d6efd;
                    margin-top: 24px;
                    margin-bottom: 16px;
                    font-size: 1.8em;
                    border-bottom: 1px solid #dee2e6;
                    padding-bottom: 8px;
                }
                .tax-html-container h2 {
                    color: #198754;
                    margin-top: 20px;
                    margin-bottom: 12px;
                    font-size: 1.5em;
                }
                .tax-html-container h3 {
                    color: #6f42c1;
                    margin-top: 18px;
                    margin-bottom: 10px;
                    font-size: 1.3em;
                }
                /* Enhanced table styles */
                .tax-html-container table {
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                }
                .tax-html-container th {
                    background-color: #e7f1ff;
                    border: 1px solid #b6d4fe;
                    color: #084298;
                    padding: 12px;
                    text-align: left;
                    font-weight: bold;
                }
                .tax-html-container td {
                    border: 1px solid #dee2e6;
                    padding: 10px;
                    text-align: left;
                }
                .tax-html-container tr:nth-child(even) {
                    background-color: #f2f8ff;
                }
                .tax-html-container tr:hover {
                    background-color: #e9ecef;
                }
                /* Special formatting for calculations */
                .tax-html-container .calculation {
                    background-color: #f1f8e9;
                    padding: 15px;
                    border-left: 4px solid #81c784;
                    margin: 15px 0;
                }
                /* Number formatting */
                .tax-html-container .number {
                    font-weight: bold;
                    color: #0d6efd;
                }
                /* Section formatting */
                .tax-html-container section {
                    margin-bottom: 25px;
                    padding-bottom: 20px;
                    border-bottom: 1px dashed #dee2e6;
                }
                /* Summary section */
                .tax-html-container .summary {
                    background-color: #e8f5e9;
                    padding: 16px;
                    border-radius: 6px;
                    border: 1px solid #c8e6c9;
                    margin-top: 25px;
                }
                </style>
                """, unsafe_allow_html=True)
                
                # Directly render the HTML content
                if "html_content" in tax_calculation:
                    html_content = tax_calculation["html_content"]
                    if not html_content.strip().startswith('<'):
                        html_content = f"<div>{html_content}</div>"
                    st.components.v1.html(
                        f'<div class="tax-html-container">{html_content}</div>', 
                        height=600,
                        scrolling=True
                    )
                else:
                    st.warning("HTML view is not available for this calculation.")
                    st.download_button(
                        label="📥 Download Tax Calculation",
                        data=tax_calculation["full_text"],
                        file_name=f"tax_calculation_{datetime.datetime.now().strftime('%Y%m%d')}.txt",
                        mime="text/plain"
                    )

        # Document comparison functionality
        st.markdown("---")
        st.subheader("📊 Compare with Another Document")
        st.write("Upload any tax document to compare with the baseline calculation.")
        previous_tax_return = st.file_uploader("Upload document for comparison", 
                                        type=["pdf", "json", "docx", "txt"], 
                                        key="previous_tax_return")

        # If document uploaded, generate comparison
        if previous_tax_return is not None:
            # Process the uploaded document - not wrapped in spinner since this is usually quick
            from agent2.utils.tax_comparison import parse_previous_tax_return, generate_tax_comparison
            uploaded_document_data = parse_previous_tax_return(previous_tax_return)

            if "error" not in uploaded_document_data:
                client_data = {"name": "Tax Client", "tax_year": datetime.datetime.now().year}
                
                # Add spinner specifically for the OpenAI document comparison call
                with st.spinner("🤖 Calling OpenAI for detailed tax document comparison..."):
                    comparison_result = generate_tax_comparison(
                        previous_year_data=uploaded_document_data,
                        current_year_data=tax_calculation,
                        client_data=client_data
                    )

                if "error" not in comparison_result:
                    st.success("✅ Document comparison completed!")
                    with open(comparison_result["report_path"], "rb") as file:
                        st.download_button(
                            label="📥 Download Comparison Report (PDF)",
                            data=file,
                            file_name=f"Tax_Document_Comparison_{datetime.datetime.now().strftime('%Y%m%d')}.pdf",
                            mime="application/pdf"
                        )
                    try:
                        display_pdf(comparison_result["report_path"])
                    except Exception as e:
                        st.warning(f"Unable to display PDF in browser: {str(e)}. Please download using the button above.")
                else:
                    st.error(f"Error generating comparison: {comparison_result['error']}")
            else:
                st.error(f"Error processing uploaded document: {uploaded_document_data['error']}")
    else:
        st.error(f"Error loading tax calculation: {tax_calculation.get('error')}")

    # Add footer
    st.markdown("---")
    st.markdown("Agent 2 powered by OpenAI")

# This allows the script to be run directly as a standalone app
if __name__ == "__main__":
    main(set_page_config=True)
