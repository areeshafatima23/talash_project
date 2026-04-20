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

# ── Mode 1 ──────────────────────────────────
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
            st.dataframe(pd.DataFrame(profile["education"]), width="stretch")

        st.subheader("Experience")
        if profile.get("experience"):
            st.dataframe(pd.DataFrame(profile["experience"]), width="stretch")

        st.subheader("Download JSON / CSV")

        json_filename = uploaded_file.name.replace(".pdf", "_profile.json")
        st.download_button(
            "Download JSON",
            json.dumps(profile, indent=2),
            json_filename,
            mime="application/json"
        )

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

        st.download_button(
            "Download CSV",
            flat_csv,
            uploaded_file.name.replace(".pdf", "_profile.csv"),
            "text/csv"
        )

# ── Mode 2 (Milestone 1) ─────────────────────────────────
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
            df = pd.DataFrame(rows)

            if not df.empty:
                st.dataframe(df[["file_name", "name", "email", "phone", "skills"]], width="stretch")

            with open(output_csv, "rb") as f:
                st.download_button("Download Full CSV", f, "milestone1_output.csv", "text/csv")
        else:
            st.warning("No CVs found in the folder.")

# ── Mode 3 (Milestone 2) ─────────────────────────────────
elif mode == "Milestone 2: Analysis Pipeline":
    st.header("Milestone 2: CV Analysis & Missing Info Detection")
    st.info("Place PDF CVs in the `cvs/` folder, then click Run.")

    cvs_folder = os.path.join(os.path.dirname(__file__), "../cvs")
    output_dir = os.path.join(os.path.dirname(__file__), "../output/milestone2")

    if st.button("Run Milestone 2 Pipeline"):
        with st.spinner("Processing CVs and performing analysis..."):
            run_m2_pipeline(cvs_folder, output_dir)

        st.success(f"Milestone 2 processing completed! Saved in {output_dir}")

        def safe_read(path):
            if os.path.exists(path) and os.path.getsize(path) > 0:
                try:
                    return pd.read_csv(path)
                except:
                    return pd.DataFrame()
            return pd.DataFrame()

        csv_files = [
            "personal_info.csv",
            "education.csv",
            "experience.csv",
            "skills.csv",
            "missing_info.csv",
            "draft_emails.csv"
        ]

        for csv_file in csv_files:
            path = os.path.join(output_dir, csv_file)
            df = safe_read(path)

            st.subheader(csv_file.replace("_", " ").replace(".csv", "").title())

            if not df.empty:
                st.dataframe(df, width="stretch")
            else:
                st.warning(f"No data in {csv_file}")

        # ── EDUCATION VISUALS ──
        edu_path = os.path.join(output_dir, "education.csv")
        edu_df = safe_read(edu_path)

        if not edu_df.empty:

            degree_counts = edu_df["degree"].value_counts().reset_index()
            degree_counts.columns = ["degree", "count"]

            fig = px.histogram(edu_df, x="degree", title="Education Degree Distribution")
            st.plotly_chart(fig, width="stretch")

            fig_pie = px.pie(
                degree_counts,
                names="degree",
                values="count",
                title="Education Degree Share"
            )
            st.plotly_chart(fig_pie, width="stretch")

        # ── SKILLS VISUALS ──
        skills_path = os.path.join(output_dir, "skills.csv")
        skills_df = safe_read(skills_path)

        if not skills_df.empty:
            top_skills = skills_df["skill"].value_counts().reset_index()
            top_skills.columns = ["skill", "count"]

            fig2 = px.bar(top_skills.head(20), x="skill", y="count", title="Top 20 Skills")
            st.plotly_chart(fig2, width="stretch")

        # ── MISSING INFO VISUALS ──
        missing_path = os.path.join(output_dir, "missing_info.csv")
        missing_df = safe_read(missing_path)

        if not missing_df.empty:
            missing_df["missing_count"] = missing_df["missing_fields"].apply(
                lambda x: len(str(x).split(","))
            )

            st.subheader("Missing Information Summary")
            st.write(f"Total CVs with missing info: {len(missing_df)}")
            st.write(f"Average missing fields per CV: {missing_df['missing_count'].mean():.2f}")

            fig_pie2 = px.pie(
                missing_df,
                names="file_name",
                values="missing_count",
                title="Missing Information Distribution per CV"
            )
            st.plotly_chart(fig_pie2, width="stretch")