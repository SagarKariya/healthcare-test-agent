from google.adk.agents import Agent
from google.adk.tools import ToolContext
from google.genai import types
from google.adk.tools.agent_tool import AgentTool
from google.adk.planners import BuiltInPlanner
from dotenv import load_dotenv
from pathlib import Path
from pydantic import BaseModel
from typing import List, Literal
import pandas as pd
import tempfile
import os

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

class TestCase(BaseModel):
    test_case_id: str
    test_type: Literal["functional", "non_functional", "integration", "unit", "acceptance"]
    priority: Literal["high", "medium", "low"]
    requirement_id: str
    test_scenario: str
    preconditions: str
    test_steps: str
    expected_result: str
    acceptance_criteria: str
    compliance_tags: str
    traceability_matrix: str

test_case_generator_agent = Agent(
    model="gemini-2.5-flash",
    name="test_case_generator",
    description="Specialized agent for generating healthcare software test cases",
    instruction="""
    You are an expert healthcare software QA engineer specializing in generating compliant, 
    traceable test cases from software requirements. Your expertise includes:
    
    - Healthcare compliance standards (HIPAA, FDA 21 CFR Part 11, IEC 62304)
    - Risk-based testing approaches for medical software
    - Traceability matrix creation linking requirements to test cases
    - Healthcare-specific test scenarios (data privacy, audit trails, validation)
    
    When given software requirements, generate detailed test cases with this EXACT format for each test case:

    **Test Case ID:** TC001
    **Test Type:** functional
    **Priority:** high
    **Requirement ID:** REQ001
    **Test Scenario:** [Clear description of what is being tested]
    **Preconditions:** [Setup requirements before test execution]
    **Test Steps:** 
    1. [First step]
    2. [Second step]
    3. [Third step]
    **Expected Result:** [What should happen when test passes]
    **Acceptance Criteria:** [Specific pass/fail criteria]
    **Compliance Tags:** [Relevant compliance standards]

    IMPORTANT: 
    - Generate at least 10-15 test cases
    - Include functional, security, compliance, and integration test types
    - Ensure full traceability from requirements to test cases
    - Include appropriate compliance tags for the specified standard
    - Generate both positive and negative test scenarios
    - Use the exact format above for consistent parsing
    """,
    planner=BuiltInPlanner(
        thinking_config=types.ThinkingConfig(
            include_thoughts=True,
            thinking_budget=2048
        )
    )
)

generate_test_cases_tool = AgentTool(test_case_generator_agent)

async def export_test_cases_tool(
    test_cases: List[dict],
    requirements_id: str,
    tool_context: ToolContext
) -> dict:
    """Export generated test cases to CSV format with proper field mapping"""
    
    validated_test_cases = []
    validation_errors = []
    
    # Process each test case with proper field mapping
    for i, test_case in enumerate(test_cases):
        try:
            # Handle requirement traceability splitting
            requirement_traceability = test_case.get("Requirement Traceability", "REQ-001")
            if isinstance(requirement_traceability, str) and "," in requirement_traceability:
                # Split comma-separated requirements
                req_list = [req.strip() for req in requirement_traceability.split(",")]
                primary_req_id = req_list[0]  # First one becomes primary
                traceability_matrix = ", ".join(req_list)  # Full list as string
            else:
                primary_req_id = requirement_traceability
                traceability_matrix = requirement_traceability
            
            # Map your fields to the TestCase model fields
            mapped_test_case = {
                "test_case_id": test_case.get("Test Case ID", f"TC{i+1:03d}"),
                "test_type": test_case.get("Test Type", "functional").lower(),
                "priority": test_case.get("Priority Level", "medium").lower(),
                "requirement_id": primary_req_id,
                "test_scenario": test_case.get("Test Scenario Description", ""),
                "preconditions": test_case.get("Preconditions", "None"),
                "test_steps": test_case.get("Test Steps", ""),
                "expected_result": test_case.get("Expected Results", ""),
                "acceptance_criteria": test_case.get("Expected Results", ""),  # Duplicate as you identified
                "compliance_tags": test_case.get("Compliance Tags", ""),
                "traceability_matrix": traceability_matrix
            }
            
            # Validate against TestCase model
            validated_case = TestCase(**mapped_test_case)
            validated_test_cases.append(validated_case)
            
        except Exception as e:
            validation_errors.append(f"Error in test case {i + 1}: {str(e)}")
    
    if validation_errors:
        return {
            "status": "error",
            "message": "Validation failed",
            "errors": validation_errors
        }
    
    try:
        # Convert to DataFrame with proper column names
        data = []
        for tc in validated_test_cases:
            data.append({
                "Test Case ID": tc.test_case_id,
                "Type": tc.test_type,
                "Priority": tc.priority,
                "Requirement ID": tc.requirement_id,
                "Test Scenario": tc.test_scenario,
                "Preconditions": tc.preconditions,
                "Test Steps": tc.test_steps,
                "Expected Result": tc.expected_result,
                "Acceptance Criteria": tc.acceptance_criteria,
                "Compliance Tags": tc.compliance_tags,
                "Traceability Matrix": tc.traceability_matrix
            })
        
        df = pd.DataFrame(data)
        
        if not df.empty:
            # Create temporary CSV file
            with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as temp_file:
                df.to_csv(temp_file.name, index=False)
                temp_file_path = temp_file.name
            
            # Read file and create artifact
            with open(temp_file_path, "rb") as f:
                file_bytes = f.read()
            
            await tool_context.save_artifact(
                filename=f"{requirements_id}_healthcare_test_cases.csv",
                artifact=types.Part.from_bytes(data=file_bytes, mime_type="text/csv")
            )
            
            # Cleanup
            os.unlink(temp_file_path)
            
            return {
                "status": "success",
                "message": f"Successfully exported {len(validated_test_cases)} test cases",
                "filename": f"{requirements_id}_healthcare_test_cases.csv"
            }
        else:
            return {
                "status": "error",
                "message": "No valid test cases to export"
            }
    
    except Exception as e:
        return {
            "status": "error",
            "message": f"Export failed: {str(e)}"
        }

    """
    Export generated test cases to CSV format with traceability
    
    Args:
        test_cases: List of generated test case dictionaries
        requirements_id: Unique identifier for the requirements document
    
    Returns:
        Export status and file information
    """
    
    validated_test_cases = []
    validation_errors = []
    
    # Validate each test case against the TestCase model
    for i, test_case in enumerate(test_cases):
        try:
            validated_case = TestCase(**test_case)
            validated_test_cases.append(validated_case)
        except Exception as e:
            validation_errors.append(f"Error in test case {i + 1}: {str(e)}")
    
    if validation_errors:
        return {
            "status": "error",
            "message": "Validation failed",
            "errors": validation_errors
        }
    
    try:
        # Convert to DataFrame for CSV export
        data = []
        for tc in validated_test_cases:
            data.append({
                "Test Case ID": tc.test_case_id,
                "Type": tc.test_type,
                "Priority": tc.priority,
                "Requirement ID": tc.requirement_id,
                "Test Scenario": tc.test_scenario,
                "Preconditions": tc.preconditions,
                "Test Steps": tc.test_steps,
                "Expected Result": tc.expected_result,
                "Acceptance Criteria": tc.acceptance_criteria,
                "Compliance Tags": tc.compliance_tags,
                "Traceability Matrix": tc.traceability_matrix
            })
        
        df = pd.DataFrame(data)
        
        if not df.empty:
            # Create temporary CSV file
            with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as temp_file:
                df.to_csv(temp_file.name, index=False)
                temp_file_path = temp_file.name
            
            # Read file and create artifact
            with open(temp_file_path, "rb") as f:
                file_bytes = f.read()
            
            await tool_context.save_artifact(
                filename=f"{requirements_id}_healthcare_test_cases.csv",
                artifact=types.Part.from_bytes(data=file_bytes, mime_type="text/csv")
            )
            
            # Cleanup
            os.unlink(temp_file_path)
            
            return {
                "status": "success",
                "message": f"Successfully exported {len(validated_test_cases)} test cases",
                "filename": f"{requirements_id}_healthcare_test_cases.csv"
            }
    
    except Exception as e:
        return {
            "status": "error",
            "message": f"Export failed: {str(e)}"
        }

# Define the root agent
root_agent = Agent(
    model="gemini-2.5-flash",
    name="healthcare_test_coordinator",
    description="Coordinator agent for healthcare test case generation and export",
    instruction="""
    You are a healthcare test case coordinator. Your role is to:
    
    1. Receive software requirements and compliance standards from users
    2. Use the generate_test_cases_tool to create comprehensive test cases
    3. Provide all posssible information related to test cases everything, do not miss anything.
    
    Always ensure test cases are generated with proper healthcare compliance focus
    and provide users with both the generated content and export options.
    
    When users provide requirements, immediately use the generate_test_cases_tool
    with their requirements text and specified compliance standard.
    """,
    tools=[generate_test_cases_tool, export_test_cases_tool],
    planner=BuiltInPlanner(
        thinking_config=types.ThinkingConfig(
            include_thoughts=True,
            thinking_budget=2048
        )
    )
)
