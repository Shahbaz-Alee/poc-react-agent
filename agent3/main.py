from llama_index.llms.openai import OpenAI
from llama_index.core.agent.react.base import ReActAgent
from llama_index.core.tools import FunctionTool
import json
import logging
import os 
from dotenv import load_dotenv
load_dotenv()
import re

class Tax_Stratigies_Agent:
    def __init__(self, openai_api_key):
        self.llm = OpenAI(api_key=openai_api_key, model="gpt-4o-mini")
        self.tools = [
            FunctionTool.from_defaults(
                fn=self.get_tax_strategies,
                name="get_tax_strategies",
                description="Get top 3 tax strategies for a given tax scenario.",
            ),
            FunctionTool.from_defaults(
                fn=self.apply_tax_strategies,
                name="apply_tax_strategies",
                description="Apply selected tax strategies and calculate estimated taxes using AI.",
            )
        ]
        self.agent = ReActAgent.from_tools(
            llm=self.llm,
            tools=self.tools,
            system_prompt=(
                "You are a tax strategy expert specializing in optimizing tax outcomes for clients. "
                "Your job is to analyze client tax information, identify the top 3 most applicable strategies, "
                "and calculate potential tax savings for each strategy using your tax knowledge."
            ),
            verbose=True,
        )
        
        # Load tax strategies file
        base_dir = os.path.dirname(os.path.abspath(__file__))
        possible_paths = [
            os.path.join(base_dir, "tax_strategies.md"),
            os.path.join(os.path.dirname(base_dir), "tax_strategies.md"),
            "tax_strategies.md"
        ]
        
        self.strategies_file_path = None
        for path in possible_paths:
            if os.path.exists(path):
                self.strategies_file_path = path
                break
        
        if not self.strategies_file_path:
            self.strategies_file_path = os.path.join(base_dir, "tax_strategies.md")
            logging.warning(f"Tax strategies file not found, will try to use: {self.strategies_file_path}")
        
        self._tax_strategies_content = None

    def _load_tax_strategies(self):
        """Load tax strategies from the markdown file."""
        if self._tax_strategies_content is None:
            try:
                with open(self.strategies_file_path, "r", encoding="utf-8") as f:
                    self._tax_strategies_content = f.read()
                    logging.info(f"Successfully loaded tax strategies from {self.strategies_file_path}")
            except FileNotFoundError:
                logging.error(f"Tax strategies file not found at {self.strategies_file_path}")
                self._tax_strategies_content = "No tax strategies available."
                    
        return self._tax_strategies_content

    def _parse_tax_strategies(self, content):
        """Parse the markdown content to extract individual strategies with their pitfalls."""
        strategies = {}
        # Updated pattern to capture strategies and their pitfalls
        strategy_pattern = r"### (Strategy \d+: .+?)\n(.*?)(?=### |$)"
        matches = re.findall(strategy_pattern, content, re.DOTALL)
        
        for title, full_content in matches:
            # Split content into main details and pitfalls
            if "#### Common Pitfalls" in full_content:
                parts = full_content.split("#### Common Pitfalls", 1)
                main_details = parts[0].strip()
                pitfalls = "#### Common Pitfalls" + parts[1].strip()
            else:
                main_details = full_content.strip()
                pitfalls = ""
            
            strategies[title] = {
                "details": main_details,
                "pitfalls": pitfalls
            }
            
        return strategies

    def _clean_json_response(self, response_text):
        """Clean a potential JSON string from markdown code blocks and other formatting."""
        cleaned_text = response_text.strip()
        
        if cleaned_text.startswith("```json"):
            cleaned_text = cleaned_text.split("```json", 1)[1]
        elif cleaned_text.startswith("```"):
            cleaned_text = cleaned_text.split("```", 1)[1]
        
        if "```" in cleaned_text:
            cleaned_text = cleaned_text.split("```")[0]
        
        return cleaned_text.strip()

    def get_tax_strategies(self, json_input):
        """
        Tool 1: Identify top 3 applicable tax strategies based on client data.
        
        Args:
            json_input (str): JSON string containing client tax information
            
        Returns:
            list: List of top 3 applicable tax strategies with details and pitfalls
        """
        tax_strategies_content = self._load_tax_strategies()
        parsed_strategies = self._parse_tax_strategies(tax_strategies_content)
        
        try:
            if isinstance(json_input, str):
                client_data = json.loads(json_input)
            else:
                client_data = json_input
        except json.JSONDecodeError:
            return []
        
        if not parsed_strategies:
            logging.warning("No tax strategies loaded from file")
            return []
        
        prompt = f"""
        You are a tax strategy expert. Based on the client's tax information, identify the most relevant tax strategies.
        
        Client Tax Information:
        {json.dumps(client_data, indent=2)}
        
        Available Tax Strategies (titles only):
        {json.dumps(list(parsed_strategies.keys()), indent=2)}
        
        For each strategy, evaluate its relevance to this client's situation on a scale of 1-10.
        Return your answer as a JSON object with strategy titles as keys and relevance scores as values.
        Example:
        {{
            "Strategy 1: New Side Business and Potential Deductions": 8,
            "Strategy 2: Converting a Primary Residence to a Rental Property": 3
        }}
        
        Include only strategies with a relevance score of 5 or higher.
        """
        
        response = self.llm.complete(prompt)
        cleaned_response = self._clean_json_response(response.text)
        
        try:
            scored_strategies = json.loads(cleaned_response)
            sorted_strategies = {k: v for k, v in sorted(scored_strategies.items(), key=lambda item: item[1], reverse=True)}
            top_strategies = {k: v for k, v in sorted_strategies.items() if v >= 5}
            
            # Limit to top 3 strategies and include pitfalls
            strategies_with_details = []
            count = 0
            for strategy_title in top_strategies.keys():
                if count >= 3:
                    break
                if strategy_title in parsed_strategies:
                    strategy_data = parsed_strategies[strategy_title]
                    strategies_with_details.append({
                        "title": strategy_title,
                        "relevance_score": top_strategies[strategy_title],
                        "details": strategy_data["details"],
                        "pitfalls": strategy_data["pitfalls"]
                    })
                    count += 1
            
            return strategies_with_details
            
        except json.JSONDecodeError:
            logging.error(f"Failed to parse JSON from response: {response.text}")            
            # Try extracting JSON pattern
            try:
                json_pattern = r'\{[\s\S]*\}'
                match = re.search(json_pattern, response.text)
                if match:
                    json_text = match.group(0)
                    scored_strategies = json.loads(json_text)
                    sorted_strategies = {k: v for k, v in sorted(scored_strategies.items(), key=lambda item: item[1], reverse=True)}
                    top_strategies = {k: v for k, v in sorted_strategies.items() if v >= 5}
                    
                    strategies_with_details = []
                    count = 0
                    for strategy_title in top_strategies.keys():
                        if count >= 3:
                            break
                        if strategy_title in parsed_strategies:
                            strategies_with_details.append({
                                "title": strategy_title,
                                "relevance_score": top_strategies[strategy_title],
                                "details": parsed_strategies[strategy_title]
                            })
                            count += 1
                    
                    return strategies_with_details
            except:
                pass
            
            logging.error("Could not parse strategies, returning empty list")
            return []

    def apply_tax_strategies(self, json_input, strategies_list):
        """
        Tool 2: Apply selected tax strategies and calculate estimated taxes using AI.
        
        Args:
            json_input (str): JSON string containing client tax information
            strategies_list (list): List of applicable tax strategies (max 3)
            
        Returns:
            str: Human-readable tax strategy analysis with tax calculations
        """
        try:
            if isinstance(json_input, str):
                client_data = json.loads(json_input)
            else:
                client_data = json_input
        except json.JSONDecodeError:
            return "Error: Invalid JSON input."
        
        if not isinstance(strategies_list, list):
            return f"Error: Expected list of strategies but got {type(strategies_list).__name__}"
        
        if len(strategies_list) == 0:
            return "No applicable tax strategies found for your situation."

        # Limit to top 3 strategies
        if len(strategies_list) > 3:
            strategies_list = strategies_list[:3]

        # First, calculate and store the baseline tax calculation
        baseline_prompt = f"""
        You are a professional tax advisor. Calculate the detailed baseline tax calculation for this client.
        
        Client Tax Information:
        {json.dumps(client_data, indent=2)}
        
        Provide a comprehensive breakdown including:
        1. Total income calculation from all sources
        2. Business expenses and deductions
        3. Adjusted Gross Income (AGI)
        4. Federal income tax calculation with tax brackets
        5. State tax calculation (if applicable)
        6. FICA taxes (Social Security and Medicare)
        7. Total tax liability
        8. Effective tax rate
        
        Show all calculations step by step with formulas and specific dollar amounts.
        Format this as a detailed calculation showing all steps and formulas used.
        """
        
        baseline_response = self.llm.complete(baseline_prompt)
        baseline_calculation = baseline_response.text
        
        # Store baseline calculation in file
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            base_tax_file_path = os.path.join(os.path.dirname(base_dir), "base_tax_calculation.txt")
            
            with open(base_tax_file_path, "w", encoding="utf-8") as f:
                f.write("BASELINE TAX CALCULATION\n")
                f.write("=" * 50 + "\n\n")
                f.write(baseline_calculation)
            
            logging.info(f"Baseline tax calculation saved to {base_tax_file_path}")
            
        except Exception as e:
            logging.error(f"Error saving baseline tax calculation: {str(e)}")
            
        # Now create the main tax strategy analysis prompt (without baseline section)
        prompt = f"""
        You are a professional tax advisor with extensive knowledge of tax calculations and optimization strategies. 
        Based on the client's financial information and the selected tax strategies, provide a tax strategy analysis.
        
        Client Tax Information:
        {json.dumps(client_data, indent=2)}
        Base line tax calculation (For Reference Only):
        {baseline_calculation}
        Selected Tax Strategies (Top {len(strategies_list)} most relevant):
        {json.dumps(strategies_list, indent=2)}
        
        Your task is to:
        1. For each strategy, calculate the tax impact and savings compared to baseline
        2. Provide detailed implementation steps
        3. Include common pitfalls to avoid for each strategy
        4. Make realistic assumptions about tax brackets, deductions, and credits
        
        Use these guidelines for calculations:
        - For US taxes, consider federal income tax, state tax (if applicable), and FICA taxes
        - Apply appropriate tax brackets based on filing status and income level
        - Consider standard vs itemized deductions
        - Factor in applicable tax credits
        - For business income, consider self-employment tax implications
        
        IMPORTANT: Format your response as human-readable text that could be directly shared with a client.
        Include clear headings, specific dollar amounts, and step-by-step explanations for each strategy.
        DO NOT respond with JSON - respond with well-formatted text only.
        DO NOT include the baseline tax calculation section in your response.
        
        Structure your response like this:
        
        TAX STRATEGY ANALYSIS
        
        ## Client Overview
        - Filing Status: [Extract from client data]
        - Total Annual Income: $[Calculate total income]
        - Primary Income Sources: [List main sources]
        - Dependents: [Number and ages if applicable]
        
        ### Strategy 1: [Strategy Title]
        - **Relevance Score**: [Score]/10
        - **How it applies**: [Detailed explanation based on client situation]
        - **Tax Calculation with Strategy**:
          - Federal Income Tax: $[Adjusted amount]
          - State Tax: $[Adjusted amount] 
          - FICA Taxes: $[Adjusted amount]
          - Total Tax with Strategy: $[New total]
        - **Estimated Tax Savings**: $[Baseline - Strategy total]
        - **Implementation Steps**:
          1. [Specific actionable step]
          2. [Specific actionable step]
          3. [Additional steps as needed]
        - **Required Documentation**: [List any forms or documents needed]
        - **Timing Considerations**: [When to implement]
        - **Common Pitfalls to Avoid**:
          [Include the specific pitfalls from the strategy data provided above]
        
        ### Strategy 2: [Strategy Title]
        [Same format as Strategy 1, including the Common Pitfalls section]
        
        ### Strategy 3: [Strategy Title]
        [Same format as Strategy 1, including the Common Pitfalls section]
        
        ## Summary and Recommendations
        
        ### Strategy Comparison
        | Strategy | Tax Savings | Implementation Difficulty | Timeline |
        |----------|-------------|---------------------------|----------|
        | [Strategy 1] | $[Amount] | [Easy/Medium/Hard] | [Timeline] |
        | [Strategy 2] | $[Amount] | [Easy/Medium/Hard] | [Timeline] |
        | [Strategy 3] | $[Amount] | [Easy/Medium/Hard] | [Timeline] |
        
        ### Best Strategy Recommendation
        - **Recommended Strategy**: [Name of strategy with best savings/effort ratio]
        - **Expected Annual Savings**: $[Amount]
        - **Why this strategy**: [Explanation of why it's best for this client]
        
        ### Combined Strategy Potential
        - **If multiple strategies can be combined**: $[Total potential savings]
        - **Overall Recommendation**: [Strategic advice for the client]
        
        ### Next Steps
        1. [Immediate action item]
        2. [Follow-up action item]
        3. [Long-term planning item]
        
        **Note**: These calculations are estimates based on current tax laws and the information provided.
        """
        
        response = self.llm.complete(prompt)
        return response.text

    def process_tax_scenario(self, client_json):
        """
        Process a client's tax scenario to identify and apply appropriate tax strategies.
        
        Args:
            client_json (str or dict): Client's tax information as JSON string or dictionary
            
        Returns:
            dict: Tax strategy analysis with applicable strategies and human-readable analysis
        """
        try:
            if isinstance(client_json, dict):
                client_json_str = json.dumps(client_json)
            else:
                client_json_str = client_json
                json.loads(client_json_str)  # Validate JSON
                
            # Step 1: Identify applicable tax strategies
            strategies_result = self.get_tax_strategies(client_json_str)
            
            if not isinstance(strategies_result, list):
                return f"Error: Expected list of strategies but got {type(strategies_result)}"
            
            # Step 2: Apply strategies and calculate tax estimates
            human_readable_analysis = self.apply_tax_strategies(client_json_str, strategies_result)
            
            return {
                "applicable_strategies": strategies_result,
                "tax_analysis": human_readable_analysis
            }
            
        except Exception as e:
            logging.error(f"Error processing tax scenario: {str(e)}")
            return f"An error occurred while analyzing your tax scenario: {str(e)}\n\nPlease check your input and try again."

if __name__ == "__main__":
    try:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        
        input_file_path = "input.json"
        logging.info(f"Loading client data from {input_file_path}")
        
        with open(input_file_path, "r", encoding="utf-8") as f:
            client_data = json.load(f)
        
        print(f"Loaded client data from {input_file_path}")
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        agent = Tax_Stratigies_Agent(openai_api_key=api_key)
        print("Tax Strategies Agent initialized")
        
        print("Processing tax scenario...")
        results = agent.process_tax_scenario(client_data)
        print(results)
    except FileNotFoundError as e:
        print(f"Error: File not found - {e}")
        print(f"Make sure the file exists in the current directory: {os.getcwd()}")
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format - {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        import traceback
        traceback.print_exc()