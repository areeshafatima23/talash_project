# src/app.py
import streamlit as st
import tempfile, os, json
import pandas as pd
from loader import extract_text_from_pdf, load_cvs_from_folder
from parser import extract_full_profile
from milestone1_pipeline import run_pipeline

st.set_page_config(page_title="TALASH", layout="wide")
st.title("🎓 TALASH — CV Analyzer")
st.caption("Talent Acquisition & Learning Automation for Smart Hiring")

mode = st.sidebar.radio("Mode", ["Upload Single CV", "Process CVs Folder"])

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

        # ── Save JSON to output folder ────────────────────────
        output_dir = os.path.join(os.path.dirname(__file__), "../output")
        os.makedirs(output_dir, exist_ok=True)
        json_filename = uploaded_file.name.replace(".pdf", "_profile.json")
        json_path = os.path.join(output_dir, json_filename)
        with open(json_path, "w") as f:
            json.dump(profile, f, indent=2)

        st.success(f"Done! Profile saved to: output/{json_filename}")

        # ── Personal Info + Summary ───────────────────────────
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Personal Info")
            st.write(f"**Name:** {profile.get('name', 'N/A')}")
            st.write(f"**Email:** {profile.get('email', 'N/A')}")
            st.write(f"**Phone:** {profile.get('phone', 'N/A')}")
            st.write(f"**Address:** {profile.get('address', 'N/A')}")

        with col2:
            st.subheader("Profile Summary")
            st.metric("Degrees", len(profile.get("education", [])))
            st.metric("Jobs", len(profile.get("experience", [])))
            st.metric("Publications", len(profile.get("publications", [])))
            st.metric("Skills", len(profile.get("skills", [])))

        # ── Education ─────────────────────────────────────────
        st.subheader("Education")
        if profile.get("education"):
            st.dataframe(pd.DataFrame(profile["education"]), use_container_width=True)
        else:
            st.info("No education records found.")

        # ── Experience ────────────────────────────────────────
        st.subheader("Experience")
        if profile.get("experience"):
            st.dataframe(pd.DataFrame(profile["experience"]), use_container_width=True)
        else:
            st.info("No experience records found.")

        # ── Skills ────────────────────────────────────────────
        st.subheader("Skills")
        if profile.get("skills"):
            st.write(", ".join(profile["skills"]))
        else:
            st.info("No skills found.")

        # ── Publications ──────────────────────────────────────
        st.subheader("Publications")
        if profile.get("publications"):
            st.dataframe(pd.DataFrame(profile["publications"]), use_container_width=True)
        else:
            st.info("No publications found.")

        # ── Patents ───────────────────────────────────────────
        st.subheader("Patents")
        if profile.get("patents"):
            st.dataframe(pd.DataFrame(profile["patents"]), use_container_width=True)
        else:
            st.info("No patents found.")

        # ── Books ─────────────────────────────────────────────
        st.subheader("Books")
        if profile.get("books"):
            st.dataframe(pd.DataFrame(profile["books"]), use_container_width=True)
        else:
            st.info("No books found.")

        # ── Certifications ────────────────────────────────────
        st.subheader("Certifications")
        if profile.get("certifications"):
            st.write(", ".join(profile["certifications"]))
        else:
            st.info("No certifications found.")

        # ── Download Buttons ──────────────────────────────────
        st.subheader("Downloads")
        col3, col4 = st.columns(2)

        with col3:
            st.download_button(
                label="Download JSON",
                data=json.dumps(profile, indent=2),
                file_name=json_filename,
                mime="application/json"
            )

        with col4:
            # Single row CSV download
            flat = {
                "file_name":      uploaded_file.name,
                "name":           profile.get("name", ""),
                "email":          profile.get("email", ""),
                "phone":          profile.get("phone", ""),
                "address":        profile.get("address", ""),
                "education":      json.dumps(profile.get("education", [])),
                "experience":     json.dumps(profile.get("experience", [])),
                "skills":         ", ".join(profile.get("skills", [])),
                "publications":   json.dumps(profile.get("publications", [])),
                "patents":        json.dumps(profile.get("patents", [])),
                "books":          json.dumps(profile.get("books", [])),
                "certifications": ", ".join(profile.get("certifications", [])),
            }
            csv_data = pd.DataFrame([flat]).to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv_data,
                file_name=uploaded_file.name.replace(".pdf", "_profile.csv"),
                mime="text/csv"
            )

        # ── Full JSON Viewer ──────────────────────────────────
        st.subheader("🔍 Full JSON Output")
        with st.expander("Click to view"):
            st.json(profile)

# ── Mode 2: Folder Processing ─────────────────────────────────
elif mode == "Process CVs Folder":
    st.header("Process All CVs from Folder")
    st.info("Place your PDF CVs in the `cvs/` folder, then click Run.")

    cvs_folder = os.path.join(os.path.dirname(__file__), "../cvs")
    output_csv = os.path.join(os.path.dirname(__file__), "../output/milestone1_output.csv")

    if st.button("Run Pipeline"):
        with st.spinner("Processing all CVs... this may take a minute."):
            rows = run_pipeline(cvs_folder, output_csv)

        if rows:
            st.success(f"Processed {len(rows)} CV(s)!")

            # Save each profile as individual JSON
            output_dir = os.path.join(os.path.dirname(__file__), "../output")
            for row in rows:
                fname = row.get("file_name", "unknown").replace(".pdf", "_profile.json")
                with open(os.path.join(output_dir, fname), "w") as f:
                    json.dump(row, f, indent=2)

            st.info(f"Individual JSON files saved in output/ folder.")

            # Show table
            display_cols = ["file_name", "name", "email", "phone", "skills"]
            df = pd.DataFrame(rows)
            available = [c for c in display_cols if c in df.columns]
            st.dataframe(df[available], use_container_width=True)

            # Download CSV
            with open(output_csv, "rb") as f:
                st.download_button(
                    "Download Full CSV",
                    f,
                    file_name="milestone1_output.csv",
                    mime="text/csv"
                )
        else:
            st.warning("No CVs found in the cvs/ folder.")