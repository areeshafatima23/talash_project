# # src/app.py
# import streamlit as st
# import tempfile, os, json
# import pandas as pd
# import plotly.express as px

# from loader import extract_text_from_pdf, load_cvs_from_folder
# from parser import extract_full_profile
# from milestone1_pipeline import run_pipeline as run_m1_pipeline
# from milestone2_pipeline import run_pipeline as run_m2_pipeline
# from milestone3_pipeline import run_pipeline as run_m3_pipeline

# st.set_page_config(page_title="TALASH", layout="wide")
# st.title("TALASH")
# st.caption("Talent Acquisition & Learning Automation for Smart Hiring")

# mode = st.sidebar.radio(
#     "Mode", 
#     ["Upload Single CV", "Process CVs Folder (Milestone 1)", "Milestone 2: Analysis Pipeline", "Milestone 3: Comprehensive Analysis"]
# )

# # Mode 1
# if mode == "Upload Single CV":
#     st.header("Upload a CV")
#     uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

#     if uploaded_file:
#         with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
#             tmp.write(uploaded_file.read())
#             tmp_path = tmp.name

#         with st.spinner("Reading PDF..."):
#             text = extract_text_from_pdf(tmp_path)
#         os.unlink(tmp_path)

#         with st.spinner("Analyzing CV with AI..."):
#             profile = extract_full_profile(text)

#         st.subheader("Personal Info")
#         st.write(f"**Name:** {profile.get('name', 'N/A')}")
#         st.write(f"**Email:** {profile.get('email', 'N/A')}")
#         st.write(f"**Phone:** {profile.get('phone', 'N/A')}")
#         st.write(f"**Address:** {profile.get('address', 'N/A')}")

#         st.subheader("Skills")
#         st.write(", ".join(profile.get("skills", [])) or "No skills found")

#         st.subheader("Education")
#         if profile.get("education"):
#             st.dataframe(pd.DataFrame(profile["education"]), width="stretch")

#         st.subheader("Experience")
#         if profile.get("experience"):
#             st.dataframe(pd.DataFrame(profile["experience"]), width="stretch")

#         st.subheader("Download JSON / CSV")

#         json_filename = uploaded_file.name.replace(".pdf", "_profile.json")
#         st.download_button(
#             "Download JSON",
#             json.dumps(profile, indent=2),
#             json_filename,
#             mime="application/json"
#         )

#         flat_csv = pd.DataFrame([{
#             "file_name": uploaded_file.name,
#             "name": profile.get("name", ""),
#             "email": profile.get("email", ""),
#             "phone": profile.get("phone", ""),
#             "address": profile.get("address", ""),
#             "education": json.dumps(profile.get("education", [])),
#             "experience": json.dumps(profile.get("experience", [])),
#             "skills": ", ".join(profile.get("skills", []))
#         }]).to_csv(index=False)

#         st.download_button(
#             "Download CSV",
#             flat_csv,
#             uploaded_file.name.replace(".pdf", "_profile.csv"),
#             "text/csv"
#         )

# # Mode 2 (Milestone 1) 
# elif mode == "Process CVs Folder (Milestone 1)":
#     st.header("Process All CVs from Folder (Milestone 1)")
#     st.info("Place PDF CVs in the `cvs/` folder, then click Run.")

#     cvs_folder = os.path.join(os.path.dirname(__file__), "../cvs")
#     output_csv = os.path.join(os.path.dirname(__file__), "../output/milestone1_output.csv")

#     if st.button("Run Milestone 1 Pipeline"):
#         with st.spinner("Processing CVs..."):
#             rows = run_m1_pipeline(cvs_folder, output_csv)

#         if rows:
#             st.success(f"Processed {len(rows)} CV(s)!")
#             df = pd.DataFrame(rows)

#             if not df.empty:
#                 st.dataframe(df[["file_name", "name", "email", "phone", "skills"]], width="stretch")

#             with open(output_csv, "rb") as f:
#                 st.download_button("Download Full CSV", f, "milestone1_output.csv", "text/csv")
#         else:
#             st.warning("No CVs found in the folder.")

# # Mode 3 (Milestone 2) 
# elif mode == "Milestone 2: Analysis Pipeline":
#     st.header("Milestone 2: CV Analysis & Missing Info Detection")
#     st.info("Place PDF CVs in the `cvs/` folder, then click Run.")

#     cvs_folder = os.path.join(os.path.dirname(__file__), "../cvs")
#     output_dir = os.path.join(os.path.dirname(__file__), "../output/milestone2")

#     if st.button("Run Milestone 2 Pipeline"):
#         with st.spinner("Processing CVs and performing analysis..."):
#             run_m2_pipeline(cvs_folder, output_dir)

#         st.success(f"Milestone 2 processing completed! Saved in {output_dir}")

#         def safe_read(path):
#             if os.path.exists(path) and os.path.getsize(path) > 0:
#                 try:
#                     return pd.read_csv(path)
#                 except:
#                     return pd.DataFrame()
#             return pd.DataFrame()

#         csv_files = [
#             "personal_info.csv",
#             "education.csv",
#             "experience.csv",
#             "skills.csv",
#             "publications.csv",
#             "missing_info.csv",
#             "draft_emails.csv"
#         ]

#         for csv_file in csv_files:
#             path = os.path.join(output_dir, csv_file)
#             df = safe_read(path)

#             st.subheader(csv_file.replace("_", " ").replace(".csv", "").title())

#             if not df.empty:
#                 st.dataframe(df, width="stretch")
#             else:
#                 st.warning(f"No data in {csv_file}")

#         # ── EDUCATION VISUALS ──
#         edu_path = os.path.join(output_dir, "education.csv")
#         edu_df = safe_read(edu_path)

#         if not edu_df.empty:

#             degree_counts = edu_df["degree"].value_counts().reset_index()
#             degree_counts.columns = ["degree", "count"]

#             fig = px.histogram(edu_df, x="degree", title="Education Degree Distribution")
#             st.plotly_chart(fig, width="stretch")

#             fig_pie = px.pie(
#                 degree_counts,
#                 names="degree",
#                 values="count",
#                 title="Education Degree Share"
#             )
#             st.plotly_chart(fig_pie, width="stretch")

#         # ── SKILLS VISUALS ──
#         skills_path = os.path.join(output_dir, "skills.csv")
#         skills_df = safe_read(skills_path)

#         if not skills_df.empty:
#             top_skills = skills_df["skill"].value_counts().reset_index()
#             top_skills.columns = ["skill", "count"]

#             fig2 = px.bar(top_skills.head(20), x="skill", y="count", title="Top 20 Skills")
#             st.plotly_chart(fig2, width="stretch")
#         # ── PUBLICATIONS VISUALS ──
#         pub_path = os.path.join(output_dir, "publications.csv")
#         pub_df = safe_read(pub_path)

#         if not pub_df.empty:
#             st.subheader("Publications Analysis")

#             pub_counts = pub_df["file_name"].value_counts().reset_index()
#             pub_counts.columns = ["candidate", "num_publications"]

#             fig_pub = px.bar(
#                 pub_counts,
#                 x="candidate",
#                 y="num_publications",
#                 title="Publications per Candidate"
#                 )
#             st.plotly_chart(fig_pub, width="stretch")

#         # ── MISSING INFO VISUALS ──
#         missing_path = os.path.join(output_dir, "missing_info.csv")
#         missing_df = safe_read(missing_path)

#         if not missing_df.empty:
#             missing_df["missing_count"] = missing_df["missing_fields"].apply(
#                 lambda x: len(str(x).split(","))
#             )

#             st.subheader("Missing Information Summary")
#             st.write(f"Total CVs with missing info: {len(missing_df)}")
#             st.write(f"Average missing fields per CV: {missing_df['missing_count'].mean():.2f}")

#             fig_pie2 = px.pie(
#                 missing_df,
#                 names="file_name",
#                 values="missing_count",
#                 title="Missing Information Distribution per CV"
#             )
#             st.plotly_chart(fig_pie2, width="stretch")

# # Mode 4 (Milestone 3)
# elif mode == "Milestone 3: Educational Analysis" or mode == "Milestone 3: Comprehensive Analysis":
#     st.header("Milestone 3: Educational & Research Profile Analysis")
#     st.info("Place PDF CVs in the `cvs/` folder, then click Run.")

#     cvs_folder = os.path.join(os.path.dirname(__file__), "../cvs")
#     output_dir = os.path.join(os.path.dirname(__file__), "../output/milestone3")

#     if st.button("Run Milestone 3 Pipeline"):
#         with st.spinner("Analyzing Profiles..."):
#             analysis_results, global_edu, global_journals, global_confs = run_m3_pipeline(cvs_folder, output_dir)
            
#         st.success(f"Milestone 3 processing completed! Saved in {output_dir}")
        
#         tab1, tab2, tab3 = st.tabs(["Overall Analysis", "Educational Records", "Research Records"])
        
#         with tab1:
#             st.subheader("Overall Candidates Analysis")
#             if analysis_results:
#                 st.dataframe(pd.DataFrame(analysis_results), width="stretch")
        
#         with tab2:
#             st.subheader("Educational Records (Normalized & Ranked)")
#             if global_edu:
#                 st.dataframe(pd.DataFrame(global_edu), width="stretch")
                
#                 # Additional visual
#                 df_edu = pd.DataFrame(global_edu)
#                 if 'marks_normalized_percent' in df_edu.columns and not df_edu['marks_normalized_percent'].isnull().all():
#                     fig_perf = px.box(df_edu, x="level", y="marks_normalized_percent", title="Academic Performance Distribution by Level")
#                     st.plotly_chart(fig_perf, width="stretch")
        
#         with tab3:
#             st.subheader("Journal Publications Analysis")
#             if global_journals:
#                 st.dataframe(pd.DataFrame(global_journals), width="stretch")
#             else:
#                 st.write("No journal publications found.")
                
#             st.subheader("Conference Publications Analysis")
#             if global_confs:
#                 st.dataframe(pd.DataFrame(global_confs), width="stretch")
#             else:
#                 st.write("No conference publications found.")
# src/app.py
# ─────────────────────────────────────────────────────────────────────────────
#  TALASH  –  Streamlit Web Application
#  Updated for Milestone 3 (Member A additions):
#    - Milestone 3 mode now shows 6 tabs instead of 3
#    - New tabs: Topic Variability, Co-Author Analysis, Books & Patents
#    - All charts use Plotly for consistency
# ─────────────────────────────────────────────────────────────────────────────

import streamlit as st
import tempfile, os, json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from loader import extract_text_from_pdf, load_cvs_from_folder
from parser import extract_full_profile
from milestone1_pipeline import run_pipeline as run_m1_pipeline
from milestone2_pipeline import run_pipeline as run_m2_pipeline
from milestone3_pipeline import run_pipeline as run_m3_pipeline

st.set_page_config(page_title="TALASH", layout="wide")
st.title("TALASH")
st.caption("Talent Acquisition & Learning Automation for Smart Hiring")

mode = st.sidebar.radio(
    "Mode",
    [
        "Upload Single CV",
        "Process CVs Folder (Milestone 1)",
        "Milestone 2: Analysis Pipeline",
        "Milestone 3: Comprehensive Analysis",
    ],
)


# ─────────────────────────────────────────────────────────────────────────────
#  MODE 1 — Single CV Upload
# ─────────────────────────────────────────────────────────────────────────────
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

        st.subheader("Books")
        if profile.get("books"):
            st.dataframe(pd.DataFrame(profile["books"]), use_container_width=True)
        else:
            st.write("No books found.")

        st.subheader("Patents")
        if profile.get("patents"):
            st.dataframe(pd.DataFrame(profile["patents"]), use_container_width=True)
        else:
            st.write("No patents found.")

        st.subheader("Download JSON / CSV")
        json_filename = uploaded_file.name.replace(".pdf", "_profile.json")
        st.download_button(
            "Download JSON",
            json.dumps(profile, indent=2),
            json_filename,
            mime="application/json",
        )

        flat_csv = pd.DataFrame([{
            "file_name": uploaded_file.name,
            "name":      profile.get("name", ""),
            "email":     profile.get("email", ""),
            "phone":     profile.get("phone", ""),
            "address":   profile.get("address", ""),
            "education": json.dumps(profile.get("education", [])),
            "experience":json.dumps(profile.get("experience", [])),
            "skills":    ", ".join(profile.get("skills", [])),
            "books":     json.dumps(profile.get("books", [])),
            "patents":   json.dumps(profile.get("patents", [])),
        }]).to_csv(index=False)

        st.download_button(
            "Download CSV",
            flat_csv,
            uploaded_file.name.replace(".pdf", "_profile.csv"),
            "text/csv",
        )


# ─────────────────────────────────────────────────────────────────────────────
#  MODE 2 — Milestone 1 Folder Pipeline
# ─────────────────────────────────────────────────────────────────────────────
elif mode == "Process CVs Folder (Milestone 1)":
    st.header("Process All CVs from Folder (Milestone 1)")
    st.info("Place PDF CVs in the `cvs/` folder, then click Run.")

    cvs_folder  = os.path.join(os.path.dirname(__file__), "../cvs")
    output_csv  = os.path.join(os.path.dirname(__file__), "../output/milestone1_output.csv")

    if st.button("Run Milestone 1 Pipeline"):
        with st.spinner("Processing CVs..."):
            rows = run_m1_pipeline(cvs_folder, output_csv)

        if rows:
            st.success(f"Processed {len(rows)} CV(s)!")
            df = pd.DataFrame(rows)
            if not df.empty:
                st.dataframe(df[["file_name", "name", "email", "phone", "skills"]], use_container_width=True)
            with open(output_csv, "rb") as f:
                st.download_button("Download Full CSV", f, "milestone1_output.csv", "text/csv")
        else:
            st.warning("No CVs found in the folder.")


# ─────────────────────────────────────────────────────────────────────────────
#  MODE 3 — Milestone 2 Analysis Pipeline
# ─────────────────────────────────────────────────────────────────────────────
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

        for csv_file in ["personal_info.csv", "education.csv", "experience.csv",
                         "skills.csv", "publications.csv", "missing_info.csv", "draft_emails.csv"]:
            path = os.path.join(output_dir, csv_file)
            df   = safe_read(path)
            st.subheader(csv_file.replace("_", " ").replace(".csv", "").title())
            if not df.empty:
                st.dataframe(df, use_container_width=True)
            else:
                st.warning(f"No data in {csv_file}")

        # Visuals
        edu_df = safe_read(os.path.join(output_dir, "education.csv"))
        if not edu_df.empty:
            fig = px.histogram(edu_df, x="degree", title="Education Degree Distribution")
            st.plotly_chart(fig, use_container_width=True)
            degree_counts = edu_df["degree"].value_counts().reset_index()
            degree_counts.columns = ["degree", "count"]
            st.plotly_chart(px.pie(degree_counts, names="degree", values="count",
                                   title="Degree Share"), use_container_width=True)

        skills_df = safe_read(os.path.join(output_dir, "skills.csv"))
        if not skills_df.empty:
            top = skills_df["skill"].value_counts().reset_index()
            top.columns = ["skill", "count"]
            st.plotly_chart(px.bar(top.head(20), x="skill", y="count", title="Top 20 Skills"),
                            use_container_width=True)

        pub_df = safe_read(os.path.join(output_dir, "publications.csv"))
        if not pub_df.empty:
            pub_counts = pub_df["file_name"].value_counts().reset_index()
            pub_counts.columns = ["candidate", "num_publications"]
            st.plotly_chart(px.bar(pub_counts, x="candidate", y="num_publications",
                                   title="Publications per Candidate"), use_container_width=True)

        missing_df = safe_read(os.path.join(output_dir, "missing_info.csv"))
        if not missing_df.empty:
            missing_df["missing_count"] = missing_df["missing_fields"].apply(
                lambda x: len(str(x).split(",")))
            st.subheader("Missing Information Summary")
            st.write(f"Total CVs with missing info: {len(missing_df)}")
            st.plotly_chart(px.pie(missing_df, names="file_name", values="missing_count",
                                   title="Missing Info per CV"), use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
#  MODE 4 — Milestone 3 Comprehensive Analysis
# ─────────────────────────────────────────────────────────────────────────────
elif mode == "Milestone 3: Comprehensive Analysis":
    st.header("Milestone 3: Educational, Research & Innovation Profile Analysis")
    st.info("Place PDF CVs in the `cvs/` folder, then click Run.")

    cvs_folder = os.path.join(os.path.dirname(__file__), "../cvs")
    output_dir = os.path.join(os.path.dirname(__file__), "../output/milestone3")

    if st.button("Run Milestone 3 Pipeline"):
        with st.spinner("Running full analysis — this may take a few minutes per CV..."):
            (analysis_results, global_edu, global_journals, global_confs,
             global_topic_rows, global_coauthor_rows,
             global_book_rows, global_patent_rows) = run_m3_pipeline(cvs_folder, output_dir)

        st.success("Milestone 3 analysis complete!")

        # ── Helper ───────────────────────────────────────────────────────────
        def safe_df(data):
            return pd.DataFrame(data) if data else pd.DataFrame()

        ar_df  = safe_df(analysis_results)
        edu_df = safe_df(global_edu)
        j_df   = safe_df(global_journals)
        c_df   = safe_df(global_confs)
        t_df   = safe_df(global_topic_rows)
        ca_df  = safe_df(global_coauthor_rows)
        bk_df  = safe_df(global_book_rows)
        pt_df  = safe_df(global_patent_rows)

        # ── 6 Tabs ────────────────────────────────────────────────────────────
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "📊 Overall Analysis",
            "🎓 Education",
            "📄 Research (Journals & Conf)",
            "🔬 Topic Variability",     # [MEMBER A]
            "🤝 Co-Author Analysis",    # [MEMBER A]
            "📚 Books & Patents",        # [MEMBER A]
        ])

        # ── TAB 1: Overall ────────────────────────────────────────────────────
        with tab1:
            st.subheader("Candidate Summary Table")
            if not ar_df.empty:
                display_cols = [c for c in [
                    "candidate_name", "highest_qualification", "academic_progression",
                    "total_publications", "dominant_research_topic", "research_variability_label",
                    "total_unique_coauthors", "total_books", "total_patents",
                ] if c in ar_df.columns]
                st.dataframe(ar_df[display_cols], use_container_width=True)

                # Comparison bar chart — publications per candidate
                if "total_publications" in ar_df.columns and "candidate_name" in ar_df.columns:
                    fig = px.bar(ar_df, x="candidate_name", y="total_publications",
                                 title="Total Publications per Candidate",
                                 labels={"candidate_name": "Candidate", "total_publications": "Publications"},
                                 color="candidate_name")
                    st.plotly_chart(fig, use_container_width=True)

                # Books & Patents comparison
                if "total_books" in ar_df.columns and "total_patents" in ar_df.columns:
                    fig2 = go.Figure()
                    fig2.add_trace(go.Bar(name="Books",   x=ar_df["candidate_name"], y=ar_df["total_books"]))
                    fig2.add_trace(go.Bar(name="Patents", x=ar_df["candidate_name"], y=ar_df["total_patents"]))
                    fig2.update_layout(barmode="group", title="Books & Patents per Candidate",
                                       xaxis_title="Candidate", yaxis_title="Count",
                                       yaxis=dict(range=[0, max(ar_df["total_books"].max(), ar_df["total_patents"].max(), 1) + 1]))
                    st.plotly_chart(fig2, use_container_width=True)

                st.subheader("Full Analysis Table")
                st.dataframe(ar_df, use_container_width=True)
            else:
                st.warning("No analysis results found.")

        # ── TAB 2: Education ──────────────────────────────────────────────────
        with tab2:
            st.subheader("Educational Records (Normalized & Ranked)")
            if not edu_df.empty:
                st.dataframe(edu_df, use_container_width=True)
                if "marks_normalized_percent" in edu_df.columns and not edu_df["marks_normalized_percent"].isnull().all():
                    fig = px.box(edu_df, x="level", y="marks_normalized_percent",
                                 title="Academic Performance Distribution by Level",
                                 labels={"level": "Education Level", "marks_normalized_percent": "Score (%)"})
                    st.plotly_chart(fig, use_container_width=True)
                if "ranking" in edu_df.columns:
                    rank_counts = edu_df["ranking"].value_counts().reset_index()
                    rank_counts.columns = ["ranking", "count"]
                    st.plotly_chart(px.bar(rank_counts, x="ranking", y="count",
                                          title="Institution Ranking Distribution"),
                                   use_container_width=True)
            else:
                st.write("No education records found.")

            # Gap interpretation from overall analysis
            if not ar_df.empty and "detected_gaps" in ar_df.columns:
                st.subheader("Educational Gap Analysis")
                for _, row in ar_df.iterrows():
                    name = row.get("candidate_name", row.get("file_name", "Candidate"))
                    gaps = row.get("detected_gaps", "")
                    if gaps:
                        st.warning(f"**{name}:** {gaps}")
                    else:
                        st.success(f"**{name}:** No significant educational gaps detected.")

        # ── TAB 3: Research (Journals & Conferences) ──────────────────────────
        with tab3:
            st.subheader("Journal Publications Analysis")
            if not j_df.empty:
                st.dataframe(j_df, use_container_width=True)
                if "quartile" in j_df.columns:
                    q_counts = j_df["quartile"].value_counts().reset_index()
                    q_counts.columns = ["quartile", "count"]
                    st.plotly_chart(px.pie(q_counts, names="quartile", values="count",
                                           title="Journal Quartile Distribution"),
                                   use_container_width=True)
            else:
                st.write("No journal publications found.")

            st.subheader("Conference Publications Analysis")
            if not c_df.empty:
                st.dataframe(c_df, use_container_width=True)
                if "a_star_status" in c_df.columns:
                    astar_counts = c_df["a_star_status"].value_counts().reset_index()
                    astar_counts.columns = ["is_a_star", "count"]
                    astar_counts["label"] = astar_counts["is_a_star"].map({True: "A* Conference", False: "Other"})
                    st.plotly_chart(px.pie(astar_counts, names="label", values="count",
                                           title="Conference Quality (A* vs Others)"),
                                   use_container_width=True)
            else:
                st.write("No conference publications found.")

        # ── TAB 4: Topic Variability  [MEMBER A] ─────────────────────────────
        with tab4:
            st.subheader("Research Topic Variability Analysis")
            st.write(
                "This module classifies each publication into research themes and measures "
                "how focused or broad the candidate's research is."
            )

            if not t_df.empty:
                st.subheader("Per-Publication Topic Classification")
                st.dataframe(t_df, use_container_width=True)

                # Bar chart: theme distribution across all candidates
                theme_counts = t_df["primary_theme"].value_counts().reset_index()
                theme_counts.columns = ["theme", "count"]
                fig_theme = px.bar(
                    theme_counts, x="theme", y="count",
                    title="Research Theme Distribution (All Candidates)",
                    labels={"theme": "Research Theme", "count": "# Publications"},
                    color="theme",
                )
                fig_theme.update_layout(xaxis_tickangle=-30)
                st.plotly_chart(fig_theme, use_container_width=True)

                # Per-candidate breakdown
                if "candidate" in t_df.columns:
                    candidates = t_df["candidate"].unique().tolist()
                    selected   = st.selectbox("Select candidate for detailed topic breakdown:", candidates)
                    cand_df    = t_df[t_df["candidate"] == selected]

                    theme_per_cand = cand_df["primary_theme"].value_counts().reset_index()
                    theme_per_cand.columns = ["theme", "count"]

                    col1, col2 = st.columns(2)
                    with col1:
                        st.plotly_chart(px.pie(theme_per_cand, names="theme", values="count",
                                               title=f"Topic Distribution — {selected}"),
                                       use_container_width=True)
                    with col2:
                        st.plotly_chart(px.bar(theme_per_cand, x="theme", y="count",
                                               title=f"Topic Counts — {selected}",
                                               color="theme"),
                                       use_container_width=True)

                # Topic trend over time
                if "year" in t_df.columns:
                    trend_df = t_df[t_df["year"].astype(str).str.isnumeric()].copy()
                    if not trend_df.empty:
                        trend_df["year"] = trend_df["year"].astype(int)
                        trend_agg = trend_df.groupby(["year", "primary_theme"]).size().reset_index(name="count")
                        fig_trend = px.line(trend_agg, x="year", y="count", color="primary_theme",
                                            title="Research Topic Trend Over Time",
                                            labels={"year": "Year", "count": "Publications", "primary_theme": "Theme"})
                        st.plotly_chart(fig_trend, use_container_width=True)

                # Diversity scores from overall analysis
                if not ar_df.empty and "research_diversity_score" in ar_df.columns:
                    st.subheader("Research Diversity Scores per Candidate")
                    div_df = ar_df[["candidate_name", "research_diversity_score",
                                   "research_variability_label", "dominant_research_topic",
                                   "topic_interpretation"]].copy()
                    st.dataframe(div_df, use_container_width=True)

                    fig_div = px.bar(div_df, x="candidate_name", y="research_diversity_score",
                                     color="research_variability_label",
                                     title="Research Diversity Score per Candidate (0=Specialist, 1=Interdisciplinary)",
                                     labels={"candidate_name": "Candidate",
                                             "research_diversity_score": "Diversity Score (0–1)"})
                    st.plotly_chart(fig_div, use_container_width=True)
            else:
                st.write("No publication data available for topic analysis.")

        # ── TAB 5: Co-Author Analysis  [MEMBER A] ─────────────────────────────
        with tab5:
            st.subheader("Co-Author Collaboration Analysis")
            st.write(
                "This module analyzes co-authorship patterns including recurring collaborators, "
                "team sizes, and collaboration diversity."
            )

            if not ca_df.empty:
                st.subheader("Per-Paper Co-Author Details")
                st.dataframe(ca_df, use_container_width=True)

                # Team size distribution
                if "team_size" in ca_df.columns:
                    fig_team = px.histogram(ca_df, x="team_size", nbins=10,
                                            title="Distribution of Team Sizes per Paper",
                                            labels={"team_size": "Authors per Paper", "count": "# Papers"})
                    st.plotly_chart(fig_team, use_container_width=True)

                # Avg team size per candidate
                if "candidate" in ca_df.columns and "team_size" in ca_df.columns:
                    avg_team = ca_df.groupby("candidate")["team_size"].mean().reset_index()
                    avg_team.columns = ["candidate", "avg_team_size"]
                    st.plotly_chart(px.bar(avg_team, x="candidate", y="avg_team_size",
                                           title="Average Team Size per Candidate",
                                           labels={"avg_team_size": "Avg Authors per Paper"}),
                                   use_container_width=True)

            # Co-author summary from overall results
            if not ar_df.empty and "total_unique_coauthors" in ar_df.columns:
                st.subheader("Co-Author Summary per Candidate")
                coauth_summary = ar_df[["candidate_name", "total_unique_coauthors",
                                        "avg_authors_per_paper", "solo_papers",
                                        "frequent_collaborators",
                                        "coauthor_interpretation"]].copy()
                st.dataframe(coauth_summary, use_container_width=True)

                fig_coauth = px.bar(coauth_summary, x="candidate_name", y="total_unique_coauthors",
                                    title="Unique Co-Authors per Candidate",
                                    labels={"candidate_name": "Candidate",
                                            "total_unique_coauthors": "Unique Co-Authors"},
                                    color="candidate_name")
                st.plotly_chart(fig_coauth, use_container_width=True)

                # Collaboration diversity
                if "avg_authors_per_paper" in coauth_summary.columns:
                    fig_avg = px.bar(coauth_summary, x="candidate_name", y="avg_authors_per_paper",
                                     title="Average Co-Authors per Paper",
                                     color="candidate_name")
                    st.plotly_chart(fig_avg, use_container_width=True)
            else:
                st.write("No co-author data available.")

        # ── TAB 6: Books & Patents  [MEMBER A] ────────────────────────────────
        with tab6:
            st.subheader("Books Authored / Co-Authored")
            if not bk_df.empty:
                st.dataframe(bk_df, use_container_width=True)

                # Authorship role distribution
                if "authorship_role" in bk_df.columns:
                    role_counts = bk_df["authorship_role"].value_counts().reset_index()
                    role_counts.columns = ["role", "count"]
                    st.plotly_chart(px.pie(role_counts, names="role", values="count",
                                           title="Book Authorship Roles"),
                                   use_container_width=True)

                # Publisher credibility
                if "publisher_credibility" in bk_df.columns:
                    cred_counts = bk_df["publisher_credibility"].value_counts().reset_index()
                    cred_counts.columns = ["credibility", "count"]
                    st.plotly_chart(px.pie(cred_counts, names="credibility", values="count",
                                           title="Publisher Credibility Distribution"),
                                   use_container_width=True)

                # Books summary per candidate
                if "candidate" in bk_df.columns:
                    bk_per_cand = bk_df.groupby("candidate").size().reset_index(name="book_count")
                    st.plotly_chart(px.bar(bk_per_cand, x="candidate", y="book_count",
                                           title="Books per Candidate", color="candidate"),
                                   use_container_width=True)

                # Show interpretation texts
                if not ar_df.empty and "books_interpretation" in ar_df.columns:
                    st.subheader("Books Interpretation")
                    for _, row in ar_df.iterrows():
                        st.info(f"**{row.get('candidate_name', 'Candidate')}:** {row.get('books_interpretation', '')}")
            else:
                st.write("No books found in the processed CVs.")

            st.markdown("---")
            st.subheader("Patents")

            if not pt_df.empty:
                st.dataframe(pt_df, use_container_width=True)

                # Inventor role distribution
                if "inventor_role" in pt_df.columns:
                    inv_counts = pt_df["inventor_role"].value_counts().reset_index()
                    inv_counts.columns = ["role", "count"]
                    st.plotly_chart(px.pie(inv_counts, names="role", values="count",
                                           title="Patent Inventor Roles"),
                                   use_container_width=True)

                # Country distribution
                if "country" in pt_df.columns:
                    country_counts = pt_df[pt_df["country"] != "Not Stated"]["country"].value_counts().reset_index()
                    if not country_counts.empty:
                        country_counts.columns = ["country", "count"]
                        st.plotly_chart(px.bar(country_counts, x="country", y="count",
                                               title="Patents by Country of Filing",
                                               color="country"),
                                       use_container_width=True)

                # Patents per candidate
                if "candidate" in pt_df.columns:
                    pt_per_cand = pt_df.groupby("candidate").size().reset_index(name="patent_count")
                    st.plotly_chart(px.bar(pt_per_cand, x="candidate", y="patent_count",
                                           title="Patents per Candidate", color="candidate"),
                                   use_container_width=True)

                # Verification links as clickable table
                if "verification_url" in pt_df.columns:
                    st.subheader("Patent Verification Links")
                    link_df = pt_df[["candidate", "patent_number", "title", "verification_url"]].copy()
                    st.dataframe(link_df, use_container_width=True)

                # Show interpretation texts
                if not ar_df.empty and "patents_interpretation" in ar_df.columns:
                    st.subheader("Patents Interpretation")
                    for _, row in ar_df.iterrows():
                        st.info(f"**{row.get('candidate_name', 'Candidate')}:** {row.get('patents_interpretation', '')}")
            else:
                st.write("No patents found in the processed CVs.")