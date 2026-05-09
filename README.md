Talash Project - Talent Acquisition & Learning Automation for Smart Hiring

Overview:
Talash is a CV analysis system designed to automate the recruitment preprocessing stage by extracting, structuring, and analyzing candidate data from PDF CVs.

Features

Milestone 1:
- CV parsing from PDF files
- Folder-based CV ingestion
- Basic information extraction (personal details, education, experience, skills)
- JSON and CSV output generation
- Streamlit-based UI prototype

Milestone 2:
- Extended analysis pipeline for candidate evaluation
- Educational profile analysis
- Professional experience and employment history analysis
- Missing information detection
- Automated personalized email generation
- Partial research profile processing (publications extraction)
- Structured storage across multiple CSV files
- Interactive dashboard with tables and charts
- Visualizations for education, skills, missing data, and research output

Milestone 3:
- Full end-to-end recruitment analysis pipeline
- Complete Streamlit-based web application
- Research profile analysis (journals and conferences)
- Topic variability analysis for identifying research focus and diversity
- Co-author analysis for collaboration pattern evaluation
- Skill alignment validation using experience and publications
- Candidate summary generation
- Candidate ranking and comparative evaluation system
- Timeline consistency and gap analysis
- Candidate-wise analytical dashboards and visualizations
- Multiple candidate CV processing through folder-based ingestion

Technologies Used
- Python
- Streamlit
- Pandas
- PyMuPDF
- pdfplumber
- Google Gemini API
- OpenAI API
- python-dotenv

Running the Project
1. Clone the repository
    _git clone <repository-link>_
2. Install dependencies
    _pip install -r requirements.txt_
3. Add API keys in .env
    _GOOGLE_API_KEY=your_key
    OPENAI_API_KEY=your_key_
4. Run the Streamlit app
    _streamlit run src/app.py_

Authors
Aimen Ahsan (467032)
Areesha Fatima (454459)
Zainab Raees (462705)
