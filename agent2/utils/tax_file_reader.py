import os
import re
import logging
import datetime
from pathlib import Path
from agent2.utils.html_conversion import convert_tax_calculation_to_html, get_clean_html_for_streamlit

logger = logging.getLogger(__name__)

def read_tax_calculation_file(file_path="base_tax_calculation.txt"):
    """
    Read the tax calculation from a text file.
    
    Args:
        file_path (str): Path to the tax calculation file
        
    Returns:
        dict: Processed tax information and full text from the file
    """
    try:
        # Check if the file exists
        if not os.path.exists(file_path):
            logger.error(f"Tax calculation file not found at: {file_path}")
            return {"error": f"Tax calculation file not found at: {file_path}"}
        
        # Read the file content
        with open(file_path, "r", encoding="utf-8") as f:
            file_content = f.read()
        
        # Create the result dictionary with the full file content
        result = {
            "full_text": file_content,
            "formatted_text": file_content
        }
        
        # Convert the text to HTML using OpenAI
        html_content = convert_tax_calculation_to_html(file_content)
        result["html_content"] = html_content
        
        # Add a clean version specifically for Streamlit
        result["streamlit_html"] = get_clean_html_for_streamlit(html_content)
        
        # Process the file content to extract tax information for calculations
        # This is kept for potential calculation needs, but the display will use the full text
        extracted_info = extract_tax_info_from_file(file_content)
        
        # Merge the extracted info with our result
        result.update(extracted_info)
        
        return result
    
    except Exception as e:
        logger.error(f"Error processing tax calculation file: {str(e)}")
        return {"error": f"Error processing tax calculation file: {str(e)}"}

def extract_tax_info_from_file(file_content):
    """
    Extract tax calculation information from the file content.
    Keep this for compatibility with existing code that might need these values.
    
    Args:
        file_content (str): Content of the tax calculation file
        
    Returns:
        dict: Structured tax information
    """
    # Initialize the result dictionary with default values
    result = {
        "income": 0,
        "taxable_income": 0,
        "adjusted_gross_income": 0,
        "deductions": 0,
        "federal_effective_rate": 0,
        "federal_taxes_owed": 0,
        "region_taxes_owed": 0,
        "fica_total": 0,
        "total_taxes_owed": 0,
        "income_after_tax": 0,
        "total_effective_tax_rate": 0,
    }
    
    # Look for key metrics in the file content
    try:
        # Extract total income
        total_income_match = re.search(r"Total Income:?\s*\$?([\d,\.]+)", file_content)
        if total_income_match:
            result["income"] = float(total_income_match.group(1).replace(",", ""))
        
        # Extract AGI
        agi_match = re.search(r"Adjusted Gross Income \(AGI\):?\s*\$?([\d,\.]+)", file_content)
        if agi_match:
            result["adjusted_gross_income"] = float(agi_match.group(1).replace(",", ""))
        
        # Extract taxable income
        taxable_income_match = re.search(r"Taxable Income:?\s*\$?([\d,\.]+)", file_content)
        if taxable_income_match:
            result["taxable_income"] = float(taxable_income_match.group(1).replace(",", ""))
        
        # Extract total business expenses/deductions
        deductions_match = re.search(r"Total Business Expenses:?\s*\$?([\d,\.]+)", file_content) or \
                           re.search(r"Total Deductions:?\s*\$?([\d,\.]+)", file_content)
        if deductions_match:
            result["deductions"] = float(deductions_match.group(1).replace(",", ""))
        
        # Extract federal tax
        federal_tax_match = re.search(r"Federal Tax:?\s*\$?([\d,\.]+)", file_content) or \
                            re.search(r"Total Federal Tax:?\s*\$?([\d,\.]+)", file_content)
        if federal_tax_match:
            result["federal_taxes_owed"] = float(federal_tax_match.group(1).replace(",", ""))
        
        # Extract state tax
        state_tax_match = re.search(r"State Tax:?\s*\$?([\d,\.]+)", file_content) or \
                          re.search(r"Total State Tax:?\s*\$?([\d,\.]+)", file_content)
        if state_tax_match:
            result["region_taxes_owed"] = float(state_tax_match.group(1).replace(",", ""))
        
        # Extract FICA taxes
        fica_tax_match = re.search(r"FICA Taxes:?\s*\$?([\d,\.]+)", file_content) or \
                         re.search(r"Total FICA Taxes:?\s*\$?([\d,\.]+)", file_content)
        if fica_tax_match:
            result["fica_total"] = float(fica_tax_match.group(1).replace(",", ""))
        
        # Extract total tax liability
        total_tax_match = re.search(r"Total Tax Liability:?\s*\$?([\d,\.]+)", file_content)
        if total_tax_match:
            result["total_taxes_owed"] = float(total_tax_match.group(1).replace(",", ""))
        
        # Extract effective tax rate
        effective_rate_match = re.search(r"Effective Tax Rate:?\s*([\d\.]+)%", file_content)
        if effective_rate_match:
            result["total_effective_tax_rate"] = float(effective_rate_match.group(1)) / 100  # Convert percentage to decimal
        
        # Calculate income after tax (if we have both income and total tax)
        if result["income"] > 0 and result["total_taxes_owed"] > 0:
            result["income_after_tax"] = result["income"] - result["total_taxes_owed"]
        
        # Calculate federal effective rate if we have federal taxes and income
        if result["federal_taxes_owed"] > 0 and result["income"] > 0:
            result["federal_effective_rate"] = result["federal_taxes_owed"] / result["income"]
            
    except Exception as e:
        logger.warning(f"Error extracting tax info from file: {e}")
        # We'll return whatever we managed to extract
    
    # Return the extracted information
    return result
