from llama_index.llms.openai import OpenAI
from llama_index.core.agent.react.base import ReActAgent
from llama_index.core.tools import FunctionTool
import json
import logging
class ScenarioClarificationAgent:
    def __init__(self, openai_api_key):
        self.llm = OpenAI(api_key=openai_api_key, model="gpt-4o-mini")
        self.tools = [
            FunctionTool.from_defaults(
                fn=self._tool_generate_question_list,
                name="generate_question_list",
                description="Use this tool to generate a comprehensive list of questions needed to file a tax return based on the client's scenario."
            ),
            FunctionTool.from_defaults(
                fn=self._tool_validate_responses,
                name="validate_responses",
                description="Use this tool to validate the client's responses and determine if more questions are needed or if we have sufficient information."
            ),
            FunctionTool.from_defaults(
                fn=self._tool_generate_structured_json,
                name="generate_structured_json",
                description="Use this tool when all questions have been answered to generate a structured JSON representation of the client's tax scenario."
            ),
        ]
        
        # Update system prompt to better define the sequential roles
        self.agent = ReActAgent.from_tools(
            tools=self.tools,
            llm=self.llm,
            system_prompt=(
                "You are a CPA assistant with three distinct roles working in a strict sequence:\n"
                "ROLE 1: Question Generator - Creates a list of important questions needed for tax filing\n"
                "ROLE 2: Response Validator - Reviews answers to the questions from Role 1 and determines if more information is needed\n"
                "ROLE 3: JSON Generator - Creates structured JSON representation when all information is gathered\n\n"
                "Always follow this exact sequence and maintain context between roles. Each role builds upon the work of the previous role."
            ),
            verbose=True
        )
        
        # Track what stage we're in
        self.current_stage = "question_generation"
        self.question_list_generated = False
        self.all_questions = []
        # Add context tracking to maintain state between agents
        self.original_scenario = ""
        self.conversation_history = []
        self.agent_memory = {}  # Store additional context between agent transitions
        # Add a counter to track conversation turns
        self.conversation_turn = 0
        # Add a flag to detect when we're in a recovery mode
        self.recovery_mode = False

    def _tool_generate_question_list(self, conversation: str):
        """Agent 1: Generates a list of questions needed to file a tax return.
        -- Args--
        Client's case scenario as a string.
        -- Returns--
        A formatted list of questions that can be used to gather necessary information for tax filing.
        -- Notes--
        This function generates a comprehensive list of questions based on the client's scenario.
        It ensures that the questions are specific, relevant, and can be answered by a layman without requiring tax knowledge.
        The questions cover all aspects of tax filing, including filing status, income sources, deductions, credits, dependents, and special situations.
        The output is a clear numbered list of questions that can be used to gather the necessary information for tax filing.
        """
        prompt = (
            "You are a professional tax preparer with extensive experience. Your task is to generate a comprehensive list of specific questions which you can ask your client. Include only the questions which a layman could answer. No tax knowledge should be required to answer these questions. "
            "Questions should be about personal information relevant to tax filing but shouldn't ask questions about how to file."
            "Based on these questions you should be able to accurately file a tax return based on the client's scenario. Think through all aspects of tax filing:\n\n"
            "You can ask as many questions as required to extract the artifacts required as questioning is the only source to extract information from client. \n"
            "Don't ask any questions which would require tax knowledge. All such information would be extracted from artifacts.\n"
            "The questions would be asked by a tax consultant to his client. The questions asked should be relevant to tax filing artifacts only. Shouldn't confuse the client or require him to use his tax knowledge. \n"
            "You can ask questions like all these and all the other necessary ones. The tax filing is being done in US, so do consider this."
            # "- Filing status (single, married, head of household, etc.)\n"
            "- Region to determine applicable tax laws (federal, state, local)\n"
            # "- Country of residence for international tax considerations\n"
            "- Annual Income amount. \n"
            "- Income sources (W-2, 1099, self-employment, investments, rental properties, etc.)\n"
            "- Deductions (medical expenses, mortgage interest, etc.)\n"
            "- Credits (child tax credit, education credits, energy credits, etc.)\n"
            "- Dependents and household information\n"
            "- Tax payments already made (withholding, estimated payments, etc.)\n"
            "- Special situations (foreign income, cryptocurrency, retirement distributions, etc.)\n\n"
            "Format as a clear numbered list of questions that would be essential for tax filing. "
            "Each question should be specific and directly related to tax filing requirements.\n"
            "Do NOT provide answers or explanations - ONLY the numbered list of questions.\n\n"
            f"Client Scenario:\n{conversation}\n\n"
        )
        
        try:
            response = self.llm.complete(prompt)
            logging.info(f"Generated questions raw response: {response.text}")
            questions = response.text.split('\n')
            cleaned_questions = []
            for q in questions:
                q = q.strip()
                if not q:
                    continue
                # Check if it starts with a number and period
                if any(q.startswith(f"{i}.") for i in range(1, 100)):
                    cleaned_questions.append(q)
                # Check if it starts with just a number (add period)
                elif any(q.startswith(str(i)) for i in range(1, 100)):
                    parts = q.split(' ', 1)
                    if len(parts) > 1:
                        cleaned_q = f"{parts[0]}. {parts[1]}"
                        cleaned_questions.append(cleaned_q)
            
            # If we couldn't extract questions properly, enforce a structured format
            if len(cleaned_questions) < 5:
                logging.warning("Failed to extract enough questions, using backup approach")
                backup_prompt = (
                    "Generate exactly 15 numbered tax filing questions based on this scenario. "
                    "Format each question starting with a number followed by a period. For example:\n"
                    "1. What is your filing status?\n"
                    "2. What was your total income?\n"
                    f"Scenario: {conversation}"
                )
                backup_response = self.llm.complete(backup_prompt)
                questions = backup_response.text.split('\n')
                cleaned_questions = [q.strip() for q in questions if q.strip() and any(q.strip().startswith(f"{i}.") for i in range(1, 100))]
            
            # Store the generated questions
            self.all_questions = cleaned_questions
            
            # Store this in agent memory for future reference
            self.agent_memory["question_list"] = "\n".join(cleaned_questions)
            self.agent_memory["parsed_questions"] = cleaned_questions
            
            # Make sure we have a substantive response
            if not cleaned_questions:
                return "I need to generate tax filing questions, but was unable to do so. Please provide more information about your tax situation."
            
            # Return the formatted list
            return "\n".join(cleaned_questions)
            
        except Exception as e:
            logging.error(f"Error generating questions: {str(e)}")
            # Fallback to a basic set of questions that include all required parameters
            basic_questions = [
                "1. What is your filing status for the tax year? (single, married, head_of_household)",
                "2. What is your country of residence for tax purposes? (Please provide a 2-letter country code, e.g., US for United States)",
                "3. In which state or province do you reside for tax purposes? (Please provide a 2-letter code, e.g., CA for California)",
                "4. What is your total annual income from all sources? (Please provide a specific numeric amount)",
                "5. Do you have any dependents to claim on your tax return?",
                "6. Did you make any estimated tax payments during the year?",
                "7. Do you plan to claim the standard deduction or itemize deductions?",
                "8. Did you have any self-employment income?",
                "9. Did you have any investment income or capital gains/losses?",
                "10. Do you have any tax credits you may qualify for?",
                "11. Did you contribute to any retirement accounts?",
                "12. Do you have any foreign income or foreign financial accounts?",
            ]
            self.all_questions = basic_questions
            self.agent_memory["question_list"] = "\n".join(basic_questions)
            self.agent_memory["parsed_questions"] = basic_questions
            return "\n".join(basic_questions)

    def _tool_validate_responses(self, conversation: str):
        """Agent 2: Validates responses and determines if more information is needed."""
        # Increment conversation turn
        self.conversation_turn += 1
        
        # Force completion after a maximum number of questions
        if self.conversation_turn >= 7:
            return "COMPLETE: All necessary information gathered."
        
        # Enhance prompt to reference previous questions from Agent 1
        question_context = ""
        if "question_list" in self.agent_memory:
            question_context = (
                "Here are the initial questions that were identified as important:\n"
                f"{self.agent_memory['question_list']}\n\n"
                "Based on these questions and the conversation below, determine if all necessary information has been gathered."
            )
        
        # Count how many questions have been answered
        answered_questions = len(self.conversation_history) // 2 if len(self.conversation_history) > 1 else 0
    
        prompt = (
            "You are a tax expert. Your job is to determine if we have ENOUGH information to create a basic tax filing. "
            "We don't need perfect or complete information - just the minimum essential details.\n\n"
            f"{question_context}\n\n"
            f"So far, {answered_questions} questions have been answered.\n\n"
            "IMPORTANT: You should err on the side of completion rather than asking too many questions. "
            "Only ask for additional information if absolutely critical tax details are missing. The most critical things that need to be asked are: 1) Country 2) Region 3) Annual Income 4) Filing Status \n\n"
            "You must do ONE of the following:\n"
            "1. If a CRITICAL piece of information is still missing (like filing status or basic income), "
            "ask ONE specific follow-up question.\n\n"
            "2. In MOST cases, you should respond with: 'COMPLETE: All necessary information gathered.'\n\n"
            f"Original Scenario: {self.original_scenario}\n\n"
            f"Conversation History:\n{conversation}\n\n"
            "Your assessment (strongly prefer 'COMPLETE: All necessary information gathered.' unless critical information is missing):"
        )
        
        # If we've already asked multiple questions, be even more inclined to finish
        if self.conversation_turn > 3:
            prompt = (
                "You are a tax expert wrapping up a client consultation. You've already gathered several pieces of information. "
                "At this point, you should have enough to proceed with a basic tax filing.\n\n"
                f"Current information:\n{conversation}\n\n"
                "Unless a fundamental piece of tax information is missing (like filing status or whether they had any income), "
                "you should respond EXACTLY with: 'COMPLETE: All necessary information gathered.'\n\n"
                "Your assessment:"
            )
        
        response = self.llm.complete(prompt)
        
        # Store this validation result in agent memory
        self.agent_memory["last_validation"] = response.text
        
        # Apply some heuristics to force completion in certain cases
        response_text = response.text.strip()
        
        # If we've asked enough questions, force completion
        if self.conversation_turn >= 4 and "COMPLETE:" not in response_text.upper():
            logging.info(f"Forcing completion after {self.conversation_turn} questions")
            return "COMPLETE: All necessary information gathered."
            
        # If response is too vague or general, force completion
        vague_phrases = ["more information", "additional details", "tell me more", "clarify", "anything else"]
        if any(phrase in response_text.lower() for phrase in vague_phrases) and self.conversation_turn > 2:
            logging.info("Detected vague question, forcing completion")
            return "COMPLETE: All necessary information gathered."
        
        return response_text

    def _tool_generate_structured_json(self, conversation: str):
        """Agent 3: Generates a structured JSON representation of the tax scenario."""
        # Reference both Agent 1's questions and Agent 2's validations
        context = ""
        if "question_list" in self.agent_memory and "last_validation" in self.agent_memory:
            context = (
                "Important tax questions identified:\n"
                f"{self.agent_memory['question_list']}\n\n"
                "Final validation assessment:\n"
                f"{self.agent_memory['last_validation']}\n\n"
            )
        
        # Enhanced prompt to ensure valid JSON generation even with minimal information
        prompt = (
            "You are a tax expert. Your job is to generate a well-structured JSON object that represents "
            "the client's tax scenario based on the conversation history.\n\n"
            "IMPORTANT: You MUST generate valid JSON even if information is incomplete. "
            "The JSON must only contain the JSON object itself - no surrounding quotes, explanations, or markdown code blocks.\n"
            "Use null values, empty arrays, or default values like 'unknown' for missing information.\n\n"
            f"{context}"
            f"Original Scenario: {self.original_scenario}\n\n"
            f"Complete Conversation History:\n{conversation}\n\n"
            "Example structure (follow this format):\n"
            "{\n"
            "  \"filing_status\": \"single\",\n"
            "  \"income\": {\n"
            "    \"primary\": \"salary\",\n"
            "    \"amount\": 75000,\n"
            "    \"sources\": []\n"
            "  },\n"
            "  \"deductions\": [],\n"
            "  \"tax_dates\": {}\n"
            "}\n\n"
            "Structured JSON output (do not include any text before or after the JSON):"
        )
        
        response = self.llm.complete(prompt)
        # Clean up potential formatting issues
        json_text = response.text.strip()
        
        # Remove any markdown code blocks if present
        if json_text.startswith("```json"):
            json_text = json_text.split("```json", 1)[1]
        if json_text.startswith("```"):
            json_text = json_text.split("```", 1)[1]
        if "```" in json_text:
            json_text = json_text.split("```")[0]
            
        # Strip any leading/trailing whitespace again after code block removal
        json_text = json_text.strip()
        
        # Check if JSON is wrapped in quotes and contains escaped characters
        if (json_text.startswith('"') and json_text.endswith('"')) or (json_text.startswith("'") and json_text.endswith("'")):
            try:
                # Try to parse it as a JSON string
                import ast
                parsed_string = ast.literal_eval(json_text)
                if isinstance(parsed_string, str):
                    json_text = parsed_string
            except:
                # If parsing fails, remove quotes manually
                if json_text.startswith('"') and json_text.endswith('"'):
                    json_text = json_text[1:-1]
                elif json_text.startswith("'") and json_text.endswith("'"):
                    json_text = json_text[1:-1]
                    
                # Unescape common escape sequences
                json_text = json_text.replace("\\n", "\n").replace("\\\"", "\"").replace("\\t", "\t")
        
        # Validate the JSON before returning
        try:
            # Check if it's valid by parsing and re-serializing
            parsed_json = json.loads(json_text)
            return json.dumps(parsed_json, indent=2)
        except:
            # If validation fails, return the original cleaned text
            return json_text

    def clarify_and_structure(self, scenario: str, clarifications=None):
        if clarifications is None:
            clarifications = []
        
        # Store the original scenario for context passing between agents
        if not self.original_scenario:
            self.original_scenario = scenario
        
        # Build conversation history string with proper formatting for clear context
        conversation_parts = [f"Client (Initial Scenario): {scenario}"]
        
        # Add Q&A exchanges, carefully preserving format for clear context
        for i, msg in enumerate(clarifications):
            role = "Agent (Question)" if i % 2 == 0 else "Client (Answer)"
            conversation_parts.append(f"{role}: {msg}")
        
        # Store the full conversation for context passing
        conversation = "\n".join(conversation_parts)
        self.conversation_history = conversation_parts
        
        try:
            # Strictly follow the Agent 1 -> Agent 2 -> Agent 3 flow
            if self.current_stage == "question_generation":
                # Agent 1: Generate list of questions
                question_list = self._tool_generate_question_list(scenario)
                self.question_list_generated = True
                self.current_stage = "validation"
                return {"response": question_list, "status": "needs_clarification"}
            
            elif self.current_stage == "validation":
                # Agent 2: Validate responses and determine if more questions are needed
                validation_result = self._tool_validate_responses(conversation)
                
                # Add a threshold for minimum information - if we have at least some 
                # answers, we should be able to generate a basic JSON
                min_answers_required = min(3, len(self.all_questions))
                answers_provided = len(clarifications) // 2
                
                # If we have enough answers, try to move to JSON generation
                if answers_provided >= min_answers_required and "COMPLETE:" not in validation_result.upper():
                    # Check if we've received enough meaningful information
                    meaningful_threshold = 50  # character count as a simple heuristic
                    meaningful_answers = 0
                    
                    for i, msg in enumerate(clarifications):
                        if i % 2 == 1 and len(msg.strip()) > meaningful_threshold:  # It's an answer and it's substantial
                            meaningful_answers += 1
                    
                    if meaningful_answers >= min_answers_required:
                        validation_result = "COMPLETE: All necessary information gathered."
                
                if "COMPLETE:" in validation_result.upper():
                    # If Agent 2 determines we have all needed information, move to Agent 3
                    self.current_stage = "json_generation"
                    json_output = self._tool_generate_structured_json(conversation)
                    
                    # Validate JSON format - multiple attempts to ensure success
                    for attempt in range(3):  # Try up to 3 times
                        try:
                            json.loads(json_output)
                            # Reset recovery mode and turn counter on success
                            self.recovery_mode = False
                            self.conversation_turn = 0
                            return {"response": json_output, "status": "complete"}
                        except json.JSONDecodeError:
                            if attempt < 2:  # Only retry if we haven't reached max attempts
                                # Try again with an even more explicit prompt
                                backup_prompt = (
                                    "Generate a valid JSON object with the following structure. "
                                    "ONLY output the JSON object - no explanations or additional text.\n"
                                    "{\n"
                                    "  \"filing_status\": string,\n"
                                    "  \"income\": {\n"
                                    "    \"primary\": string,\n"
                                    "    \"additional\": array\n"
                                    "  },\n"
                                    "  \"deductions\": array,\n"
                                    "  \"tax_dates\": object\n"
                                    "}\n\n"
                                    f"Based on this information:\n{conversation}"
                                )
                                json_output = self.llm.complete(backup_prompt).text.strip()
                            else:
                                # Last attempt failed, create a minimal valid JSON as fallback
                                minimal_json = {
                                    "filing_status": "unknown",
                                    "income": {
                                        "primary": "unknown",
                                        "additional": []
                                    },
                                    "deductions": [],
                                    "tax_dates": {},
                                    "raw_conversation": conversation
                                }
                                return {"response": json.dumps(minimal_json), "status": "complete"}
                    
                    # This code should not be reached due to the fallback above
                    return {"response": json_output, "status": "complete"}
                else:
                    # Agent 2 determined we need more information - return the follow-up question
                    return {"response": validation_result, "status": "needs_clarification"}
            
            elif self.current_stage == "json_generation":
                # Agent 3: Generate JSON based on complete information
                json_output = self._tool_generate_structured_json(conversation)
                
                # Enhanced JSON validation with multiple fallbacks
                try:
                    json.loads(json_output)
                    return {"response": json_output, "status": "complete"}
                except json.JSONDecodeError:
                    # Try with a more structured prompt
                    backup_prompt = (
                        "Generate ONLY a valid JSON object with this exact structure:\n"
                        "{\n"
                        "  \"filing_status\": \"value\",\n"
                        "  \"income\": {\n"
                        "    \"primary\": \"value\",\n"
                        "    \"sources\": []\n"
                        "  },\n"
                        "  \"tax_information\": {\n"
                        "    \"dates\": {},\n"
                        "    \"deductions\": []\n"
                        "  }\n"
                        "}\n\n"
                        "Fill in appropriate values based on this conversation. "
                        "For any missing information, use null or \"unknown\".\n\n"
                        f"Conversation: {conversation}"
                    )
                    
                    backup_response = self.llm.complete(backup_prompt)
                    backup_output = backup_response.text.strip()
                    
                    try:
                        # Try to parse the backup response
                        json.loads(backup_output)
                        return {"response": backup_output, "status": "complete"}
                    except:
                        # Create a minimal valid JSON as last resort rather than asking more questions
                        minimal_json = {
                            "filing_status": "unknown",
                            "income": {
                                "primary": "unknown",
                                "sources": []
                            },
                            "tax_information": {
                                "dates": {},
                                "deductions": []
                            },
                            "note": "Limited information was provided. This is a basic structure that should be reviewed.",
                            "conversation_summary": conversation[:500] + "..." if len(conversation) > 500 else conversation
                        }
                        
                        return {
                            "response": json.dumps(minimal_json, indent=2),
                            "status": "complete"
                        }
            
            # Fallback (should not typically reach here)
            return {"response": "I need more information about your tax situation.", "status": "needs_clarification"}
            
        except Exception as e:
            # Reset state in case of error
            return {
                "response": f"Error processing tax scenario: {str(e)}",
                "status": "error"
            }
    
    def reset(self):
        """Reset the agent to its initial state."""
        self.current_stage = "question_generation"
        self.question_list_generated = False
        self.all_questions = []
        # Also reset the context tracking
        self.original_scenario = ""
        self.conversation_history = []
        self.agent_memory = {}
        self.conversation_turn = 0
        self.recovery_mode = False
