import streamlit as st
import tempfile
import os
from pathlib import Path
import sys
import asyncio
from typing import Optional

# Document processing libraries
from PyPDF2 import PdfReader
import docx
import io

# ADK imports
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# Add the healthcare_agent to Python path
sys.path.append(str(Path(__file__).parent))

from healthcare_agent.agent import root_agent

def extract_text_from_pdf(pdf_file) -> str:
    """Extract text from PDF using PyPDF2"""
    try:
        pdf_reader = PdfReader(pdf_file)
        text_data = ""
        
        for page in pdf_reader.pages:
            text_data += page.extract_text() + "\n"
        
        return text_data.strip()
    except Exception as e:
        st.error(f"Error extracting PDF content: {str(e)}")
        return ""

def extract_text_from_docx(docx_file) -> str:
    """Extract text from DOCX file"""
    try:
        doc = docx.Document(docx_file)
        text_data = ""
        
        for paragraph in doc.paragraphs:
            text_data += paragraph.text + "\n"
            
        return text_data.strip()
    except Exception as e:
        st.error(f"Error extracting DOCX content: {str(e)}")
        return ""

def process_uploaded_file(uploaded_file) -> Optional[str]:
    """Process uploaded file and extract text content"""
    if uploaded_file is None:
        return None
    
    file_type = uploaded_file.type
    content = ""
    
    try:
        if file_type == "text/plain":
            # Handle text files
            content = uploaded_file.getvalue().decode("utf-8")
            
        elif file_type == "application/pdf":
            # Handle PDF files
            content = extract_text_from_pdf(uploaded_file)
            
        elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            # Handle DOCX files
            content = extract_text_from_docx(uploaded_file)
            
        elif uploaded_file.name.endswith('.md'):
            # Handle Markdown files
            content = uploaded_file.getvalue().decode("utf-8")
            
        else:
            st.error(f"Unsupported file type: {file_type}")
            return None
            
        if not content.strip():
            st.error("No text content found in the uploaded file")
            return None
            
        return content
        
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")
        return None

async def generate_test_cases_with_adk(requirements_text: str, compliance_standard: str) -> dict:
    """Generate test cases using ADK agent with proper Runner execution"""
    try:
        # Create session service and session
        session_service = InMemorySessionService()
        session = await session_service.create_session(
            app_name="healthcare_test_generator",
            user_id="streamlit_user"
        )
        
        # Create ADK Runner
        runner = Runner(
            agent=root_agent,
            app_name="healthcare_test_generator", 
            session_service=session_service
        )
        
        # Create a proper prompt for the healthcare agent
        prompt = f"""
        Analyze the following healthcare software requirements document and generate 
        comprehensive, compliant test cases for {compliance_standard} standards:

        REQUIREMENTS DOCUMENT:
        {requirements_text[:8000]}  # Limit content to avoid token limits

        INSTRUCTIONS:
        1. Generate functional test cases for each identified requirement
        2. Create security test cases for data protection and privacy
        3. Include compliance-specific test cases for {compliance_standard}
        4. Add integration test cases for system interfaces
        5. Generate acceptance test cases with clear criteria
        6. Ensure full traceability from requirements to test cases
        7. Include appropriate risk-based testing scenarios

        Please provide structured output with:
        - Test Case ID
        - Test Type (functional, security, compliance, integration, acceptance)
        - Priority Level
        - Requirement Traceability
        - Test Scenario Description
        - Preconditions
        - Test Steps
        - Expected Results
        - Compliance Tags

        Generate at least 10-15 comprehensive test cases.
        """
        
        # Create content for the agent
        user_content = types.Content(
            role='user', 
            parts=[types.Part(text=prompt)]
        )
        
        # Execute the agent using Runner
        final_response = ""
        async for event in runner.run_async(
            user_id="streamlit_user",
            session_id=session.id,
            new_message=user_content
        ):
            # Process events from the agent
            if event.is_final_response() and event.content:
                # Extract the final response text
                if event.content.parts:
                    final_response = event.content.parts[0].text
                break
        
        if final_response:
            return {
                "status": "success",
                "content": final_response,
                "message": "Test cases generated successfully using ADK"
            }
        else:
            return {
                "status": "error",
                "content": "",
                "message": "No response received from ADK agent"
            }
            
    except Exception as e:
        return {
            "status": "error",
            "content": "",
            "message": f"Error in ADK agent execution: {str(e)}"
        }


st.set_page_config(
    page_title="Healthcare Test Case Generator",
    page_icon="🏥",
    layout="wide"
)

st.title("🏥 Healthcare Software Requirements to Test Cases")
st.markdown("Upload your healthcare software requirements document to generate compliant test cases")

# Add dependency installation info
with st.expander("✨ Upcoming Features"):
    st.code("""
    1. Getting Software requirement document from Confluence page
    2. Automatic test stories ocreatin on JIRA
    3. Agentic validation of GDPR and Complience standards
    """)

# File upload section
uploaded_file = st.file_uploader(
    "Choose a requirements document",
    type=['pdf', 'docx', 'txt', 'md'],
    help="Upload software requirements document (PDF, DOCX, TXT, or Markdown)",
    key="doc_uploader"
)

# Compliance standard selection
compliance_standard = st.selectbox(
    "Select Compliance Standard",
    ["HIPAA", "FDA 21 CFR Part 11", "IEC 62304", "ISO 13485", "Custom"],
    help="Choose the healthcare compliance standard for test case generation"
)

# Custom compliance requirements
if compliance_standard == "Custom":
    custom_requirements = st.text_area(
        "Custom Compliance Requirements",
        placeholder="Enter specific compliance requirements..."
    )

# Processing section
if uploaded_file is not None:
    st.success(f"✅ File uploaded: {uploaded_file.name}")
    
    # Display file details
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info(f"📄 Size: {len(uploaded_file.getvalue())} bytes")
    with col2:
        st.info(f"🔍 Type: {uploaded_file.type}")
    with col3:
        st.info(f"📋 Format: {uploaded_file.name.split('.')[-1].upper()}")
    
    # Extract and preview document content
    with st.expander("📖 Document Content Preview"):
        with st.spinner("Extracting text content..."):
            content = process_uploaded_file(uploaded_file)
            
            if content:
                st.success(f"✅ Extracted {len(content)} characters of text")
                
                # Show first 1000 characters as preview
                preview_text = content[:1000]
                if len(content) > 1000:
                    preview_text += "...\n\n[Content truncated for preview]"
                
                st.text_area(
                    "Extracted Content (Preview)",
                    preview_text,
                    height=200,
                    disabled=True
                )
            else:
                st.error("❌ Failed to extract content from the document")
    
    # Process button - only show if content was successfully extracted
    if 'content' in locals() and content:
        if st.button("🚀 Generate Test Cases", type="primary", use_container_width=True):
            with st.spinner("🔄 Processing requirements and generating test cases..."):
                try:
                    # Use asyncio to run the async ADK agent
                    result = asyncio.run(
                        generate_test_cases_with_adk(content, compliance_standard)
                    )
                    
                    if result["status"] == "success":
                        st.success("✅ Test cases generated successfully!")
                        
                        # Display the generated content
                        st.subheader("📋 Generated Test Cases")
                        
                        # Show the agent's response
                        with st.expander("🤖 ADK Agent Response", expanded=True):
                            st.markdown(result["content"])
                        
                        # Create downloadable content
                        st.subheader("💾 Download Test Cases")
                        
                        # Format content for download
                        download_content = f"""Healthcare Software Test Cases
Generated using Google ADK Agent
Compliance Standard: {compliance_standard}
Generated on: {st.session_state.get('timestamp', 'Unknown')}

Source Document: {uploaded_file.name}

{result["content"]}
"""
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.download_button(
                                label="📄 Download as Text",
                                data=download_content,
                                file_name=f"{uploaded_file.name}_test_cases.txt",
                                mime="text/plain",
                                use_container_width=True
                            )
                        
                        with col2:
                            # Create CSV format (simplified)
                            csv_header = "Test_Case_ID,Type,Priority,Requirement_ID,Test_Scenario\n"
                            csv_content = csv_header + "Generated test cases would be formatted as CSV here"
                            
                            st.download_button(
                                label="📊 Download as CSV",
                                data=csv_content,
                                file_name=f"{uploaded_file.name}_test_cases.csv",
                                mime="text/csv",
                                use_container_width=True
                            )
                    
                    else:
                        st.error(f"❌ Error: {result['message']}")
                        
                        # Show debugging information
                        with st.expander("🔧 Debug Information"):
                            st.write("Result:", result)
                        
                except Exception as e:
                    st.error(f"❌ Error processing with ADK agent: {str(e)}")
                    
                    # Show debugging information
                    with st.expander("🔧 Debug Information"):
                        st.write("Exception:", str(e))
                        st.write("Exception type:", type(e))

# Information sidebar
with st.sidebar:
    st.header("ℹ️ About")
    st.markdown("""
    This AI agent converts healthcare software requirements into compliant, 
    traceable test cases using Google's ADK and Gemini 2.5 Flash.
    
    **✨ Features:**
    - Healthcare compliance standards support
    - Requirement traceability matrix
    - Risk-based test case generation
    - Multiple export formats
    - Document content validation
    """)
    
    st.header("📋 Supported Standards")
    st.markdown("""
    - **HIPAA** - Health Insurance Portability and Accountability Act
    - **FDA 21 CFR Part 11** - Electronic Records
    - **IEC 62304** - Medical Device Software
    - **ISO 13485** - Medical Devices QMS
    """)
    
    st.header("📎 Supported File Types")
    st.markdown("""
    - **PDF** (.pdf)
    - **Word Documents** (.docx)
    - **Text Files** (.txt)
    - **Markdown** (.md)
    """)
