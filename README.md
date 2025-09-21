# Healthcare Test Case Generator

An AI-powered tool that converts healthcare software requirements into compliant, traceable test cases using Google's Agent Development Kit (ADK) and Streamlit.

## Features

- 🏥 Healthcare compliance standards support (HIPAA, FDA 21 CFR Part 11, IEC 62304, ISO 13485)
- 📄 Multiple document format support (PDF, DOCX, TXT, Markdown)
- 🤖 AI-powered test case generation using Google ADK and Gemini 2.5 Flash
- 📊 CSV export with traceability matrix
- 🔄 Requirement traceability from source to test cases
- ⚡ Google Cloud Shell optimized deployment

## Quick Start

### Prerequisites

- Google Cloud Project with Vertex AI enabled
- uv package manager (pre-installed in Cloud Shell)

### Installation

\`\`\`bash
# Clone repository
git clone https://github.com/yourusername/healthcare-test-agent.git
cd healthcare-test-agent

# Install dependencies
uv sync

# Configure environment
cp .env.example .env
# Edit .env with your Google Cloud project details
\`\`\`

### Running Locally

\`\`\`bash
# Run Streamlit app
uv run streamlit run app.py --server.port 8080

# Or run ADK web interface
uv run adk web --port 8080
\`\`\`

### Deploy to Cloud Run

\`\`\`bash
gcloud run deploy healthcare-test-agent \\
  --source . \\
  --port 8080 \\
  --allow-unauthenticated \\
  --region us-central1
\`\`\`

## Project Structure

\`\`\`
healthcare-test-agent/
├── healthcare_agent/
│   ├── __init__.py
│   └── agent.py          # ADK agent definition
├── app.py                # Streamlit application
├── server.py            # FastAPI server for deployment
├── requirements.txt     # Python dependencies
├── Dockerfile          # Container configuration
├── .env.example        # Environment template
└── README.md
\`\`\`

## Usage

1. Upload healthcare software requirements document
2. Select compliance standard (HIPAA, FDA, etc.)
3. Generate test cases using AI agent
4. Download results as CSV or text format

## Supported Compliance Standards

- HIPAA (Health Insurance Portability and Accountability Act)
- FDA 21 CFR Part 11 (Electronic Records)
- IEC 62304 (Medical Device Software)
- ISO 13485 (Medical Devices Quality Management)

## Contributing

1. Fork the repository
2. Create feature branch (\`git checkout -b feature/new-feature\`)
3. Commit changes (\`git commit -am 'Add new feature'\`)
4. Push to branch (\`git push origin feature/new-feature\`)
5. Create Pull Request

## License

MIT License - see LICENSE file for details
