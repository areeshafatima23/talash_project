# src/app.py
import streamlit as st
import tempfile, os, json
import pandas as pd
import plotly.express as px
from loader import extract_text_from_pdf, load_cvs_from_folder
from parser import extract_full_profile
from milestone1_pipeline import run_pipeline as run_m1_pipeline
from milestone2_pipeline import run_pipeline as run_m2_pipeline

st.set_page_config(page_title="TALASH", layout="wide")
st.title("🎓 TALASH — CV Analyzer")
st.caption("Talent Acquisition & Learning Automation for Smart Hiring")

mode = st.sidebar.radio(
    "Mode", 
    ["Upload Single CV", "Process CVs Folder (Milestone 1)", "Milestone 2: Analysis Pipeline"]
)

# ── Mode 1: Single CV Upload ──────────────────────────────────
if mode == "Upload Single CV":
    st.header("Upload a CV")
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

    if uploaded_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name

        with st.spinner("Reading PDF..."):
            text = extract_text_from_pdf(tmp_path)
        os.unlink(tmp_path)

        with st.spinner("Analyzing CV with AI..."):
            profile = extract_full_profile(text)

        st.subheader("Personal Info")
        st.write(f"**Name:** {profile.get('name', 'N/A')}")
        st.write(f"**Email:** {profile.get('email', 'N/A')}")
        st.write(f"**Phone:** {profile.get('phone', 'N/A')}")
        st.write(f"**Address:** {profile.get('address', 'N/A')}")

        st.subheader("Skills")
        st.write(", ".join(profile.get("skills", [])) or "No skills found")

        st.subheader("Education")
        if profile.get("education"):
            st.dataframe(pd.DataFrame(profile["education"]), use_container_width=True)

        st.subheader("Experience")
        if profile.get("experience"):
            st.dataframe(pd.DataFrame(profile["experience"]), use_container_width=True)

        st.subheader("Download JSON / CSV")
        json_filename = uploaded_file.name.replace(".pdf", "_profile.json")
        st.download_button("Download JSON", json.dumps(profile, indent=2), json_filename, mime="application/json")
        flat_csv = pd.DataFrame([{
            "file_name": uploaded_file.name,
            "name": profile.get("name", ""),
            "email": profile.get("email", ""),
            "phone": profile.get("phone", ""),
            "address": profile.get("address", ""),
            "education": json.dumps(profile.get("education", [])),
            "experience": json.dumps(profile.get("experience", [])),
            "skills": ", ".join(profile.get("skills", []))
        }]).to_csv(index=False)
        st.download_button("Download CSV", flat_csv, uploaded_file.name.replace(".pdf", "_profile.csv"), "text/csv")

# ── Mode 2: Folder Processing (Milestone 1) ─────────────────
elif mode == "Process CVs Folder (Milestone 1)":
    st.header("Process All CVs from Folder (Milestone 1)")
    st.info("Place PDF CVs in the `cvs/` folder, then click Run.")
    cvs_folder = os.path.join(os.path.dirname(__file__), "../cvs")
    output_csv = os.path.join(os.path.dirname(__file__), "../output/milestone1_output.csv")

    if st.button("Run Milestone 1 Pipeline"):
        with st.spinner("Processing CVs..."):
            rows = run_m1_pipeline(cvs_folder, output_csv)

        if rows:
            st.success(f"Processed {len(rows)} CV(s)!")
            st.dataframe(pd.DataFrame(rows)[["file_name", "name", "email", "phone", "skills"]], use_container_width=True)
            with open(output_csv, "rb") as f:
                st.download_button("Download Full CSV", f, "milestone1_output.csv", "text/csv")
        else:
            st.warning("No CVs found in the folder.")

# ── Mode 3: Milestone 2 Analysis Pipeline ───────────────────
elif mode == "Milestone 2: Analysis Pipeline":
    st.header("Milestone 2: CV Analysis & Missing Info Detection")
    st.info("Place PDF CVs in the `cvs/` folder, then click Run.")

    cvs_folder = os.path.join(os.path.dirname(__file__), "../cvs")
    output_dir = os.path.join(os.path.dirname(__file__), "../output/milestone2")

    if st.button("Run Milestone 2 Pipeline"):
        with st.spinner("Processing CVs and performing analysis..."):
            run_m2_pipeline(cvs_folder, output_dir)

        st.success(f"Milestone 2 processing completed! CSVs and JSONs saved in {output_dir}")

        # ── Load and display CSVs ───────────────────────────
        csv_files = ["personal_info.csv", "education.csv", "experience.csv", "skills.csv", "missing_info.csv", "draft_emails.csv"]
        for csv_file in csv_files:
            path = os.path.join(output_dir, csv_file)
            if os.path.exists(path):
                st.subheader(csv_file.replace("_", " ").replace(".csv", "").title())
                df = pd.read_csv(path)
                st.dataframe(df, use_container_width=True)
            else:
                st.warning(f"{csv_file} not found.")

        # ── Example Charts ─────────────────────────────────
        # Education degree count
        edu_path = os.path.join(output_dir, "education.csv")
        if os.path.exists(edu_path):
            df_edu = pd.read_csv(edu_path)
            fig = px.histogram(df_edu, x="degree", title="Education Degree Distribution")
            st.plotly_chart(fig, use_container_width=True)

        # Skills frequency
        skills_path = os.path.join(output_dir, "skills.csv")
        if os.path.exists(skills_path):
            df_skills = pd.read_csv(skills_path)
            top_skills = df_skills["skill"].value_counts().reset_index()
            top_skills.columns = ["skill", "count"]
            fig2 = px.bar(top_skills.head(20), x="skill", y="count", title="Top 20 Skills")
            st.plotly_chart(fig2, use_container_width=True)

        # Missing info summary
        missing_path = os.path.join(output_dir, "missing_info.csv")
        if os.path.exists(missing_path):
            df_missing = pd.read_csv(missing_path)
            missing_count = df_missing["missing_fields"].apply(lambda x: len(x.split(",")))
            st.subheader("Missing Information Summary")
            st.write(f"Total CVs with missing info: {len(df_missing)}")
            st.write(f"Average missing fields per CV: {missing_count.mean():.2f}")