import os
import logging
from openai import OpenAI
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()

def convert_tax_calculation_to_html(tax_calculation_text):
    """
    Convert the tax calculation text to HTML format using OpenAI.
    
    Args:
        tax_calculation_text (str): The tax calculation text to convert
        
    Returns:
        str: The HTML representation of the tax calculation
    """
    try:
        # Check if OpenAI API key is available
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error("OpenAI API key not found")
            return f"<pre>{tax_calculation_text}</pre>"  # Fallback to simple pre-formatted HTML
        
        # Initialize OpenAI client
        client = OpenAI(api_key=api_key)
        logger.info("Calling OpenAI to convert tax calculation to HTML...")
        
        # Create prompt for OpenAI with improved HTML structure guidance
        prompt = f"""
        Convert the following tax calculation text to a well-formatted HTML representation.
        Do not change ANY of the content - keep all numbers, calculations, and text exactly the same.
        
        Improve the presentation using these HTML elements and CSS classes:
        - Use <section> tags to group related content
        - Use <h1>, <h2>, <h3> for section titles 
        - Use <p> for text blocks
        - Wrap tables in <div class="table-responsive">
        - Use <table>, <tr>, <th>, <td> for tabular data
        - Use <span class="number"> for important numeric values
        - Wrap calculation blocks in <div class="calculation">...</div>
        - Place summary information in <div class="summary">...</div>
        
        Apply modern formatting while maintaining the exact mathematical values and explanations.
        
        Here's the tax calculation text:
        
        ```
        {tax_calculation_text}
        ```
        
        Return ONLY valid HTML that can be directly embedded in a web page. Don't include any explanations before or after.
        """
        
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an HTML conversion expert who preserves the exact content of tax documents while improving their presentation with HTML."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1  # Lower temperature for more consistent output
        )
        
        # Extract content
        html_content = response.choices[0].message.content.strip()
        
        # Remove any markdown code block formatting if present
        if html_content.startswith("```html"):
            html_content = html_content.split("```html", 1)[1]
        if html_content.startswith("```"):
            html_content = html_content.split("```", 1)[1]
        if "```" in html_content:
            html_content = html_content.split("```")[0]
        html_content = html_content.strip()
        
        # Ensure proper HTML structure for better rendering
        if not html_content.startswith("<!DOCTYPE html>") and not html_content.startswith("<html"):
            # Add a basic HTML structure if missing
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333333; }}
                    /* Additional styling will be applied from app.py */
                </style>
            </head>
            <body>
                {html_content}
            </body>
            </html>
            """
        
        logger.info("Successfully converted tax calculation to HTML")
        return html_content
    
    except Exception as e:
        logger.error(f"Error converting tax calculation to HTML: {str(e)}")
        # Fallback to simple pre-formatted HTML
        return f"<pre>{tax_calculation_text}</pre>"

def get_clean_html_for_streamlit(html_content):
    """
    Clean and prepare HTML content for rendering in Streamlit.
    
    Args:
        html_content (str): Raw HTML content
        
    Returns:
        str: Clean HTML ready for Streamlit rendering
    """
    # Remove DOCTYPE, html, head, and body tags if present
    # Streamlit doesn't need these and they can cause rendering issues
    clean_html = html_content
    
    # Strip out full document structure to keep only the body content
    if "<!DOCTYPE" in clean_html or "<html" in clean_html:
        # Try to extract just the body content
        import re
        body_match = re.search(r'<body[^>]*>(.*?)</body>', clean_html, re.DOTALL)
        if body_match:
            clean_html = body_match.group(1).strip()
    
    # Add our own wrapper div with styling
    clean_html = f"""
    <div style="font-family: Arial, sans-serif; line-height: 1.6; padding: 15px;">
        {clean_html}
    </div>
    """
    
    return clean_html
